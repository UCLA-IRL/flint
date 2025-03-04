import argparse
from ndn_compute_key_creator import create_keys


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate security keys for specified entities.")
    parser.add_argument('--path', type=str, default='sec_data/',
                        help='Directory path to store keys (default: sec_data/)')
    parser.add_argument('--entities', nargs='+', default=['worker', 'driver'],
                        help='List of entities (default: worker driver)')
    parser.add_argument('--app_prefix', type=str, default='ndn-compute',
                        help='Application prefix (default: ndn-compute)')

    args = parser.parse_args()
    create_keys(path=args.path, entities=args.entities, app_prefix=args.app_prefix)
