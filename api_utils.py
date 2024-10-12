import logging
import json
from api_call import *  # Assuming you have this to make API requests
from getters import *  # Assuming these are your data retrieval functions
from redis_utils import store_standings  # For storing standings in Redis


logging.basicConfig(
    filename='log.txt',  # Log file name
    level=logging.INFO,  # Log level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log message format
)


def fetch_league_info(league_id):
    """
    Fetches league information based on league ID.

    Args:
        league_id (str): The ID of the league.

    Returns:
        dict: The league information.
    """
    league_info = get_league_info_from_db(league_id)

    if league_info:
        logging.info(f"League info for ID {league_id} retrieved from database.")
        return league_info  # Return the info from the database

    logging.info(f"Fetching league info for ID {league_id} from API.")
    url = f"https://{api_host}/api/tournament/{league_id}"
    league_info = make_api_request(url)

    if league_info:
        logging.info(f"League info for ID {league_id} successfully fetched from API.")
    else:
        logging.error(f"Failed to fetch league info for ID {league_id} from API.")

    return league_info


def fetch_standings(league_id, season_id):
    """
    Fetches league standings based on league ID and season ID.
    First checks the database for cached standings.

    Args:
        league_id (str): The ID of the league.
        season_id (str): The ID of the season.

    Returns:
        dict: The standings information.
    """
    standings_data = get_standings(league_id, season_id)
    if standings_data:
        logging.info(f"Standings for league ID {league_id} and season ID {season_id} retrieved from database.")
        return standings_data  # Return cached standings

    # If data is not found, fetch from API
    logging.info(f"Fetching standings for league ID {league_id} and season ID {season_id} from API.")
    url = f"https://{api_host}/api/tournament/{league_id}/season/{season_id}/standings/total"
    standings_data = make_api_request(url)

    if standings_data:
        # Store the new standings data in the database
        store_standings(league_id, season_id, standings_data)
        logging.info(f"Standings for league ID {league_id} and season ID {season_id} successfully fetched and stored.")
    else:
        logging.error(f"Failed to fetch standings for league ID {league_id} and season ID {season_id} from API.")

    return standings_data


def fetch_league_image(league_id):
    """
    Fetches the league image based on league ID, with Redis caching.
    """
    image_data = get_league_image_from_db(league_id)
    if image_data:
        logging.info(f"Image for league ID {league_id} retrieved from database.")
        return image_data

    logging.info(f"Fetching league image for ID {league_id} from API.")
    url = f"https://{api_host}/api/tournament/{league_id}/image"
    image_data = make_api_request(url)

    if image_data:
        logging.info(f"League image for ID {league_id} successfully fetched from API.")
    else:
        logging.error(f"Failed to fetch league image for ID {league_id} from API.")

    return image_data


def fetch_league_seasons(league_id):
    """
    Fetches league seasons based on league ID.

    Args:
        league_id (str): The ID of the league.

    Returns:
        list: A list of seasons for the specified league.
    """
    logging.info(f"Fetching seasons data for league ID {league_id} from API.")
    url = f"https://{api_host}/api/tournament/{league_id}/seasons"
    response = make_api_request(url)

    if response:
        seasons = response.get('seasons', [])
        if seasons:
            logging.info(f"Seasons data for league {league_id}: {seasons}")
            return seasons
        else:
            logging.warning(f"No seasons data found for league ID {league_id}")
    else:
        logging.error(f"Failed to fetch seasons data for league ID {league_id} from API.")

    return []

def fetch_team_info(team_id):
    """
    Fetches team information based on team ID.

    Args:
        team_id (str): The ID of the team.

    Returns:
        dict: The team information.
    """
    team_info = get_team_info(team_id)  # Check if info exists in the database

    if team_info:
        logging.info(f"Team info for ID {team_id} retrieved from database.")
        return team_info  # Return the info from the database

    logging.info(f"Fetching team info for ID {team_id} from API.")
    url = f"https://{api_host}/api/team/{team_id}"
    team_info = make_api_request(url)

    if team_info:
        logging.info(f"Team info for ID {team_id} successfully fetched from API.")
    else:
        logging.error(f"Failed to fetch team info for ID {team_id} from API.")

    return team_info


# Example usage
#logging.info("Fetching standings, league info, and league seasons for league ID '187'.")
#print(fetch_standings("187", "61714"))
#print(fetch_league_info("187"))
#print(fetch_league_seasons("187"))
#print(fetch_team_info("2820"))