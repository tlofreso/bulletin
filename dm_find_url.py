import urllib.request
from bs4 import BeautifulSoup
import argparse

def listen_for_arguments(): #This is defunct - not used
    parser = argparse.ArgumentParser(description='Return the URL for the most recent bulletin.')
    parser.add_argument('parish_name', nargs='*', help='Name of the parish from its permalink URL: e.g. st-isidore-kingston')
    return parser.parse_args()
#args = listen_for_arguments()

def get_dm_url(name:str):
    if name:
    #    print("success")
    #    print(args.parish_name[0])
        url = "https://discovermass.com/church/" + name + "/#bulletins"
        req = urllib.request.Request(
            url,
            data=None,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
            }
        )
        rawdata = urllib.request.urlopen(req)
    # rawdata = open("test.html", "r")
        html = rawdata.read().decode('utf-8')
        soup = BeautifulSoup(html, "html.parser")
        bulletin = soup.find(id="bulletin-current")
        bulletin_link = bulletin.get('href')
        bulletin_date = bulletin.get_text()

    #    print('This bulletin is from ' + bulletin_date + "\n")
        return(bulletin_link)

    else:
        raise Exception("Enter a parish name and try again")