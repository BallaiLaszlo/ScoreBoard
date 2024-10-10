import logging
from redis_connection import r

import json



def store_league_info(league_id, league_info, last_fetched = 0):
    """
    Saves league information to the database.

    Args:
        league_id (str): The ID of the league.
        league_info (dict): The league information to store.
        last_fetched (float): The timestamp of when the league info was fetched.
    """
    # Convert league_info to JSON string if necessary
    if isinstance(league_info, dict):
        league_info = json.dumps(league_info)
    r.set(f"league_info:{league_id}", league_info)
    r.set(f"league_info_time:{league_id}", last_fetched)


def store_standings(league_id, season_id, standings_data, last_fetched=0):
    """
    Stores the standings for a given league and season in the database.

    Args:
        league_id (str): The ID of the league.
        season_id (str): The ID of the season.
        standings_data (dict): The standings data to store.
        last_fetched (float): The last fetched time.
    """
    r.set(f"standings:{league_id}:{season_id}", json.dumps(standings_data))
    r.set(f"standings_time:{league_id}:{season_id}", last_fetched)
    logging.info(f"Standings for league ID {league_id} and season ID {season_id} stored in the database.")


def store_league_image(league_id, image_data):
    """
    Save league image in Redis.
    """
    image_key = f"league_image:{league_id}"
    r.set(image_key, image_data)


def store_league_seasons(league_id, seasons):
    """
    Store the seasons data in Redis with the key of the league ID.
    """
    r.set(f"league:{league_id}:seasons", json.dumps(seasons))

#store_standings("8",61643,fetch_standings("8","61643"))
#store_league_info("8",fetch_league_info("8"))
#store_league_image("8",fetch_league_image("8"))
#store_league_seasons("8",fetch_league_seasons(8))