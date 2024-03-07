import json
from time import sleep
from typing import List, IO

from pydantic import BaseModel
import PyPDF2

from openai import Client

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

class MassTime(BaseModel):
    day: str  # "Monday"
    time: int # 1630 is 4:30pm. All times local

class ConfessionTime(BaseModel):
    day: str # "Saturday"
    time: int # 1500 is 3:00pm. All times local
    duration: int # Number of minutes confession runs for

def get_times(client:Client, assistant_id:str, activity:str, bulletin_pdf:IO[bytes]) -> List[MassTime]:
    assistant = client.beta.assistants.retrieve(assistant_id)
    uploaded_bulletin=client.files.create(
        purpose="assistants",
        file=bulletin_pdf
    )

    thread = client.beta.threads.create()
    if activity in ["mass"]:   
        client.beta.threads.messages.create(
            thread_id=thread.id, 
            content=MASSTIME_PROMPT,
            role="user",
            file_ids=[uploaded_bulletin.id]
        )
    if activity in ["conf"]:   
        client.beta.threads.messages.create(
            thread_id=thread.id, 
            content=CONFESSIONTIME_PROMPT,
            role="user",
            file_ids=[uploaded_bulletin.id]
        )        
    #try:
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )
#    except:
#        print(f"OpenAI wasn't able to process the bulletin pdf/tempfile for some reason - skipping")
#        return ""

    while run.status in ["queued", "in_progress", "cancelling"]:
        #print(run.status)
        sleep(2)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    #print(run.status)

    messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )

    client.files.delete(uploaded_bulletin.id)
    client.beta.threads.delete(thread.id)

#    print(messages.data[0].content[0].text.value)
    response_role = messages.data[0].role
    if response_role == "user":
#        raise Exception("Last message in thread is not from the assistant. Have you hit the usage limit?")
        print(f"Last message in the thread is not from the assistant. Perhaps a usage limit issue? No response at all?")
        return ""

    response_string = messages.data[0].content[0].text.value
#    print(response_string)
    json_str = response_string[response_string.find("[") : response_string.rfind("]") + 1]
    try:
        response_json = json.loads(json_str)
        if activity in ["mass"]:
            response_masstimes = [MassTime.model_validate_json(json.dumps(j)) for j in response_json]
            return response_masstimes
        if activity in ["conf"]:
            response_confessiontimes = [ConfessionTime.model_validate_json(json.dumps(j)) for j in response_json]
            return response_confessiontimes    
    except ValueError:
        print(f'Something went wrong parsing the JSON: {json_str}')
        print(f'The OpenAI response might be helpful: {response_string}')
        return ""

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
        download_bulletin("0689", bulletin_file)

        client = Client()
        assistant_id = environ["BULLETIN_ASSISTANT_ID"]

        mass_times = get_times(client, assistant_id, "mass", bulletin_file)

        for mass_time in mass_times:
            print(mass_time)
