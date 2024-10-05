import redis
import json

# Connect to Redis
r = redis.Redis(
  host='redis-15767.c328.europe-west3-1.gce.redns.redis-cloud.com',
  port=15767,
  password='Qv4YUmGipTypX2Cc7fGScegE79UnIlBw')


def save_league_info_to_db(league_id, league_info):
    """
    Saves league information to Redis.

    Args:
        league_id (str): The ID of the league.
        league_info (dict): The league information to be saved.
    """
    league_key = f"league:{league_id}"
    # Store league info as a JSON string
    r.set(league_key, json.dumps(league_info))


def get_league_info_from_db(league_id):
    """
    Retrieves league information from Redis.

    Args:
        league_id (str): The ID of the league.

    Returns:
        dict or None: The league information if found, otherwise None.
    """
    league_key = f"league:{league_id}"
    league_info = r.get(league_key)

    if league_info:
        # Parse the JSON string back to a dictionary
        return json.loads(league_info)

    return None

def get_standings_from_db(league_id, season_id):
    """
    Retrieve standings from Redis by league and season ID.
    """
    standings_key = f"standings:{league_id}:{season_id}"
    if r.exists(standings_key):
        standings = r.get(standings_key)
        return json.loads(standings)
    return None

def save_standings_to_db(league_id, season_id, standings):
    """
    Save standings in Redis.
    """
    standings_key = f"standings:{league_id}:{season_id}"
    r.set(standings_key, json.dumps(standings))

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
