import argparse
from datetime import date, timedelta
import os
import sys
import time
from tempfile import TemporaryFile, NamedTemporaryFile

from download_bulletins import download_bulletin
from info_extract import get_times, count_pages
from notion_stuff import get_notion_client_from_environment, get_all_parishes, get_individual_parish, upload_parish_analysis
from openai import Client
from rich import print

# Function to initialize and parse command line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description='Update parish mass times in the Notion DB.')

    parser.add_argument('-d', '--dry-run', action='store_true', help='Dry run: downloads bulletins but does not update the database')
    parser.add_argument('-a', '--all', action='store_true', help='Runs against all enabled parishes with expired data')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose')
    parser.add_argument('-m', '--mass', action='store_true', help='Search for Mass Times')
    parser.add_argument('-c', '--confession', action='store_true', help='Search for Confession Times')
    parser.add_argument('-e', '--adoration', action='store_true', help='Search for Adoration Times')
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


def run_parish(parish_id:str, publisher:str, config:argparse.Namespace, mass:bool=False, confession:bool=False, adoration:bool=False, dry_run:bool=False, verbose:bool=False):

    # Tiny not-great logging utility
    analysis_log = []
    def log(message, console=False):
        """Adds something to the log we'll write to notion, and optionally prints it out"""
        analysis_log.append(message)
        if console:
            print(f"Parish {parish_id}: {message}")

    log("Process start.", console=True)

    with TemporaryFile('w+b') as temp_file:
        if publisher in ["Parishes Online"]: 
            url = download_bulletin(parish_id, temp_file, "PO")
        if publisher in ["Discover Mass"]:
            url = download_bulletin(parish_id, temp_file, "DM")
            log("Brief delay to prevent a lockout", console=True)
            time.sleep(30)
        if publisher in ["eCatholic"]:
            url = download_bulletin(parish_id, temp_file, "EC")
        if publisher in ["Other"]:
            return      #There's no code to process "other" bulletins yet"
        temp_file.seek(0)
        log(f"Downloaded bulletin from {publisher}.", console=True)

        page_count = count_pages(temp_file)
        temp_file.seek(0)
        log(f"Counted {page_count} pages in this PDF", console=True)

### TO DO ###
### main.py
###
### Combine all 3 activities into one request, use an array (events = get_times(... ['mass', 'adoration', 'confession']))
### Filter out via json, sort into mass_times, etc. And do all of the logic.
###     e.g. mass_times = json.loads(events){mass} or however json works
###
### info_extract.py
###
### Implement a for loop
### Can I resume a run?
### Only delete bulletin file remotely after I'm done with it
### Adjust event logic & checking
        openai_client = Client()
        if mass:
            mass_times = get_times(openai_client, config.bulletin_assistant_id, "mass", temp_file)
            log(f"Extracted {len(mass_times)} mass times.", console=True)
            if len(mass_times) == 0:
                log(f"Because no masses were found, they will not be updated.", console=True)

            for mass_time in mass_times:
                log(f"Found mass {mass_time}", console=verbose)
        else:
            mass_times = ""

        if confession:
            confession_times = get_times(openai_client, config.bulletin_assistant_id, "conf", temp_file)
            log(f"Extracted {len(confession_times)} confession times.", console = True)
            if len(confession_times) == 0:
                log(f"Because no confessions were found, they will not be updated.", console=True)
            
            for confession_time in confession_times:
                log(f"Found confession at {confession_time}", console=verbose)
        else:
            confession_times = ""

        if adoration:
            adoration_times = get_times(openai_client, config.bulletin_assistant_id, "adore", temp_file)
            log(f"Extracted {len(adoration_times)} adoration times.", console=True)
            if len(adoration_times) == 0:
                log(f"Because no adoration was found, this will not be updated.", console=True)
            
            for adoration_time in adoration_times:
                log(f"Found adoration at {adoration_time}", console=verbose)
        else:
            adoration_times = ""

        if dry_run:
            log(f"Dry run - skipping DB update.", console=True)

        else:
            notion_client = get_notion_client_from_environment()
            upload_parish_analysis(
                notion_client, 
                config.parish_db_id, 
                parish_id, 
                mass_times,
                confession_times,
                adoration_times, 
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

    if not args.mass and not args.confession and not args.adoration:
        sys.exit(f'Error: No data selected. As this serves no purpose, I will now quit. Try again with the -m and/or the -c operators')

    if args.all:
        print("Running against all enabled parishes with old data...")
        all_parishes = get_all_parishes(notion_client, config.parish_db_id)
        expiration_date = date.today() - timedelta(days=7)
        parishes_to_run = [p for p in all_parishes if p.enabled and p.last_run_timestamp < expiration_date]
        if args.verbose:
            print(f"Found the following {len(parishes_to_run)} enabled parishes:")
            for p in parishes_to_run:
                print(p)

        parish_ids_to_run = [p.parish_id for p in parishes_to_run]

    if len(parish_ids_to_run) == 0:
        sys.exit(f"Error: No parishes specified or none found enabled in DB. Use -a or positional arguments to specify parishes")

    if not args.all:
        print("Running against the requested parish ID, *regardless* of it is enabled or out of date")
        single_parish = get_individual_parish(notion_client, config.parish_db_id, args.parish_ids[0])
        expiration_date = date.today() - timedelta(days=7)
        parishes_to_run = [p for p in single_parish]
        parish_ids_to_run = [p.parish_id for p in parishes_to_run]

    for parish in parishes_to_run:
        run_parish(parish.parish_id, parish.publisher, config, args.mass, args.confession, args.adoration, args.dry_run, args.verbose)

if __name__ == "__main__":
    main()
 