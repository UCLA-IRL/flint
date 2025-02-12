import os
from xmlrpc.server import SimpleXMLRPCServer
from ndn_compute_remote import NdnComputeRemote


def main():
    management_port = int(os.environ.get("MANAGEMENT_PORT", "5000"))

    print(f"Driver running at {management_port} (may also be forwarded to host machine)", flush=True)

    server = SimpleXMLRPCServer(("0.0.0.0", management_port))
    server.register_instance(NdnComputeRemote())
    server.serve_forever()


if __name__ == "__main__":
    main()
