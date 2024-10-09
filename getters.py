import json
from datetime import time

import redis
from redis import Redis
from redis_connection import r

with open('settings.json', 'r') as f:
    settings = json.load(f)

leagues = settings["leagues"]

def get_league_names(league_id):
    league_info = r.get(f"league_info:{league_id}")
    if league_info:
        league_info_dict = json.loads(league_info.decode('utf-8'))
        return league_info_dict
    return None

def get_league_name_list():
    league_name_list = []
    for league_id in leagues:
        league_info_dict = get_league_names(league_id)
        if league_info_dict:
            unique_tournament = league_info_dict.get('uniqueTournament', {})
            league_name = unique_tournament.get('name')
            if league_name:
                league_name_list.append((league_id, league_name))
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
        return season_ids
    return None

def get_first_season_id(league_id):
    """
    Retrieve the first season ID from Redis.
    """
    temp = get_seasons(league_id)
    if temp:
        return temp[0]
    return None

def get_league_image_from_db(league_id):
    """
    Retrieve league image from Redis by league ID.
    """
    image_key = f"league_image:{league_id}"
    if r.exists(image_key):
        return r.get(image_key)
    return None

def get_standings(league_id, season_id):
    key = f"standings:{league_id}:{season_id}"
    standings = r.get(key)
    if standings:
        standings_dict = json.loads(standings.decode('utf-8'))
        return standings_dict
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
    key = f"last_fetched:{league_id}:{season_id}"
    last_fetched = r.get(key)
    if last_fetched:
        return float(last_fetched.decode('utf-8'))
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
