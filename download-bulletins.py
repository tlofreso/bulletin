import json
import os
import requests

# Load the data from the JSON file
with open("processed_parish.json", "r") as file:
    data = json.load(file)

# Create the 'bulletins' directory if it doesn't exist
os.makedirs('bulletins', exist_ok=True)

# Download the files
for item in data:
    url = item['bulletinUrlStem'] + "20230709B.pdf"
    response = requests.get(url)

    # Extract the numbers from the URL and use them to create a filename
    numbers = url.split('/')[-3:-1]
    filename = '-'.join(numbers) + "-20230709B.pdf"
    path = os.path.join('bulletins', filename)

    print(path)

    with open(path, 'wb') as file:
        file.write(response.content)

