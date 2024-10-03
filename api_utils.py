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

def make_api_request(url):
    """
    General request handler to make API calls.

    Args:
        url (str): The URL to send the request to.

    Returns:
        dict or bytes: The JSON response data if available, otherwise raw content.
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
    url = f"https://{api_host}/api/tournament/{league_id}"
    return make_api_request(url)

def get_first_season_id(league_name):
    """
    Retrieves the first season ID for a given league name.

    Args:
        league_name (str): The name of the league.

    Returns:
        str or None: The first season ID if available, otherwise None.
    """
    league = next((league for league in leagues if league['name'] == league_name), None)
    return league['seasons'][0] if league and 'seasons' in league and league['seasons'] else None

def fetch_standings(league_id, season_id):
    """
    Fetches league standings based on league ID and season ID.

    Args:
        league_id (str): The ID of the league.
        season_id (str): The ID of the season.

    Returns:
        dict: The standings information.
    """
    url = f"https://{api_host}/api/tournament/{league_id}/season/{season_id}/standings/total"
    return make_api_request(url)

def fetch_league_image(league_id):
    """
    Fetches the league image based on league ID.

    Args:
        league_id (str): The ID of the league.

    Returns:
        bytes or None: The image data if available, otherwise None.
    """
    url = f"https://{api_host}/api/tournament/{league_id}/image"
    return make_api_request(url)

def get_league_names():
    """
    Retrieves the names of all leagues from the settings.

    Returns:
        list: A list of league names.
    """
    return [league['name'] for league in leagues]

def get_league_id(league_name):
    """
    Retrieves the league ID based on the league name.

    Args:
        league_name (str): The name of the league.

    Returns:
        str or None: The ID of the league if found, otherwise None.
    """
    return league_id_lookup.get(league_name)
