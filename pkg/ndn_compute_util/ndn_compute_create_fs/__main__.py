import argparse
from ndn_compute_fs_creator import create_fs_from_directory


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Create a toy distributed filesystem by chunking and distributing files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "in_dir",
        help="Input directory containing files to distribute"
    )

    parser.add_argument(
        "out_dir",
        help="Output directory for the distributed filesystem"
    )

    parser.add_argument(
        "-p", "--partitions",
        type=int,
        default=2,
        help="Number of partitions (machines) to distribute files across"
    )

    parser.add_argument(
        "-c", "--copies",
        type=int,
        default=1,
        help="Number of copies of each chunk to maintain"
    )

    parser.add_argument(
        "-s", "--chunk-size",
        type=int,
        default=64,
        help="Approximate size of each chunk in megabytes"
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    try:
        create_fs_from_directory(
            in_dir=args.in_dir,
            out_dir=args.out_dir,
            num_partitions=args.partitions,
            num_copies=args.copies,
            chunk_size=args.chunk_size
        )
        print(f"Successfully created distributed filesystem:")
        print(f"- Input directory: {args.in_dir}")
        print(f"- Output directory: {args.out_dir}")
        print(f"- Number of partitions: {args.partitions}")
        print(f"- Copies per chunk: {args.copies}")
        print(f"- Chunk size: {args.chunk_size}MB")
    finally:
        pass
    """
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exit(1)
    """