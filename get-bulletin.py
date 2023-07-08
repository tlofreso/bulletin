import httpx, json

urls = [
    "https://container.parishesonline.com/bulletins/14/0689/20230226B.pdf",
    "https://container.parishesonline.com/bulletins/14/0599/20230226B.pdf",
    "https://container.parishesonline.com/bulletins/14/0598/20230226B.pdf",
    "https://container.parishesonline.com/bulletins/14/0597/20230226B.pdf",
]

valid_urls = []


def get_urls():
    for url in urls:
        r = httpx.get(url)

        if r.headers["content-type"] == "application/pdf":
            valid_urls.append(url)

    return valid_urls


for id in range(4020, 9999):

    parish_id = str(id).zfill(4)
    url = f"https://container.parishesonline.com/bulletins/14/{parish_id}/20230226B.pdf"
    r = httpx.get(url)
    print("na " + url)

    if r.headers["content-type"] == "application/pdf":
        valid_urls.append(url)
        print(url)


with open("parish.json", "w") as outfile:
    json.dump(valid_urls, outfile)
