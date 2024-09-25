from io import BytesIO
from PIL import Image
import requests
import json

# Load settings
with open('settings.json') as f:
    settings = json.load(f)

api_key = settings["api_key"]
api_host = "footapi7.p.rapidapi.com"

# Extract leagues from settings
leagues = settings["leagues"]

# Create a dictionary for league ID lookup
league_id_lookup = {league['name']: league['id'] for league in leagues}


def fetch_league_info(league_id):
    url = f"https://footapi7.p.rapidapi.com/api/tournament/{league_id}"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': api_host
    }
    response = requests.get(url, headers=headers)

    # Check for rate limit exceeded or other errors
    if response.status_code == 429:
        print("Error: You have exceeded the number of allowed requests. Please try again later.")
        return {}
    elif response.status_code != 200:
        print(f"Error: Unable to fetch league info (Status Code: {response.status_code})")
        return {}

    return response.json()


def fetch_league_image(league_id):
    url = f"https://footapi7.p.rapidapi.com/api/tournament/{league_id}/image"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': api_host
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 429:
        print("Error: You have exceeded the number of allowed requests. Please try again later.")
        return None
    elif response.status_code != 200:
        print(f"Error: Unable to fetch league image (Status Code: {response.status_code})")
        return None

    return response.content  # Return the raw image data


def fetch_teams(league_id):
    url = f"https://sportapi7.p.rapidapi.com/api/v1/teams?league_id={league_id}"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': api_host
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 429:
        print("Error: You have exceeded the number of allowed requests. Please try again later.")
        return []
    elif response.status_code != 200:
        print(f"Error: Unable to fetch teams (Status Code: {response.status_code})")
        return []

    return response.json().get('teams', [])


def fetch_matches(team_id):
    url = f"https://sportapi7.p.rapidapi.com/api/v1/matches?team_id={team_id}"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': api_host
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 429:
        print("Error: You have exceeded the number of allowed requests. Please try again later.")
        return []
    elif response.status_code != 200:
        print(f"Error: Unable to fetch matches (Status Code: {response.status_code})")
        return []

    return response.json().get('matches', [])


def get_league_names():
    return [league['name'] for league in leagues]


def get_league_id(league_name):
    return league_id_lookup.get(league_name)

