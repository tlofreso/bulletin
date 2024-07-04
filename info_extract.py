import json
from time import sleep
from typing import List, IO

from pydantic import BaseModel
import PyPDF2
from tempfile import NamedTemporaryFile

#from openai import Client
import openai

MASSTIME_PROMPT = """What are the regular Mass Times at this Parish?  Provide output as a valid JSON array in which every object in the array represents a single mass time.  Include attributes for the day of the week and the time of day.  The "day" attribute should be the name of the day, and the "time" attribute should be an int representing 24hr time.  (900 is 9am, 1400 is 2pm, etc.)

Example Response:

[
 {
    "day": "Sunday",
    "time": 900
 }
]

Do not include any content in the response other than the JSON itself.
"""

CONFESSIONTIME_PROMPT = """What are the regular Confession Times at this Parish?  Provide output as a valid JSON array in which every object in the array represents a single confession time.  Include attributes for the day of the week, the time of day, and its duration.  The "day" attribute should be the name of the day, and the "time" attribute should be an int representing 24hr time.  (900 is 9am, 1400 is 2pm, etc.) The "duration" attribute should be an int representing the number of minutes between the start and end of confession (for example, if confessions run from 3:00pm to 4:00pm, the duration would be 60).

Example Response:

[
 {
    "day": "Saturday",
    "time": 1500,
    "duration": 60
 }
]

Do not include any content in the response other than the JSON itself.
"""

ADORATION_PROMPT = """When is Eucharistic Adoration held at this parish? Provide output as a valid JSON array in which every object in the array represents a single adoration time.  Include attributes for if it is 24 hours, the day of the week, the time of day, and its duration.  The "day" attribute should be the name of the day, and the "time" attribute should be an int representing 24hr time.  (900 is 9am, 1400 is 2pm, etc.) The "duration" attribute should be an int representing the number of minutes between the start and end of adoration (for example, if adoration goes from 3:00pm to 4:00pm, the duration would be 60).
If it appears adoration is held all fo the time, for 24 hours a day, or "perpetually", then set the "is24hour" attribute to the boolean true, "day" attribute to all, and the rest of the attributes to 0. If there is no adoration at this parish, then set the "is24hour" attribute to the boolean false, "day" to "none", and time and duration to 0.

Example Response:
[
 {
    "is24hour": false,
    "day": "Saturday",
    "time": 1500,
    "duration": 60
 }
]

Do not include any content in the response other than the JSON itself.
"""

class MassTime(BaseModel):
    day: str  # "Monday"
    time: int # 1630 is 4:30pm. All times local

class ConfessionTime(BaseModel):
    day: str # "Saturday"
    time: int # 1500 is 3:00pm. All times local
    duration: int # Number of minutes confession runs for

class AdorationTime(BaseModel):
    is24hour: bool # True
    day: str # "Tuesday"
    time: int # 800 is 8am. All times local.
    duration: int #Number of minutes for adoration

def get_times(client: openai.Client, assistant_id:str, activity:List[str], bulletin_pdf:IO[bytes]) -> List[MassTime]:
    response_masstimes, response_adorationtimes, response_confessiontimes = ([],[],[])
    assistant = client.beta.assistants.retrieve(assistant_id)
    with NamedTemporaryFile('w+b', suffix=".pdf") as bulletin_with_suffix:
        bulletin_with_suffix.write(bulletin_pdf.read())
        uploaded_bulletin=client.files.create(
            purpose="assistants",
            file=bulletin_with_suffix.file
        )

    thread = client.beta.threads.create()
    # client.beta.threads.messages.create(
    #     thread_id=thread.id,
    #     role="user",
    #     content="Here is a parish bulletin. Analyze it, and prepare to answer questions about its contents.",
    #     attachments=[
    #         {
    #         "file_id": uploaded_bulletin.id,
    #         "tools": [{"type": "file_search"}]
    #         }
    #     ]
    # )

    for event in activity:
        print(event)
        prompt = MASSTIME_PROMPT # etc
        if event in ["mass"]:
            prompt = MASSTIME_PROMPT
        if event in ["conf"]:
            prompt = CONFESSIONTIME_PROMPT
        if event in ["adore"]:
            prompt = ADORATION_PROMPT
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt,
            attachments=[
                {
                "file_id": uploaded_bulletin.id,
                "tools": [{"type": "file_search"}]
                }
            ]
        )
        try:
            response = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id
            )
        except:
            raise

        #client.beta.threads.runs.update(run_id=response.id)
        while response.status in ["queued", "in_progress", "cancelling"]:
        #    print(response.status)
            sleep(2)
            response = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=response.id)
        messages_response = client.beta.threads.messages.list(thread_id=thread.id)
        response_role = messages_response.data[0].role
        #print(response_role)


        if response_role == "user":
    #        raise Exception("Last message in thread is not from the assistant. Have you hit the usage limit?")
            print(f"Last message in the thread is not from the assistant. Perhaps a usage limit issue? No response at all?")
            print(messages_response.data[0].content[0].text.value)
            return ""

        response_string = messages_response.data[0].content[0].text.value
    #   print(response_string)
        json_str = response_string[response_string.find("[") : response_string.rfind("]") + 1]

        try:
            response_json = json.loads(json_str)
            if event in ["mass"]:
                response_masstimes = [MassTime.model_validate_json(json.dumps(j)) for j in response_json]
            if event in ["conf"]:
                response_confessiontimes = [ConfessionTime.model_validate_json(json.dumps(j)) for j in response_json]
            if event in ["adore"]:
                response_adorationtimes = [AdorationTime.model_validate_json(json.dumps(a)) for a in response_json]
        except ValueError:
            print(f'Something went wrong parsing the JSON: {json_str}')
            print(f'The OpenAI response might be helpful: {response_string}')
            return ""

    #         thread_id=thread.id,
    #         content=CONFESSIONTIME_PROMPT,
    #         role="user",
    #         attachments=[
    #             {
    #             "file_id": uploaded_bulletin.id,
    #             "tools": [{"type": "file_search"}]
    #             }
    #         ]
    #     )
    # if activity in ["adore"]:
    #     client.beta.threads.messages.create(
    #         thread_id=thread.id,
    #         content=ADORATION_PROMPT,
    #         role="user",
    #         attachments=[
    #             {
    #             "file_id": uploaded_bulletin.id,
    #             "tools": [{"type": "file_search"}]
    #             }
    #         ]
    #     )
    client.files.delete(uploaded_bulletin.id)
    client.beta.threads.delete(thread.id)

    return(response_masstimes, response_confessiontimes, response_adorationtimes)

def count_pages(pdf:IO[bytes]) -> int:
    try:
        reader = PyPDF2.PdfReader(pdf)
        return len(reader.pages)
    except:
        print("PDF issue - Did you hit a usage cap?")
        return "0"

if __name__ == '__main__':
    # Test code
    from tempfile import TemporaryFile
    from os import environ
    from download_bulletins import download_bulletin

    with TemporaryFile("w+b") as bulletin_file:
        download_bulletin("our-lady-of-mount-carmel-wickliffe-oh", bulletin_file, "DM")

        client = openai.Client()
        assistant_id = environ["BULLETIN_ASSISTANT_ID"]

        mass_times = get_times(client, assistant_id, "mass", bulletin_file)

        for mass_time in mass_times:
            print(mass_time)
