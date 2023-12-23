from typing import List

from info_extract import MassTime
from notion_client import Client

def get_notion_client(api_key):
    return Client(auth=api_key)

def get_parishes_to_check(client:Client, database_id:str) -> List[str]:
    #client.databases.retrieve(database_id)
    print(client.databases.query(database_id))
    return ["0689"]

def update_parish_masstimes(parish_id:str, masstimes:List[MassTime]):
    return

if __name__ == "__main__":
    import os
    client = get_notion_client(os.environ["NOTION_API_KEY"])
    print(get_parishes_to_check(client, os.environ["PARISH_DB_ID"]))

