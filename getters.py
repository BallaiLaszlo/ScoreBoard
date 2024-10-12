import json
import logging
from datetime import time
import redis
from redis import Redis
from redis_connection import r


logging.basicConfig(
    filename='log.txt',  # Log file name
    level=logging.INFO,  # Log level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log message format
)

with open('settings.json', 'r') as f:
    settings = json.load(f)

leagues = settings["leagues"]

def get_league_names(league_id):
    """
    Retrieve league information from Redis by league ID.
    """
    league_info = r.get(f"league_info:{league_id}")
    if league_info:
        league_info_dict = json.loads(league_info.decode('utf-8'))
        logging.info(f"Retrieved league info for league ID {league_id}.")
        return league_info_dict
    logging.warning(f"No league info found for league ID {league_id}.")
    return None

def get_league_name_list():
    """
    Get a list of league IDs and names.
    """
    league_name_list = []
    for league_id in leagues:
        league_info_dict = get_league_names(league_id)
        if league_info_dict:
            unique_tournament = league_info_dict.get('uniqueTournament', {})
            league_name = unique_tournament.get('name')
            if league_name:
                league_name_list.append((league_id, league_name))
                logging.info(f"Added league ID {league_id} with name '{league_name}' to the league name list.")
            else:
                logging.warning(f"No name found for league ID {league_id}.")
        else:
            logging.warning(f"League info not found for league ID {league_id}.")
    return league_name_list

def get_seasons(league_id):
    """
    Retrieves the seasons of a league from the database.

    Args:
        league_id (str): The ID of the league.

    Returns:
        list: The season IDs of the league.
    """
    seasons_key = f"league:{league_id}:seasons"
    seasons_data = r.get(seasons_key)
    if seasons_data:
        seasons_list = json.loads(seasons_data)
        season_ids = [season['id'] for season in seasons_list]
        logging.info(f"Retrieved seasons for league ID {league_id}: {season_ids}.")
        return season_ids
    logging.warning(f"No seasons found for league ID {league_id}.")
    return None

def get_first_season_id(league_id):
    """
    Retrieve the first season ID from Redis.
    """
    temp = get_seasons(league_id)
    if temp:
        logging.info(f"First season ID for league ID {league_id} is {temp[0]}.")
        return temp[0]
    logging.warning(f"No seasons available to retrieve first season ID for league ID {league_id}.")
    return None

def get_league_image_from_db(league_id):
    """
    Retrieve league image from Redis by league ID.
    """
    image_key = f"league_image:{league_id}"
    if r.exists(image_key):
        image = r.get(image_key)
        logging.info(f"Retrieved image for league ID {league_id}.")
        return image
    logging.warning(f"No image found for league ID {league_id}.")
    return None

def get_standings(league_id, season_id):
    """
    Retrieve standings for a specific league and season from Redis.
    """
    key = f"standings:{league_id}:{season_id}"
    standings = r.get(key)
    if standings:
        standings_dict = json.loads(standings.decode('utf-8'))
        logging.info(f"Retrieved standings for league ID {league_id}, season ID {season_id}.")
        return standings_dict
    logging.warning(f"No standings found for league ID {league_id}, season ID {season_id}.")
    return None

def get_league_info_from_db(league_id):
    """
    Retrieves league information from the database using the league ID.

    Args:
        league_id (str): The ID of the league.

    Returns:
        str: The league name, or None if not found.
    """
    league_info = r.get(f"league_info:{league_id}")
    if league_info:
        logging.info(f"Retrieved league info for league ID {league_id}.")
    else:
        logging.warning(f"No league info found for league ID {league_id}.")
    return league_info

def get_last_fetched_time(league_id, season_id):
    """
    Retrieves the last fetched time for standings from Redis.

    Args:
        league_id (str): The ID of the league.
        season_id (str): The ID of the season.

    Returns:
        float: The last fetched time in seconds since epoch, or None if not found.
    """
    key = f"standings_time:{league_id}:{season_id}"
    last_fetched = r.get(key)
    if last_fetched:
        logging.info(f"Retrieved last fetched time for league ID {league_id}, season ID {season_id}.")
        return float(last_fetched.decode('utf-8'))
    logging.warning(f"No last fetched time found for league ID {league_id}, season ID {season_id}.")
    return None


def delete_standings(league_id):
    """
    Deletes the standings data for the given league from the Redis database.

    Args:
        league_id (str): The ID of the league whose standings will be deleted.
    """
    try:
        redis_key = f"standings:{league_id}"
        if r.exists(redis_key):
            r.delete(redis_key)
            logging.info(f"Deleted standings for league {league_id} from Redis.")
        else:
            logging.warning(f"No standings found for league {league_id} in Redis.")
    except Exception as e:
        logging.error(f"Error deleting standings for league {league_id}: {e}")


def get_team_info(team_id):
    """
    Retrieves the team information from the database.

    Args:
        team_id (str): The ID of the team.

    Returns:
        dict: The team information including name, location, manager, venue, country, etc.
    """
    # Fetch the team info as a string from Redis
    team_info = r.get(f"team_info:{team_id}")

    if team_info:
        # Log the raw data for debugging
        logging.info(f"Raw team info retrieved for team ID {team_id}: {team_info}")

        # Parse the string into a dictionary (since it's stored as a JSON string)
        try:
            team_info = json.loads(team_info)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON for team ID {team_id}: {e}")
            return None

        # Log the parsed data
        logging.info(f"Parsed team info for team ID {team_id}: {team_info}")

        # Accessing the nested structure to get the required fields
        team = team_info.get('team', {})
        team_name = team.get('name', 'Unknown')
        manager_name = team.get('manager', {}).get('name', 'Unknown')
        venue = team.get('venue', {}).get('name', 'Unknown')
        venue_capacity = team.get('venue', {}).get('capacity', 'Unknown')

        # Extracting country and location from the venue's city
        venue_city = team.get('venue', {}).get('city', {}).get('name', 'Unknown')
        country_name = team.get('country', {}).get('name', 'Unknown')

        # Extracting team colors
        team_colors = team.get('teamColors', {})
        primary_color = team_colors.get('primary', 'Unknown')
        secondary_color = team_colors.get('secondary', 'Unknown')
        text_color = team_colors.get('text', 'Unknown')

        # Return the relevant details including location and country
        return {
            'name': team_name,
            'manager': manager_name,
            'venue': venue,
            'venue_capacity': venue_capacity,
            'location': venue_city,
            'country': country_name,
            'team_colors': {
                'primary': primary_color,
                'secondary': secondary_color,
                'text': text_color
            }
        }
    else:
        logging.warning(f"No team info found for team ID {team_id}.")
        return None


def get_team_id_from_standings(standings, team_name):
    """
    Retrieves the team ID for a specific team from the standings data.

    Args:
        standings (dict): The standings data.
        team_name (str): The name of the team to find.

    Returns:
        int: The ID of the team if found, otherwise None.
    """
    # Iterate through the standings rows to find the team by its name
    for row in standings.get('standings', [])[0].get('rows', []):
        team = row.get('team', {})
        if team.get('name') == team_name:
            return team.get('id')

    logging.warning(f"No team ID found for team name {team_name}")
    return None

def get_team_scores(response):
    """
    Extract team scores from the API response and return the entire response.
    """
    try:
        # Log the raw response for debugging
        logging.info(f"Raw API response: {response}")

        # If you want to extract specific data later, you can still do so
        team_scores = response.get('matches', [])  # Adjust according to the actual structure of your response

        # Log the team scores for debugging
        logging.info(f"Extracted team scores: {team_scores}")

        # Return the entire response for further processing
        return response
    except Exception as e:
        logging.error(f"Error extracting team scores: {e}")
        return None

# Example usage
#print(leagues)
#print(get_league_names(leagues))
#print(get_seasons("8"))
#print(get_first_season_id("8"))
#print(get_league_image_from_db("8"))
#print(get_standings("8","61643"))
#print(get_standings("8", get_first_season_id("8")))
#print(get_league_info_from_db("8"))
#print(get_league_names("8"))
#print(get_league_name_list())
#print(get_team_info("17"))
