import argparse
import os
import sys
from tempfile import TemporaryFile

from download_bulletins import download_bulletin
from info_extract import get_mass_times
from notion_stuff import get_notion_client_from_environment, get_all_parishes, upload_parish_analysis
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


def run_parish(parish_id:str, config:argparse.Namespace, dry_run:bool=False, verbose:bool=False):

    # Tiny not-great logging utility
    analysis_log = []
    def log(message, console=False):
        """Adds something to the log we'll write to notion, and optionally prints it out"""
        analysis_log.append(message)
        if console:
            print(f"Parish {parish_id}: {message}")

    log("Process start.", console=True)

    with TemporaryFile('w+b') as temp_file:
        url = download_bulletin(parish_id, temp_file)
        log("Downloaded bulletin.", console=True)

        openai_client = Client()
        temp_file.seek(0)
        mass_times = get_mass_times(openai_client, config.bulletin_assistant_id, temp_file)
        log(f"Extracted {len(mass_times)} mass times.", console=True)

        for mass_time in mass_times:
            log(f"Found mass {mass_time}", console=verbose)

        if dry_run:
            log(f"Dry run - skipping DB update.", console=True)
        else:
            notion_client = get_notion_client_from_environment()
            upload_parish_analysis(
                notion_client, 
                config.parish_db_id, 
                parish_id, 
                mass_times, 
                url,
                analysis_log
            )
            log(f"Uploaded to Notion.", console=True)

    log(f"Finished.", console=True)


def main():
    args = parse_arguments()

    # Load configuration
    config = get_config()
    notion_client = get_notion_client_from_environment()

    parish_ids_to_run = args.parish_ids
    if args.all:
        print("Running against all enabled parishes...")
        all_parishes = get_all_parishes(notion_client, config.parish_db_id)
        parishes_to_run = [p for p in all_parishes if p.enabled]
        if args.verbose:
            print(f"Found the following {len(parishes_to_run)} enabled parishes:")
            for p in parishes_to_run:
                print(p)

        parish_ids_to_run = [p.parish_id for p in parishes_to_run]

    if len(parish_ids_to_run) == 0:
        sys.exit(f"Error: No parishes specified or none found enabled in DB. Use -a or positional arguments to specify parishes")

    for parish_id in parish_ids_to_run:
        run_parish(parish_id, config, args.dry_run, args.verbose)

if __name__ == "__main__":
    main()
 