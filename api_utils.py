from io import BytesIO
from PIL import Image
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


# Fetch league image
def fetch_league_image(league_id):
    url = f"https://{api_host}/api/tournament/{league_id}/image"
    response = make_api_request(url)

    if response:
        return response.content  # Return the raw image data
    return None


# Fetch teams for a league
def fetch_teams(league_id):
    url = f"https://sportapi7.p.rapidapi.com/api/v1/teams?league_id={league_id}"
    data = make_api_request(url)

    if data:
        return data.get('teams', [])
    return []


# Fetch matches for a team
def fetch_matches(team_id):
    url = f"https://sportapi7.p.rapidapi.com/api/v1/matches?team_id={team_id}"
    data = make_api_request(url)

    if data:
        return data.get('matches', [])
    return []


# Fetch seasons for a league and add to settings.json
def fetch_league_seasons(league_id, league_name):
    url = f"https://{api_host}/api/tournament/{league_id}/seasons"
    data = make_api_request(url)

    if data and 'seasons' in data:
        seasons = [season['id'] for season in data['seasons']]
        return seasons
    else:
        print(f"No seasons found for league {league_name}")
        return ["No seasons available"]


# Update settings.json with league seasons
def update_settings_with_seasons():
    for league in leagues:
        league_name = league['name']
        league_id = league['id']
        print(f"Fetching seasons for league: {league_name} (ID: {league_id})")

        seasons = fetch_league_seasons(league_id, league_name)
        league['seasons'] = seasons

    # Save updated settings back to settings.json
    with open('settings.json', 'w') as f:
        json.dump(settings, f, indent=4)

    print("settings.json updated with seasons.")


# Helper functions to get league names and IDs
def get_league_names():
    return [league['name'] for league in leagues]


def get_league_id(league_name):
    return league_id_lookup.get(league_name)

update_settings_with_seasons()