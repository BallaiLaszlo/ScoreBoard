import time

import redis
import json

# Connect to Redis
r = redis.Redis(
  host='redis-15767.c328.europe-west3-1.gce.redns.redis-cloud.com',
  port=15767,
  password='Qv4YUmGipTypX2Cc7fGScegE79UnIlBw')


def save_league_info_to_db(league_id, league_info, last_fetched):
    """
    Saves league information to the database.

    Args:
        league_id (str): The ID of the league.
        league_info (dict): The league information to store.
        last_fetched (float): The timestamp of when the league info was fetched.
    """
    # Convert league_info to JSON string if necessary
    league_info_json = json.dumps(league_info)

    # Save to Redis
    r.set(f"league_info:{league_id}", league_info_json)
    r.set(f"league_info_time:{league_id}", last_fetched)


def get_league_info_from_db(league_id):
    """
    Retrieves league information and last fetched time from the database.

    Args:
        league_id (str): The ID of the league.

    Returns:
        tuple: (league_info, last_fetched) where league_info is the league data
                and last_fetched is the timestamp of when it was fetched.
    """
    # Retrieve data from Redis
    league_info = r.get(f"league_info:{league_id}")
    last_fetched = r.get(f"league_info_time:{league_id}")

    if league_info:
        # Deserialize the league_info from JSON if necessary
        league_info = json.loads(league_info)

    # If last_fetched is None, you can set it to a default value like 0 or current time.
    last_fetched = float(last_fetched) if last_fetched else 0.0

    return league_info, last_fetched


def get_standings_from_db(league_id):
    """
    Retrieve standings for a given league from the database.

    Args:
        league_id (str): The ID of the league.

    Returns:
        tuple: The standings data and the timestamp of the last fetch.
    """
    standings_key = f"standings:{league_id}"
    timestamp_key = f"timestamp:{league_id}"

    standings_data = r.get(standings_key)
    last_fetched = r.get(timestamp_key)

    if standings_data:
        standings_data = json.loads(standings_data)

    return standings_data, float(last_fetched) if last_fetched else None


def store_standings_in_db(league_id, standings_data, last_fetched):
    """
    Stores standings information to the database.

    Args:
        league_id (str): The ID of the league.
        standings_data (dict): The standings data to store.
        last_fetched (float): The timestamp of when the standings data was fetched.
    """
    standings_data_json = json.dumps(standings_data)

    # Save standings data and last fetched time to Redis
    r.set(f"standings:{league_id}", standings_data_json)
    r.set(f"standings_time:{league_id}", last_fetched)


def get_league_image_from_db(league_id):
    """
    Retrieve league image from Redis by league ID.
    """
    image_key = f"league_image:{league_id}"
    if r.exists(image_key):
        return r.get(image_key)
    return None

def save_league_image_to_db(league_id, image_data):
    """
    Save league image in Redis.
    """
    image_key = f"league_image:{league_id}"
    r.set(image_key, image_data)
