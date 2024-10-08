import json
import logging

from api_utils import fetch_league_info, fetch_league_seasons, fetch_league_image, fetch_standings
from redis_connection import r
from redis_utils import store_league_info, store_league_seasons, store_league_image, store_standings


import time

def init_leagues():
    with open('settings.json') as f:
        settings = json.load(f)

    leagues = settings.get('leagues', [])

    for league_id in leagues:
        info = r.get(f"league_info:{league_id}")
        if info:
            info = info.decode('utf-8')  # Decode the bytes object to a string
            info = json.loads(info)  # Convert the string back to a dictionary
            store_league_info(league_id, info)
        else:
            # If info is not in Redis, fetch it from the API
            info = fetch_league_info(league_id)
            if info:
                store_league_info(league_id, info)

        seasons = fetch_league_seasons(league_id)
        store_league_seasons(league_id, seasons)

        # Fetch and store standings for each season
        for season_id in seasons:
            while True:
                try:
                    standings_data = fetch_standings(league_id, season_id)
                    if standings_data:
                        store_standings(league_id, season_id, standings_data)
                    break
                except Exception as e:
                    if "404" in str(e):
                        logging.error(f"Error fetching standings for league {league_id} and season {season_id}: {e}")
                        break
                    elif "rate limit" in str(e):
                        logging.error(f"Rate limit exceeded. Waiting for 1 minute before retrying.")
                        time.sleep(60)
                    else:
                        logging.error(f"Error fetching standings for league {league_id} and season {season_id}: {e}")
                        break

        # Fetch and store league image
        while True:
            try:
                image_data = fetch_league_image(league_id)
                if image_data:
                    store_league_image(league_id, image_data)
                break
            except Exception as e:
                if "404" in str(e):
                    logging.error(f"Error fetching image for league {league_id}: {e}")
                    break
                elif "rate limit" in str(e):
                    logging.error(f"Rate limit exceeded. Waiting for 1 minute before retrying.")
                    time.sleep(60)
                else:
                    logging.error(f"Error fetching image for league {league_id}: {e}")
                    break

    return leagues