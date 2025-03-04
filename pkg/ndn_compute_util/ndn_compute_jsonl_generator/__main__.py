import argparse
from ndn_compute_jsonl_generator import generate_large_jsonl


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a large JSONL file with dummy data.')
    parser.add_argument('filename', type=str, help='Name of the output file')
    parser.add_argument('size', type=float, help='Desired file size in megabytes')

    args = parser.parse_args()
    generate_large_jsonl(args.filename, args.size)
