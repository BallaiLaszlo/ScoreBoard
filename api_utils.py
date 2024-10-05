import requests
import json
from redis_utils import get_league_info_from_db, save_league_info_to_db, get_standings_from_db, save_standings_to_db, \
    get_league_image_from_db, save_league_image_to_db

# Load settings
with open('settings.json', 'r') as f:
    settings = json.load(f)

api_key = settings["api_key"]
api_host = "footapi7.p.rapidapi.com"

# Extract leagues from settings
leagues = settings["leagues"]

# Create a dictionary for league ID lookup
league_id_lookup = {league['name']: league['id'] for league in leagues}


def make_api_request(url):
    """
    General request handler to make API calls.
    """
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

    if "application/json" in response.headers.get("Content-Type", ""):
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            print("Error: Failed to parse JSON response.")
            return None
    else:
        return response.content  # Return raw content for non-JSON data


def fetch_league_info(league_id):
    """
    Fetches league information based on league ID.

    Args:
        league_id (str): The ID of the league.

    Returns:
        dict: The league information.
    """
    # Check in the database first
    league_info = get_league_info_from_db(league_id)

    if league_info is None:
        # If not found, fetch from the API
        league_info = make_api_request(f"https://{api_host}/api/tournament/{league_id}")
        if league_info:
            # Save to the database
            save_league_info_to_db(league_id, league_info)

    return league_info


def get_first_season_id(league_name):
    """
    Retrieves the first season ID for a given league name.
    """
    league = next((league for league in leagues if league['name'] == league_name), None)
    return league['seasons'][0] if league and 'seasons' in league and league['seasons'] else None


def fetch_standings(league_id, season_id):
    """
    Fetches league standings based on league ID and season ID, with Redis caching.
    """
    standings = get_standings_from_db(league_id, season_id)
    if standings:
        return standings

    url = f"https://{api_host}/api/tournament/{league_id}/season/{season_id}/standings/total"
    standings = make_api_request(url)

    if standings:
        save_standings_to_db(league_id, season_id, standings)

    return standings


def fetch_league_image(league_id):
    """
    Fetches the league image based on league ID, with Redis caching.
    """
    image_data = get_league_image_from_db(league_id)
    if image_data:
        return image_data

    url = f"https://{api_host}/api/tournament/{league_id}/image"
    image_data = make_api_request(url)

    if image_data:
        save_league_image_to_db(league_id, image_data)

    return image_data


def get_league_names():
    """
    Retrieves the names of all leagues from the settings.
    """
    return [league['name'] for league in leagues]


def get_league_id(league_name):
    """
    Retrieves the league ID based on the league name.
    """
    return league_id_lookup.get(league_name)
