from ndn_compute_cluster_manager import (buildnfd_ndn_compute_cluster,
                                         build_ndn_compute_cluster,
                                         run_ndn_compute_cluster,
                                         stop_ndn_compute_cluster)
import sys
import argparse
import os


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="NDN Compute Cluster Manager",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Build command
    build_parser = subparsers.add_parser(
        "build",
        help="Build the NDN compute cluster images (driver and worker)"
    )

    # BuildNFD command
    buildnfd_parser = subparsers.add_parser(
        "buildnfd",
        help="Build only the NFD image"
    )

    # Start command
    start_parser = subparsers.add_parser(
        "start",
        help="Start the NDN compute cluster with a specified number of workers"
    )
    start_parser.add_argument(
        "num_workers",
        type=int,
        help="Number of worker containers to start"
    )
    start_parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild driver and worker before starting containers"
    )

    # Stop command
    stop_parser = subparsers.add_parser(
        "stop",
        help="Stop all running NDN compute cluster containers"
    )

    args = parser.parse_args()

    if not os.path.isdir('cluster'):
        raise Exception("Can't find the necessary files to build the cluster, are you in the repository root?")

    # Execute the appropriate function based on the command
    if args.command == "build":
        build_ndn_compute_cluster()
    elif args.command == "buildnfd":
        buildnfd_ndn_compute_cluster()
    elif args.command == "start":
        run_ndn_compute_cluster(num_workers=args.num_workers, rebuild=args.rebuild)
    elif args.command == "stop":
        stop_ndn_compute_cluster()
    else:
        parser.print_help()
        sys.exit(1)
