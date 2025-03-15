from ndn_compute_cluster_manager import run_ndn_compute_stack
import os


if __name__ == "__main__":
    if not os.path.isdir('cluster'):
        raise Exception("Can't find the necessary files to build the cluster, are you in the repository root?")

    # TODO: argparse to run the various build/run/stop commands
    # Deploy with default 2 workers, or specify a different number
    run_ndn_compute_stack(num_workers=2)
