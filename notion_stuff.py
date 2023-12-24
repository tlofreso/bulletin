import os
from typing import List

from notion_client import Client
from pydantic import BaseModel

database_id = "00f6fa861276497580fbf6ef48bc53e9"

def get_notion_client_from_environment() -> Client:
    return Client(auth=os.environ["NOTION_API_KEY"])

notion = get_notion_client_from_environment()


class ParishRow(BaseModel):
    name:str
    enabled:bool
    parish_id:str


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

def findPageID(parishName):
    response = notion.databases.query(
        **{"database_id": database_id,
           "filter": {
               "property": "Name",
               "title": {"equals": parishName}
            }
        }
    )
    resultList = [i["id"] for i in response['results']]     #Coming out of the list, the key is ['hash-code-here']
    resultList = str(resultList)[2:-2]                      #To work with the ID, I'm removing the [' and the '].
    return resultList

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
    elif property_type == "checkbox":
        return property["checkbox"]

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

    print(response.keys())

    results = []
    for row in response["results"]:
        results.append(ParishRow(
            name      = get_row_property_value(row, "Name"),
            enabled   = get_row_property_value(row, "Enable"),
            parish_id = get_row_property_value(row, "ParishID"),
        ))


    # pagination via recursion isn't probably a perfect idea, but I'm lazy
    if response["has_more"] == True:
        results.extend(get_all_parishes(client, database_id, cursor=response["next_cursor"]))
    
    return results


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
            selectedID = findPageID(selectParish)
            if selectedID == '':
                print ("Not a valid parish. Try again\n")
                pass
            else:
                print("\nThe pageID for " + selectParish + " is " + str(selectedID))
                updateText = input("\nType something to put in the 'notes' column for this parish: ")
                updateContent(selectedID, updateText)
                print("\nGot it! Check the database.")
                break
        # print(selectedID == ['b665cd6a-b72c-49f7-a9be-67ddf941e846'])
        # print(selectedID == [])

    #   findPageID(parish)     #Find the ID of the parish
    #   createParish(parish)   #Create a parish in the database
    #   updateContent(parish, content)    #Update the content of a predetermined property. 
