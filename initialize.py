import logging
import json
from api_utils import fetch_league_info, fetch_standings, fetch_league_seasons, fetch_league_image
from redis_utils import store_league_info, store_standings, store_league_image, store_league_seasons
from getters import get_league_info_from_db, get_standings, get_league_image_from_db, get_seasons, get_first_season_id


def initialize_leagues():
    """
    Initializes the leagues from settings.json, checks if they are in the database,
    and if not, fetches the league info, standings, and league image, then stores them.
    """
    with open('settings.json', 'r') as file:
        settings = json.load(file)

    leagues = settings.get('leagues', [])

    for league_id in leagues:
        # Check and fetch league info
        logging.info(f"Checking league {league_id}...")
        league_info = get_league_info_from_db(league_id)
        if not league_info:
            logging.info(f"Fetching league info for {league_id} from API.")
            league_info = fetch_league_info(league_id)
            if league_info:
                store_league_info(league_id, league_info)
            else:
                logging.warning(f"Failed to fetch league info for {league_id}")
                continue  # Skip this league if info could not be fetched

        # Check and fetch league seasons
        league_seasons = get_seasons(league_id)
        if not league_seasons:
            logging.info(f"Fetching seasons for league {league_id} from API.")
            league_seasons = fetch_league_seasons(league_id)
            if league_seasons:
                store_league_seasons(league_id, league_seasons)
            else:
                logging.warning(f"Failed to fetch seasons for {league_id}")
                continue  # Skip this league if seasons could not be fetched

        # Assuming you want to fetch standings for the latest season
        latest_season = get_first_season_id(league_id)
        if latest_season:
            standings = get_standings(league_id, latest_season)
            if not standings:
                logging.info(f"Fetching standings for league {league_id}, season {latest_season} from API.")
                standings = fetch_standings(league_id, latest_season)
                if standings:
                    store_standings(league_id, latest_season, standings)
                else:
                    logging.warning(f"Failed to fetch standings for league {league_id}, season {latest_season}")

        # Check and fetch league image
        league_image = get_league_image_from_db(league_id)
        if not league_image:
            logging.info(f"Fetching image for league {league_id} from API.")
            league_image = fetch_league_image(league_id)
            if league_image:
                store_league_image(league_id, league_image)
            else:
                logging.warning(f"Failed to fetch image for {league_id}")
