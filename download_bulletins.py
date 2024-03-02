from datetime import datetime, timedelta
import httpx
from typing import IO
from dm_find_url import get_dm_url

PARISHES_ONLINE_ROOT = "https://container.parishesonline.com/bulletins/14"
PARISHES_ONLINE_FILE_FORMAT = "%Y%m%dB.pdf"
ECATHOLIC_ONLINE_ROOT = "https://files.ecatholic.com"
ECATHOLIC_ONLINE_FILE_FORMAT = "%Y%m%d.pdf"
DAYS_TO_LOOK_BEFORE_GIVING_UP = 30

def download_bulletin(parish_id:str, file:IO[bytes], publisher_type="PO"):
    """
    For Discover Mass:      Given a parish permalink, download the parish bulletin
    For Parishes Online:    Given a parishesonline parish ID in region 14, download the parish bulletin
    For eCatholic:          Given an eCatholic parish ID, download the parish bulletin
    """

    # Search backwards in time until we find a bulletin
    current_date = datetime.now()
    success = False
    if publisher_type == "DM":
        url = get_dm_url(parish_id)
        response = httpx.get(url)
    for i in range(30):
        if success:
            break

        date_to_check = current_date - timedelta(days=i)
        if publisher_type == "PO": 
            filename = date_to_check.strftime(PARISHES_ONLINE_FILE_FORMAT)
            url = f"{PARISHES_ONLINE_ROOT}/{parish_id}/{filename}"
            response = httpx.get(url)
        if publisher_type == "EC":
            filename = date_to_check.strftime(ECATHOLIC_ONLINE_FILE_FORMAT)
            url = f"{ECATHOLIC_ONLINE_ROOT}/{parish_id}/bulletins/{filename}"
            response = httpx.get(url)
        #print(url, response.status_code)
        if response.status_code != 200:
            continue
        if response.status_code == 200:
            file.write(response.content)
            success = True
            break
        #print(response.content)

    if not success:
        raise Exception("No bulletin found")

    return url

if __name__ == "__main__":
    import tempfile

#    with open("test.pdf", "wb") as bulletin_file:
#        download_bulletin("st-james-the-less-columbus-oh", bulletin_file, "DM")

    with tempfile.TemporaryFile("w+b") as bulletin_file:
        download_bulletin("0689", bulletin_file)
        bulletin_file.seek(0)
        assert len(bulletin_file.read(10)) > 5