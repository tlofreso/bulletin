import notion_stuff
import json

client = notion_stuff.get_notion_client_from_environment()

master_list = notion_stuff.extract_all_parish_info(client, notion_stuff.database_id)
master_json = {}
for act in master_list:
    parish_json = []
    for element in act:
        try:
            if not element[0] in ["mass_times", "conf_times", "adore_times", "logs"]:
                parish_json.append({element[0]: element[1]})
            else:
                parish_json.append({element[0]: json.loads(element[1])})

        except json.decoder.JSONDecodeError as e:   #If there's an empty string, don't crash, but instead give an empty string back
            parish_json.append({element[0]: ""})

    master_json[parish_json[0]["name"]] = parish_json

if __name__ == "__main__":
    from rich import print
    print(master_json)