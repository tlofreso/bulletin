from datetime import datetime, timedelta
import httpx
from typing import IO

PARISHES_ONLINE_ROOT = "https://container.parishesonline.com/bulletins/14"
PARISHES_ONLINE_FILE_FORMAT = "%Y%m%dB.pdf"
DAYS_TO_LOOK_BEFORE_GIVING_UP = 30

def download_bulletin(parish_id:str, file:IO[bytes]):
    """
    Given a parishesonline parish ID in region 14, download the parish bulletin
    to the given file-like.  Return the URL the bulletin was found on.
    """

    # Search backwards in time until we find a bulletin
    current_date = datetime.now()
    success = False
    url = ""
    for i in range(30):
        if success:
            break

        date_to_check = current_date - timedelta(days=i)
        filename = date_to_check.strftime(PARISHES_ONLINE_FILE_FORMAT)
        url = f"{PARISHES_ONLINE_ROOT}/{parish_id}/{filename}"
        response = httpx.get(url)
        #print(url, response.status_code)
        if response.status_code != 200:
            continue

        #print(response.content)
        file.write(response.content)
        success = True

    if not success:
        raise Exception("No bulletin found")

    return url

if __name__ == "__main__":
    import tempfile

    #with open("test.pdf", "wb") as bulletin_file:
        #download_bulletin("0689", bulletin_file)


    with tempfile.TemporaryFile("w+b") as bulletin_file:
        download_bulletin("0689", bulletin_file)
        bulletin_file.seek(0)
        assert len(bulletin_file.read(10)) > 5