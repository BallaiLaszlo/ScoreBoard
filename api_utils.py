import logging
import json
from api_call import *
from getters import get_league_info_from_db, get_standings, get_league_image_from_db, get_team_info, \
    get_previous_matches, format_last_three_matches, get_next_three_matches, get_league_season_info
from redis_connection import r
from redis_utils import store_standings, store_last_three_matches, store_next_three_matches, store_league_season_info

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


def fetch_previous_matches(team_id):
    """
    Fetches previous matches for a team based on team ID, with Redis caching.
    """
    # Check if matches exist in the Redis database
    cached_matches = r.get(f'team_previous_matches:{team_id}')

    if cached_matches:
        logging.info(f"Previous matches for team ID {team_id} retrieved from database.")
        return json.loads(cached_matches)  # Return matches from Redis

    logging.info(f"Fetching previous matches for team ID {team_id} from API.")
    url = f"https://{api_host}/api/team/{team_id}/matches/previous/1"

    previous_matches = make_api_request(url)

    # Log the raw response from the API
    logging.info(f"Raw API response for team ID {team_id}: {previous_matches}")

    if previous_matches:
        logging.info(f"Previous matches for team ID {team_id} successfully fetched from API.")
        # Cache the fetched matches in Redis for future use
        r.set(f'team_previous_matches:{team_id}', json.dumps(previous_matches))  # Store in Redis
    else:
        logging.warning(f"No previous matches found for team ID {team_id}.")
        return []  # Return an empty list if no matches found

    return previous_matches  # Return the fetched matches


def fetch_and_store_upcoming_matches(team_id):
    """
    Fetches upcoming matches for a team and stores them in Redis.

    Args:
        team_id (str): The ID of the team.

    Returns:
        list: A list of the next three matches.
    """
    logging.info(f"Fetching upcoming matches for team ID {team_id}")
    try:
        url = f"https://api.sofascore.com/api/v1/team/{team_id}/events/next/0"
        response = make_api_request(url)

        if not response:
            logging.error(f"No response received for team ID {team_id}")
            return []

        events = response.get('events', [])
        logging.info(f"Received {len(events)} events for team ID {team_id}")

        next_three_matches = []
        for event in events[:3]:
            match_info = {
                'match_id': event['id'],
                'tournament_name': event['tournament']['name'],
                'home_team': event['homeTeam']['name'],
                'away_team': event['awayTeam']['name'],
                'home_team_id': event['homeTeam']['id'],
                'away_team_id': event['awayTeam']['id'],
                'status': event['status']['description'],
                'start_timestamp': event['startTimestamp']
            }
            next_three_matches.append(match_info)
            logging.info(f"Processed match: {match_info}")

        # Store in Redis
        if next_three_matches:
            redis_key = f'team_next_matches:{team_id}'
            r.set(redis_key, json.dumps(next_three_matches))
            logging.info(f"Stored {len(next_three_matches)} matches for team ID {team_id} in Redis")
        else:
            logging.warning(f"No upcoming matches found for team ID {team_id}")

        return next_three_matches

    except Exception as e:
        logging.error(f"Error in fetch_and_store_upcoming_matches for team ID {team_id}: {str(e)}")
        return []


def fetch_and_store_match_details(match_id):
    """
    Fetches match details from the API and stores them in Redis.

    Args:
        match_id (str): The ID of the match.

    Returns:
        dict: The match details if successful, None otherwise.
    """
    logging.info(f"Fetching match details for match ID: {match_id}")

    # Check if match details exist in Redis
    cached_details = r.get(f"match_details:{match_id}")
    if cached_details:
        logging.info(f"Match details for ID {match_id} retrieved from database.")
        return json.loads(cached_details)

    try:
        url = f"https://{api_host}/api/match/{match_id}"
        match_details = make_api_request(url)

        if match_details:
            # Store the match details in Redis
            r.set(f"match_details:{match_id}", json.dumps(match_details))
            logging.info(f"Match details for ID {match_id} successfully fetched from API and stored in database.")
            return match_details
        else:
            logging.error(f"Failed to fetch match details for match ID: {match_id}")
            return None

    except Exception as e:
        logging.error(f"Error in fetch_and_store_match_details: {str(e)}")
        return None


def fetch_and_store_league_season_info(league_id, season_id):
    """
    Fetches league season info from API, stores it in Redis, and returns the info.
    """
    logging.info(f"Fetching league season info for league ID {league_id} and season ID {season_id}")

    # First, try to get the info from Redis
    info = get_league_season_info(league_id, season_id)

    if info:
        logging.info(f"League season info for league ID {league_id} and season ID {season_id} retrieved from Redis.")
        return info

    # If not in Redis, fetch from API
    url = f"https://footapi7.p.rapidapi.com/api/tournament/{league_id}/season/{season_id}/info"

    info = make_api_request(url)

    if info:
        # Store the fetched info in Redis
        store_league_season_info(league_id, season_id, info)
        logging.info(
            f"League season info for league ID {league_id} and season ID {season_id} fetched from API and stored in Redis.")
    else:
        logging.error(f"Failed to fetch league season info for league ID {league_id} and season ID {season_id}.")

    return info
# Example usage
# logging.info("Fetching standings, league info, and league seasons for league ID '187'.")
# print(fetch_standings("187", "61714"))
# print(fetch_league_info("187"))
# print(fetch_league_seasons("187"))
# print(fetch_team_info("2820"))
# print(fetch_previous_matches("2820"))
