import argparse
import os
import sys
from tempfile import TemporaryFile

from download_bulletins import download_bulletin
from info_extract import get_mass_times
from notion_stuff import get_notion_client_from_environment, get_all_parishes
from openai import Client
from rich import print

# Function to initialize and parse command line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description='Update parish mass times in the Notion DB.')

    parser.add_argument('-d', '--dry-run', action='store_true', help='Dry run: downloads bulletins but does not update the database')
    parser.add_argument('-a', '--all', action='store_true', help='Runs against all enabled parishes')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose')
    parser.add_argument('parish_ids', nargs='*', help='ID(s) of the parish(es) to be checked')

    return parser.parse_args()

# Function to check for required environment variables and return them in a config object
def get_config():
    required_vars = ['OPENAI_API_KEY', 'BULLETIN_ASSISTANT_ID', 'NOTION_API_KEY', 'PARISH_DB_ID']
    config = {}

    missing_vars = [var for var in required_vars if var not in os.environ]
    if missing_vars:
        sys.exit(f"Error: Missing environment variables: {', '.join(missing_vars)}")

    for var in required_vars:
        config[var.lower()] = os.environ[var]

    return argparse.Namespace(**config)

def parish_log(parish_id:str, message):
    print(f"Parish {parish_id}: {message}")

def run_parish(parish_id:str, config:argparse.Namespace, dry_run:bool=False, verbose:bool=False):
    parish_log(parish_id, "Process start.")

    with TemporaryFile('w+b') as temp_file:
        download_bulletin(parish_id, temp_file)
        parish_log(parish_id, "Downloaded bulletin.")

        openai_client = Client()
        temp_file.seek(0)
        mass_times = get_mass_times(openai_client, config.bulletin_assistant_id, temp_file)
        parish_log(parish_id, f"Extracted {len(mass_times)} mass times")

        if verbose:
            for mass_time in mass_times:
                parish_log(parish_id, f"Found mass {mass_time}")
        if dry_run:
            parish_log(parish_id, f"Dry run - skipping DB update")


def main():
    args = parse_arguments()

    # Load configuration
    config = get_config()
    notion_client = get_notion_client_from_environment()

    parish_ids_to_run = args.parish_ids
    if len(parish_ids_to_run) == 0 and not args.all:
        sys.exit(f"Error: No parishes specified. Use -a or positional arguments to specify parishes")

    elif args.all:
        print("Running against all enabled parishes...")
        all_parishes = get_all_parishes(notion_client, config.parish_db_id)
        parishes_to_run = [p for p in all_parishes if p.enabled]
        if args.verbose:
            print("Found the following enabled parishes:")
            for p in parishes_to_run:
                print(p)

        parish_ids_to_run = [p.parish_id for p in parishes_to_run]

    for parish_id in parish_ids_to_run:
        run_parish(parish_id, config, args.dry_run, args.verbose)

if __name__ == "__main__":
    main()
 