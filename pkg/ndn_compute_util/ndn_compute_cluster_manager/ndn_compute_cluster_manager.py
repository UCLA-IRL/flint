import docker
import os
import subprocess


nfd_image_tag = "ndn-compute/nfd:latest"
driver_image_tag = "ndn-compute/driver:latest"
worker_image_tag = "ndn-compute/worker:latest"


# TODO: show usage in getting-started.ipynb
def _image_exists(client, tag: str) -> bool:
    return any(img.tags and tag in img.tags for img in client.images.list())


def buildnfd_ndn_compute_cluster(client=None):
    """
    Building NFD takes forever, so we separate it out.

    We aren't using the Python Docker SDK because it doesn't support the Dockerfile syntax for NFD:
    https://github.com/docker/docker-py/issues/2230
    """
    print(f"Building NFD image: {nfd_image_tag}")
    command = f"docker build -t {nfd_image_tag} ./cluster/nfd-node"

    result = subprocess.run(command.split(" "), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if result.returncode != 0:
        raise RuntimeError(f"NFD docker build failed, hint: try manually running to see stdout: {command}")

def build_ndn_compute_cluster(client=None):
    # Initialize Docker client if not provided
    if client is None:
        client = docker.from_env()

    print("Building images...")

    # Build driver image
    print(f"Building driver image: {driver_image_tag}")
    driver_image, _ = client.images.build(
        path=".",
        dockerfile="./cluster/driver/Dockerfile",
        tag=driver_image_tag,
        rm=True
    )

    # Build worker image (only once, as it will be reused)
    print(f"Building worker image: {worker_image_tag}")
    worker_image, _ = client.images.build(
        path=".",
        dockerfile="./cluster/worker/Dockerfile",
        tag=worker_image_tag,
        rm=True
    )


def run_ndn_compute_cluster(num_workers=2, rebuild=False, client=None):
    """
    Deploy the ndn-compute cluster using the Docker SDK

    Args:
        num_workers: Number of worker containers to create
        client: Optional docker client instance. If None, a new client will be created.
    """
    # Initialize Docker client if not provided
    if client is None:
        client = docker.from_env()

    if not _image_exists(client, nfd_image_tag):
        buildnfd_ndn_compute_cluster(client)

    if not _image_exists(client, driver_image_tag) or not _image_exists(client, worker_image_tag) or rebuild:
        build_ndn_compute_cluster(client)

    # Create network with specific subnet
    print("Creating network...")
    network_name = "ndn_compute_net"
    try:
        network = client.networks.get(network_name)
        print(f"Network {network_name} already exists")
    except docker.errors.NotFound:
        ipam_pool = docker.types.IPAMPool(
            subnet='192.168.1.0/24'
        )
        ipam_config = docker.types.IPAMConfig(
            pool_configs=[ipam_pool]
        )
        network = client.networks.create(
            network_name,
            driver='bridge',
            ipam=ipam_config
        )
        print(f"Network {network_name} created")

    # Start containers
    print("Starting containers...")

    # Start NFD container
    print("Starting NFD container...")
    try:
        old_container = client.containers.get("nfd1")
        print("Found existing NFD container, removing...")
        old_container.remove(force=True)
    except docker.errors.NotFound:
        pass

    nfd_container = client.containers.run(
        nfd_image_tag,
        name="nfd1",
        entrypoint=["/usr/bin/nfd"],
        command=["--config", "/custom-config/nfd.conf"],
        volumes={
            os.path.abspath('./cluster/nfd-node-config'): {'bind': '/custom-config', 'mode': 'rw'},
            os.path.abspath('./sec_data/certs'): {'bind': '/certs', 'mode': 'rw'}
        },
        detach=True,
        environment={
            "APP_PREFIX": "ndn-compute"
        },
        network=network_name
    )

    # Need to set the specific IP after container creation
    network.disconnect(nfd_container)
    network.connect(nfd_container, ipv4_address='192.168.1.2')
    print(f"NFD container started with ID: {nfd_container.id}")

    # Start driver container
    print("Starting driver container...")
    try:
        old_container = client.containers.get("driver1")
        print("Found existing driver container, removing...")
        old_container.remove(force=True)
    except docker.errors.NotFound:
        pass

    driver_container = client.containers.run(
        driver_image_tag,
        name="driver1",
        detach=True,
        environment={
            "APP_PREFIX": "ndn-compute",
            "MANAGEMENT_PORT": "5214"
        },
        ports={'5214/tcp': 5214},
        network=network_name
    )

    # Need to set the specific IP after container creation
    network.disconnect(driver_container)
    network.connect(driver_container, ipv4_address='192.168.1.10')
    print(f"Driver container started with ID: {driver_container.id}")

    # Generate dynamic worker configurations
    worker_containers = []

    for n in range(1, num_workers + 1):
        worker_name = f"worker{n}"
        worker_ip = f"192.168.1.{19 + n}"  # Starting from 192.168.1.20 for worker1
        worker_id = str(n)

        print(f"Starting worker container: {worker_name} with IP {worker_ip}...")

        try:
            old_container = client.containers.get(worker_name)
            print(f"Found existing {worker_name} container, removing...")
            old_container.remove(force=True)
        except docker.errors.NotFound:
            pass

        # Ensure the data directory exists
        data_dir = f'./generated_data/distributed/{worker_id}'
        os.makedirs(os.path.abspath(data_dir), exist_ok=True)

        worker_container = client.containers.run(
            worker_image_tag,
            name=worker_name,
            detach=True,
            environment={
                "APP_PREFIX": "ndn-compute",
                "WORKER_ID": worker_id
            },
            volumes={
                os.path.abspath(data_dir): {'bind': '/app/data', 'mode': 'rw'}
            },
            network=network_name
        )

        # Need to set the specific IP after container creation
        network.disconnect(worker_container)
        network.connect(worker_container, ipv4_address=worker_ip)
        print(f"Worker container {worker_name} started with ID: {worker_container.id}")

        worker_containers.append({
            "name": worker_name,
            "ip": worker_ip,
            "id": worker_id,
            "container": worker_container
        })

    print(f"NDN compute cluster deployment complete with {num_workers} workers!")
    return {
        "network": network,
        "nfd": nfd_container,
        "driver": driver_container,
        "workers": worker_containers
    }


def stop_ndn_compute_cluster(client=None):
    # Initialize Docker client if not provided
    if client is None:
        client = docker.from_env()

    print("Stopping NDN compute cluster...")

    # Stop NFD container
    try:
        nfd_container = client.containers.get("nfd1")
        print("Stopping NFD container...")
        nfd_container.stop()
        nfd_container.remove()
        print("NFD container stopped and removed.")
    except docker.errors.NotFound:
        print("NFD container not found.")
    except Exception as e:
        print(f"Error stopping NFD container: {e}")

    # Stop driver container
    try:
        driver_container = client.containers.get("driver1")
        print("Stopping driver container...")
        driver_container.stop()
        driver_container.remove()
        print("Driver container stopped and removed.")
    except docker.errors.NotFound:
        print("Driver container not found.")
    except Exception as e:
        print(f"Error stopping driver container: {e}")

    # Find and stop all worker containers (worker1, worker2, etc.)
    worker_count = 0
    worker_index = 1

    # Keep looking for workers until we find one that doesn't exist
    while True:
        worker_name = f"worker{worker_index}"
        try:
            worker_container = client.containers.get(worker_name)
            print(f"Stopping {worker_name} container...")
            worker_container.stop()
            worker_container.remove()
            worker_count += 1
            print(f"{worker_name} container stopped and removed.")
        except docker.errors.NotFound:
            print(f"{worker_name} container not found.")
            # Break the loop at the first missing worker
            break
        except Exception as e:
            print(f"Error stopping {worker_name} container: {e}")
            # Also break if there's an error with a worker container
            break

        worker_index += 1

    # Remove the network
    network_name = "ndn_compute_net"
    try:
        network = client.networks.get(network_name)
        print(f"Removing network {network_name}...")
        network.remove()
        print(f"Network {network_name} removed.")
    except docker.errors.NotFound:
        print(f"Network {network_name} not found.")
    except Exception as e:
        print(f"Error removing network: {e}")

    print(f"NDN compute cluster shutdown complete. Stopped {worker_count} workers.")
