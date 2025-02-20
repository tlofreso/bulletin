import notion_stuff
import json
import datetime

client = notion_stuff.get_notion_client_from_environment()
def convertTo12H(time):
    try:
        time = str(time)
        if len(time) != 4:
            time = time.zfill(4)
        time = datetime.datetime.strptime(time, "%H%M")
        return(time.strftime("%-I:%M%p"))
    except:
        print("ERROR!" + time)
def convertToDateTimeWithDuration(time, duration):
    try:
        time = str(time)
        if len(time) != 4:
            time = time.zfill(4)
        time = datetime.datetime.strptime(time, "%H%M")
        endtime = time + datetime.timedelta(minutes=duration)
        return(time.strftime("%-I:%M%p"), endtime.strftime("%-I:%M%p"))
    except:
        raise
def cleanList(string:str):
    table = str.maketrans("", "", "[]'")
    return string.translate(table)

def main():
    master_list = notion_stuff.extract_all_parish_info(client, notion_stuff.database_id)
    master_json = []
    for parish in master_list:
        parish_json = {}
        for detail in parish:
            try:
                if detail[0] in ["name"]:
                    parish_json[detail[0]] = detail[1].split(",")[0]
                if detail[0] in ["address", "city", "zip_code", "phone", "www"]:
                    parish_json[detail[0]] = detail[1]
                if detail[0] in ["mass_times"]:
                    times = json.loads(detail[1])
                    calendar = []
                    for weekday in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]:
                        day = []
                        for mass in times:                    
                            if mass["day"] == weekday:
                                day.append(convertTo12H(mass["time"]))
                        if len(day) > 0:
                            # calendar.append(weekday + ": " + cleanList(str(day)))
                            var = ""
                            for n in day:
                                var = var + str(day[n])
                            print(var)
                            calendar.append(weekday + ": " + str(day[0]))
                    # print(calendar)
                    parish_json[detail[0]] = calendar
                if detail[0] in ["conf_times"]:
                    times = json.loads(detail[1])
                    # print(times)
                    calendar = []
                    for weekday in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]:
                        day = []
                        for conf in times:                    
                            if conf["day"] == weekday:
                                day.append(convertToDateTimeWithDuration(conf["time"], conf["duration"]))
                        if len(day) > 0:
                            calendar.append(weekday + ": " + str(day[0][0] + " to " + str(day[0][1])))
                    print(calendar)
                    parish_json[detail[0]] = calendar
                if detail[0] in ["coords"]:
                    parish_json["latitude"] = float(detail[1].split(",")[1])
                    # print(detail[1].split(",")[0])
                    parish_json["longitude"] = float(detail[1].split(",")[0])
            except json.decoder.JSONDecodeError as e:
                parish_json[detail[0]] = ["TBD"]
        master_json.append(parish_json)

    with open('export.json', 'w', encoding='utf-8') as f:
        json.dump(master_json, f, ensure_ascii=False, indent=2)
        return("Exported Notion Data to export.json!")

if __name__ == "__main__":
    from rich import print
    print(main())
