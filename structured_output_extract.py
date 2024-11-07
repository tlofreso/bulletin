import json
from time import sleep
from typing import List, IO

from pydantic import BaseModel, Field
import PyPDF2
from tempfile import NamedTemporaryFile
from ocr import analyze_document

#from openai import Client
import openai

MASSTIME_PROMPT = """What are the regular Mass Times at this Parish?"""
CONFESSIONTIME_PROMPT = """What are the regular Confession Times at this Parish?"""
ADORATION_PROMPT = """When is Eucharistic Adoration held at this parish?  The "day" attribute should be the name of the day, and the "time" attribute should be an int representing 24hr time.  (900 is 9am, 1400 is 2pm, etc.) The "duration" attribute should be an int representing the number of minutes between the start and end of adoration (for example, if adoration goes from 3:00pm to 4:00pm, the duration would be 60).  If it appears adoration is held all fo the time, for 24 hours a day, or "perpetually", then set the "is24hour" attribute to the boolean true, "day" attribute to all, and the rest of the attributes to 0. If there is no adoration at this parish, then set the "is24hour" attribute to the boolean false, "day" to "none", and time and duration to 0."""

class MassTime(BaseModel):
    day: str = Field(..., description="Day of the week. e.g., 'Monday'")
    time: int = Field(..., description="Time of the day. Use 4-digit time format, e.g., 1630 for 4:30pm. All times are local.")

class MassTimes(BaseModel):
    masses: List[MassTime] = Field(..., description="List of MassTime instances representing individual mass schedules")

class ConfessionTime(BaseModel):
    day: str = Field(..., description="Day of the week, e.g., 'Saturday'")
    time: int = Field(..., description="Time in 24-hour format, e.g., 1500 for 3:00pm. All times are local.")
    duration: int = Field(..., description="Duration of confession in minutes")

class ConfessionTimes(BaseModel):
    confessions: List[ConfessionTime] = Field(..., description="List of ConfessionTime instances representing individual confession schedules")

class AdorationTime(BaseModel):
    is24hour: bool = Field(..., description="True if adoration runs 24 hours")
    day: str = Field(..., description="Day of the week, e.g., 'Tuesday'")
    time: int = Field(..., description="Time in 24-hour format, e.g., 800 for 8:00am. All times are local.")
    duration: int = Field(..., description="Duration of adoration in minutes")

class AdorationTimes(BaseModel):
    adorations: List[AdorationTime] = Field(..., description="List of AdorationTime instances representing individual adoration schedules")

def get_times(client: openai.Client, activity:List[str], bulletin_pdf:IO[bytes]):
    response_masstimes, response_adorationtimes, response_confessiontimes = ([],[],[])
    bulletin_md = analyze_document(bulletin_pdf)["content"]

    for event in activity:
        prompt = MASSTIME_PROMPT # etc
        if event in ["mass"]:
            prompt = MASSTIME_PROMPT
            schema = MassTimes
        if event in ["conf"]:
            prompt = CONFESSIONTIME_PROMPT
            schema = ConfessionTimes
        if event in ["adore"]:
            prompt = ADORATION_PROMPT
            schema = AdorationTimes

        print(event)
        completion = client.beta.chat.completions.parse(

            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": bulletin_md},
            ],
            response_format=schema,
        )

        response = completion.choices[0].message.parsed
        print(response)

        if event in ["mass"]:
            response_masstimes = response.masses
        if event in ["conf"]:
            response_confessiontimes = response.confessions
        if event in ["adore"]:
            response_adorationtimes = response.adorations

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
        bulletin_file.seek(0)

        client = openai.Client()

        mass_times = get_times(client, ["mass"], bulletin_file)

        for mass_time in mass_times:
            print(mass_time)
