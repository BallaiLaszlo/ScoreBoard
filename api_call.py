import json
import logging

import requests

with open('settings.json', 'r') as f:
    settings = json.load(f)


api_key = settings["api_key"]
api_host = "footapi7.p.rapidapi.com"
def make_api_request(url):
    """
    General request handler to make API calls.
    """
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': api_host
    }
    response = requests.get(url, headers=headers)
    logging.info(f"API response for {url}: {response.text}")

    if response.status_code == 429:
        print("Error: You have exceeded the number of allowed requests. Please try again later.")
        return None
    elif response.status_code != 200:
        print(f"Error: Unable to fetch data (Status Code: {response.status_code})")
        return None

    if "application/json" in response.headers.get("Content-Type", ""):
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            print("Error: Failed to parse JSON response.")
            return None
    else:
        return response.content  # Return raw content for non-JSON data

