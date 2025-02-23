from datetime import date
import json
import os
from typing import List

from notion_client import Client
from pydantic import BaseModel

from info_extract import MassTime, ConfessionTime, AdorationTime, ParishInfo

database_id = "00f6fa861276497580fbf6ef48bc53e9"

def get_notion_client_from_environment() -> Client:
    return Client(auth=os.environ["NOTION_API_KEY"])

notion = get_notion_client_from_environment()


class ParishRow(BaseModel):
    name:str
    enabled:bool
    parish_id:str
    last_run_timestamp:date
    publisher:str

class ParishActivities(BaseModel):
    name:str
    enabled:bool
    coords:str
    address:str
    city:str
    zip_code:str
    phone:str
    www:str
    parish_id:str
    last_run_timestamp:str
    mass_times:str
    conf_times:str
    adore_times:str
    logs:str


def createParish(parishName):
    notion.pages.create(
        **{
            "parent": {
                "database_id": database_id
            },
            "properties": {
                "Name": {
                    "title":[
                        {
                            "text": {
                                "content": parishName
                                }
                        }
                    ]
                }
                #"Column 2 goes here"
            }
        }
    )

def findPageID(client:Client, db_id:str, filter:dict):
    response = client.databases.query(
        **{"database_id": db_id,
           "filter": filter
        }
    )
    resultList = [i["id"] for i in response['results']]     #Coming out of the list, the key is ['hash-code-here']
    if len(resultList) != 1:
        raise Exception(f"Didn't find a unique page for {filter}!")
    #resultList = str(resultList)[2:-2]                      #To work with the ID, I'm removing the [' and the '].
    return resultList[0]

def get_parish_page_key(client:Client, db_id:str, parish_id:str):
    filter = {
        "property": "ParishID",
        "rich_text": {"equals": parish_id}
    }
    return findPageID(client, db_id, filter)

def get_parish_page_key_by_name(client:Client, db_id:str, parishName:str):
    filter = {
        "property": "Name",
        "title": {"equals": parishName}
    }
    return findPageID(client, db_id, filter)


def updateContent(parishKey, newText):
    notion.pages.update(
        **{"page_id": parishKey,
           "properties": {
                "Notes": {
                    "rich_text":[
                        {
                            "text": {
                                "content": newText
                                }
                        }
                    ]
                }
            }
        }
    )

def get_row_property_value(row, attribute_name):
    property = row["properties"][attribute_name]
    property_type = property["type"]
    if property_type  in ["rich_text", "title"]:
        value = ""
        if len(property[property_type]) > 0:
            value = property[property_type][0]["plain_text"]
        return value
    elif property_type in ["checkbox", "url"]:
        return property[property_type]
    elif property_type in ["select"]:
        value = ""
        if property[property_type]:
            value = property[property_type]["name"]
        return value
    
    raise Exception("did not understand property with type " + property_type)

def get_all_parishes(client:Client, database_id:str, cursor=None) -> List[ParishRow]:
    """
    Gets a representation of every Parish in the DB.
    """
    #client.databases.retrieve(database_id)
    if cursor == None:
        response = client.databases.query(database_id)
    else:
        response = client.databases.query(database_id, start_cursor=cursor)

    #print(response.keys())

    results = []
    for row in response["results"]:
        #print(row)
        last_run_timestamp_str = get_row_property_value(row, "GPT Timestamp")
        if len(last_run_timestamp_str.strip()) == 0:
            last_run_timestamp_str = "1980-01-01"
        results.append(ParishRow(
            name      = get_row_property_value(row, "Name"),
            enabled   = get_row_property_value(row, "Enable"),
            parish_id = get_row_property_value(row, "ParishID"),
            last_run_timestamp = date.fromisoformat(last_run_timestamp_str),
            publisher = get_row_property_value(row, "Bulletin Publisher")
        ))


    # pagination via recursion isn't probably a perfect idea, but I'm lazy
    if response["has_more"] == True:
        results.extend(get_all_parishes(client, database_id, cursor=response["next_cursor"]))
    
    return results

def extract_all_parish_info(client:Client, database_id:str, cursor=None) -> List[ParishActivities]:
    """
    Pulls data from every Parish in the DB.
    """
    if cursor == None:
        response = client.databases.query(database_id)
    else:
        response = client.databases.query(database_id, start_cursor=cursor)

    results = []
    for row in response["results"]:
        last_run_timestamp_str = get_row_property_value(row, "GPT Timestamp")
        if len(last_run_timestamp_str.strip()) == 0:
            last_run_timestamp_str = "1980-01-01"
        results.append(ParishActivities(
            name      = get_row_property_value(row, "Name"),
            parish_id = get_row_property_value(row, "ParishID"),
            last_run_timestamp = str(date.fromisoformat(last_run_timestamp_str)),
            mass_times = get_row_property_value(row, "GPT Results"),
            conf_times = get_row_property_value(row, "Confession Testing"),
            adore_times = get_row_property_value(row, "Adoration Testing"),
            logs = get_row_property_value(row, "GPT Logs"),
            enabled = get_row_property_value(row, "Enable"),
            coords = get_row_property_value(row, "LonLat"),
            address = get_row_property_value(row, "Street Address"),
            city = get_row_property_value(row, "City"),
            zip_code = get_row_property_value(row, "Zip Code"),
            phone = get_row_property_value(row, "Phone Number"),
            www = get_row_property_value(row, "Website")
        ))

    if response["has_more"] == True:
        results.extend(extract_all_parish_info(client, database_id, cursor=response["next_cursor"]))

    return results

def get_individual_parish(client:Client, database_id:str, parish_id:str, cursor=None) -> List[ParishRow]:
    """
    Gets a representation of one requested Parish from the DB.
    """
    if cursor == None:
        response = client.databases.query(**{"database_id": database_id, "filter": { "property": "ParishID", "rich_text": {"contains": parish_id,},},})
        
    else:
        response = client.databases.query(database_id, start_cursor=cursor)

    results = []
    for row in response["results"]:
        #print(row)
        last_run_timestamp_str = get_row_property_value(row, "GPT Timestamp")
        if len(last_run_timestamp_str.strip()) == 0:
            last_run_timestamp_str = "1980-01-01"
        results.append(ParishRow(
            name      = get_row_property_value(row, "Name"),
            enabled   = get_row_property_value(row, "Enable"),
            parish_id = get_row_property_value(row, "ParishID"),
            last_run_timestamp = date.fromisoformat(last_run_timestamp_str),
            publisher = get_row_property_value(row, "Bulletin Publisher"),
            coords    = get_row_property_value(row, "LonLat"),
            address   = get_row_property_value(row, "Street Address"),
            city      = get_row_property_value(row, "City"),
            zip_code  = get_row_property_value(row, "Zip Code"),
            phone     = get_row_property_value(row, "Phone Number"),
            www       = get_row_property_value(row, "Website")
        ))
    
    return results

def get_text_property_json(text_content:str) -> dict:
    """
    Returns json usable for updates
    """
    return {
        "rich_text": [
            {
                "text": {
                    "content": text_content
                }
            }
        ]
    }

def get_url_property_json(url:str) -> dict:
    """
    Returns json usable for updates
    """
    return {
        "url": url
    }

def updateContent(client:Client, parishKey:str, updated_properties:dict):
    client.pages.update(
        page_id = parishKey,
        properties = updated_properties
    )

def upload_parish_analysis(client:Client, db_id, parish_id:str, mass_times:List[MassTime], conf_times:List[ConfessionTime], adore_times:List[AdorationTime], bulletin_url:str, analysis_log:List[str]):
    log_text = "\n".join(analysis_log)
    parish_page_key = get_parish_page_key(client, db_id, parish_id)
    mass_result_text = json.dumps([m.model_dump() for m in mass_times])
    conf_result_text = json.dumps([c.model_dump() for c in conf_times])
    adore_result_text = json.dumps([a.model_dump() for a in adore_times])
    timestamp = date.today().isoformat()
    updated_properties = {
        "GPT Logs": get_text_property_json(log_text),
        "Link to latest bulletin": get_url_property_json(bulletin_url),
        "GPT Timestamp": get_text_property_json(timestamp),
    }
    if mass_times:
        updated_properties["GPT Results"] = get_text_property_json(mass_result_text)
    if conf_times:
        updated_properties["Confession Testing"] = get_text_property_json(conf_result_text)
    if adore_times:
        updated_properties["Adoration Testing"] = get_text_property_json(adore_result_text)

    updateContent(client, parish_page_key, updated_properties)

def upload_parish_info(client:Client, db_id, parish_id:str, parish_info:List[ParishInfo]):
    parish_page_key = get_parish_page_key(client, db_id, parish_id)
    # info_text = json.dumps([i.model_dump() for i in parish_info])
    info = [i.model_dump() for i in parish_info]
    address = info[0]["address"]
    city = info[0]["city"]
    zipcode = info[0]["zipcode"]
    phone = info[0]["phone"]
    www = info[0]["website"]

    # print("info text:", info_text)
    updated_properties = {
        "Street Address": get_text_property_json(address),
        "City": get_text_property_json(city),
        "Zip Code": get_text_property_json(zipcode),
        "Phone Number": get_text_property_json(phone),
        "Website": get_text_property_json(www)
    }
    updateContent(client, parish_page_key, updated_properties)

if __name__ == "__main__":
    from rich import print
    # A little demo

    client = get_notion_client_from_environment()
    print(get_all_parishes(client, database_id))

    while True:
        selectParish = input("What parish do you want to select? Type its name *exactly* as it appears in the database!) ")
        if selectParish == "":
            print("Doesn't look like you selected anything. Try again\n")
            pass
        else:
            selectedID = get_parish_page_key_by_name(client, database_id, selectParish)
            if selectedID == '':
                print ("Not a valid parish. Try again\n")
                pass
            else:
                print("\nThe pageID for " + selectParish + " is " + str(selectedID))
                updateText = input("\nType something to put in the 'GPT Logs' column for this parish: ")
                updated_properties = {
                    "GPT Logs": get_text_property_json(updateText)
                }
                updateContent(client, selectedID, updated_properties)
                print("\nGot it! Check the database.")
                break
        # print(selectedID == ['b665cd6a-b72c-49f7-a9be-67ddf941e846'])
        # print(selectedID == [])

    #   findPageID(parish)     #Find the ID of the parish
    #   createParish(parish)   #Create a parish in the database
    #   updateContent(parish, content)    #Update the content of a predetermined property. 
