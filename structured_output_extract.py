import json
import os
from time import sleep
from typing import List, IO

from pydantic import BaseModel, Field
import PyPDF2
from tempfile import NamedTemporaryFile

# Use remote OCR server if OCR_SERVER_URL is set, otherwise use local Marker
if os.environ.get("OCR_SERVER_URL"):
    from ocr_client import analyze_document
else:
    from ocr_local import analyze_document

import openai

# LLM configuration: Use Ollama if OLLAMA_BASE_URL is set, otherwise OpenAI
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL")  # e.g., http://localhost:11434/v1
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5")

INFO_PROMPT = """What do I need to know to learn more about this parish or to find it on a map?"""
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

class ParishInfo(BaseModel):
    address: str = Field(..., description="The street address of the parish")
    city: str = Field(..., description="The city the parish is in")
    zipcode: str = Field(..., description="The parish zip code")
    phone: str = Field(..., description="The main phone number for contacting the parish")
    website: str = Field(..., description="The main parish website")

class ParishInfo2(BaseModel):
    metadata: List[ParishInfo] = Field(..., description="Summary of the metadata gathered")


def get_ollama_client():
    """Create an OpenAI client configured for Ollama"""
    return openai.Client(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama"  # Ollama doesn't require a real key
    )


def truncate_to_pages(markdown: str, max_pages: int = 4) -> str:
    """Truncate markdown to first N pages based on page markers from OCR.

    Note: Local LLMs (7B-14B) struggle with long bulletin text. Consider
    keeping the LLM component outsourced (OpenAI, etc.) for better accuracy.
    """
    import re
    # Find page markers like ![](_page_0_...) or ![](_page_1_...)
    page_pattern = re.compile(r'!\[\]\(_page_(\d+)_')

    matches = list(page_pattern.finditer(markdown))
    if not matches:
        # No page markers, return as-is
        return markdown

    # Find the position where page number exceeds max_pages
    for match in matches:
        page_num = int(match.group(1))
        if page_num >= max_pages:
            return markdown[:match.start()].strip()

    return markdown


def extract_with_ollama(client: openai.Client, prompt: str, schema: type[BaseModel], content: str):
    """Extract structured data using Ollama with JSON prompting"""
    schema_json = schema.model_json_schema()

    system_prompt = f"""{prompt}

You must respond with valid JSON matching this exact schema:
{json.dumps(schema_json, indent=2)}

IMPORTANT: Respond with ONLY the JSON object. No markdown, no explanation, no code blocks. Just pure JSON."""

    completion = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
    )

    response_text = completion.choices[0].message.content.strip()

    # Try to extract JSON from response (handle markdown code blocks)
    if response_text.startswith("```"):
        # Extract content between code blocks
        lines = response_text.split("\n")
        json_lines = []
        in_block = False
        for line in lines:
            if line.startswith("```"):
                in_block = not in_block
                continue
            if in_block:
                json_lines.append(line)
        response_text = "\n".join(json_lines)

    response_json = json.loads(response_text)
    return schema.model_validate(response_json)


def extract_with_openai(client: openai.Client, prompt: str, schema: type[BaseModel], content: str):
    """Extract structured data using OpenAI's native structured output"""
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content},
        ],
        response_format=schema,
    )
    return completion.choices[0].message.parsed


def get_times(client: openai.Client, activity: List[str], bulletin_pdf: IO[bytes]):
    response_masstimes, response_adorationtimes, response_confessiontimes, response_info = ([], [], [], [])
    bulletin_md = analyze_document(bulletin_pdf)["content"]

    # Choose extraction method based on configuration
    use_ollama = OLLAMA_BASE_URL is not None
    extract_fn = extract_with_ollama if use_ollama else extract_with_openai

    # Truncate input for local LLMs (they struggle with long documents)
    if use_ollama:
        bulletin_md = truncate_to_pages(bulletin_md, max_pages=4)

    for event in activity:
        prompt = MASSTIME_PROMPT
        if event in ["mass"]:
            prompt = MASSTIME_PROMPT
            schema = MassTimes
        if event in ["conf"]:
            prompt = CONFESSIONTIME_PROMPT
            schema = ConfessionTimes
        if event in ["adore"]:
            prompt = ADORATION_PROMPT
            schema = AdorationTimes
        if event in ["info"]:
            prompt = INFO_PROMPT
            schema = ParishInfo2

        print(event)
        response = extract_fn(client, prompt, schema, bulletin_md)

        if event in ["mass"]:
            response_masstimes = response.masses
        if event in ["conf"]:
            response_confessiontimes = response.confessions
        if event in ["adore"]:
            response_adorationtimes = response.adorations
        if event in ["info"]:
            response_info = response.metadata

    return (response_masstimes, response_confessiontimes, response_adorationtimes, response_info)

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
    from download_bulletins import download_bulletin

    with TemporaryFile("w+b") as bulletin_file:
        download_bulletin("our-lady-of-mount-carmel-wickliffe-oh", bulletin_file, "DM")
        bulletin_file.seek(0)

        # Use Ollama if configured, otherwise OpenAI
        if OLLAMA_BASE_URL:
            print(f"Using Ollama at {OLLAMA_BASE_URL} with model {OLLAMA_MODEL}")
            client = get_ollama_client()
        else:
            print("Using OpenAI")
            client = openai.Client()

        mass_times = get_times(client, ["mass"], bulletin_file)

        for mass_time in mass_times:
            print(mass_time)
