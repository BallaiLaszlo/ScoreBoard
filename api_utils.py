import requests
import json

# Load settings
with open('settings.json', 'r') as f:
    settings = json.load(f)

api_key = settings["api_key"]
api_host = "footapi7.p.rapidapi.com"

# Extract leagues from settings
leagues = settings["leagues"]

# Create a dictionary for league ID lookup
league_id_lookup = {league['name']: league['id'] for league in leagues}


# General request handler
def make_api_request(url):
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': api_host
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 429:
        print("Error: You have exceeded the number of allowed requests. Please try again later.")
        return None
    elif response.status_code != 200:
        print(f"Error: Unable to fetch data (Status Code: {response.status_code})")
        return None

    return response.json()


# Fetch league information
def fetch_league_info(league_id):
    url = f"https://{api_host}/api/tournament/{league_id}"
    return make_api_request(url)

# General request handler
def make_api_request(url):
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': api_host
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 429:
        print("Error: You have exceeded the number of allowed requests. Please try again later.")
        return None
    elif response.status_code != 200:
        print(f"Error: Unable to fetch data (Status Code: {response.status_code})")
        return None

    # Check if content-type is application/json before trying to parse JSON
    if "application/json" in response.headers.get("Content-Type", ""):
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            print("Error: Failed to parse JSON response.")
            return None
    else:
        return response.content  # Return raw content (useful for images or non-JSON data)

# Fetch league image
def fetch_league_image(league_id):
    url = f"https://{api_host}/api/tournament/{league_id}/image"
    response = make_api_request(url)

    if response:  # Response could be None or empty
        return response  # Return the raw image data
    return None  # Return None if no data is available


# Fetch standings based on the league_id
def fetch_standings(league_id):
    url = f"https://{api_host}/api/tournament/{league_id}/standings/total"
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": api_host
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()  # Return the JSON response if successful
    else:
        print("Failed to retrieve standings")
        return None


# Helper functions to get league names and IDs
def get_league_names():
    return [league['name'] for league in leagues]


def get_league_id(league_name):
    return league_id_lookup.get(league_name)