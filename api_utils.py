import logging
import time

import requests
import json

from api_call import *
from getters import *

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


    return league_info

FETCH_INTERVAL = 12 * 60 * 60  # 12 hours


def fetch_standings(league_id, season_id):
    """
    Fetches league standings based on league ID and season ID,
    checking the database for a recent fetch first.

    Args:
        league_id (str): The ID of the league.
        season_id (str): The ID of the season.

    Returns:
        dict: The standings information.
    """
    standings_data = get_standings(league_id, season_id)
    last_fetched = 0
    current_time = time.time()

    if standings_data and (current_time - last_fetched < FETCH_INTERVAL):
        logging.info(f"Standings for league ID {league_id} and season ID {season_id} retrieved from database.")
        return standings_data  # Return the cached standings

    logging.info(f"Fetching standings for league ID {league_id} and season ID {season_id} from API.")
    url = f"https://{api_host}/api/tournament/{league_id}/season/{season_id}/standings/total"
    standings_data = make_api_request(url)

    return standings_data

def fetch_league_image(league_id):
    """
    Fetches the league image based on league ID, with Redis caching.
    """
    image_data = get_league_image_from_db(league_id)
    if image_data:
        return image_data

    url = f"https://{api_host}/api/tournament/{league_id}/image"
    image_data = make_api_request(url)

    return image_data

# api_utils.py
def fetch_league_seasons(league_id):
    url = f"https://{api_host}/api/tournament/{league_id}/seasons"
    response = make_api_request(url)
    if response:
        seasons = response.get('seasons', [])
        if seasons:
            logging.info(f"Seasons data for league {league_id}: {seasons}")
            return seasons
        else:
            logging.warning(f"No seasons data found for league {league_id}")
    return []


#print(fetch_league_seasons("8"))
#print(fetch_league_image("8"))
#print(fetch_standings("8","61643"))
#print(fetch_league_info("8"))