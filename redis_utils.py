import logging
import json
from typing import Union, Dict, Any, List

from getters import get_last_three_matches
from redis_connection import r


def store_league_info(league_id: str, league_info: Union[Dict[str, Any], str], last_fetched: float = 0) -> None:
    """
    Saves league information to the Redis database.

    Args:
        league_id (str): The unique identifier of the league.
        league_info (Union[Dict[str, Any], str]): The league information to store. Can be a dictionary or a JSON string.
        last_fetched (float, optional): The timestamp of when the league info was fetched. Defaults to 0.

    Returns:
        None

    Raises:
        RedisError: If there's an error while storing data in Redis.
    """
    if isinstance(league_info, dict):
        league_info = json.dumps(league_info)
    r.set(f"league_info:{league_id}", league_info)
    r.set(f"league_info_time:{league_id}", last_fetched)


def store_standings(league_id: str, season_id: str, standings_data: Dict[str, Any], last_fetched: float = 0) -> None:
    """
    Stores the standings for a given league and season in the Redis database.

    Args:
        league_id (str): The unique identifier of the league.
        season_id (str): The unique identifier of the season.
        standings_data (Dict[str, Any]): The standings data to store.
        last_fetched (float, optional): The timestamp of when the standings were last fetched. Defaults to 0.

    Returns:
        None

    Raises:
        RedisError: If there's an error while storing data in Redis.
    """
    r.set(f"standings:{league_id}:{season_id}", json.dumps(standings_data))
    r.set(f"standings_time:{league_id}:{season_id}", last_fetched)
    logging.info(f"Standings for league ID {league_id} and season ID {season_id} stored in the database.")


def store_league_image(league_id: str, image_data: Union[bytes, str]) -> None:
    """
    Saves league image in Redis.

    Args:
        league_id (str): The unique identifier of the league.
        image_data (Union[bytes, str]): The image data to store. Can be binary data or a URL.

    Returns:
        None

    Raises:
        RedisError: If there's an error while storing data in Redis.
    """
    image_key = f"league_image:{league_id}"
    r.set(image_key, image_data)
    logging.info(f"Stored image for league ID {league_id} in Redis.")

    image_key = f"league_image:{league_id}"
    r.set(image_key, image_data)
    logging.info(f"Stored image for league ID {league_id} in Redis.")


def store_league_seasons(league_id: str, seasons: List[Dict[str, Any]]) -> None:
    """
    Store the seasons data in Redis with the key of the league ID.

    Args:
        league_id (str): The unique identifier of the league.
        seasons (List[Dict[str, Any]]): A list of season dictionaries to store.

    Returns:
        None

    Raises:
        RedisError: If there's an error while storing data in Redis.
    """
    r.set(f"league:{league_id}:seasons", json.dumps(seasons))


def store_team_info(team_id: str, team_info: Union[Dict[str, Any], str], last_fetched: float = 0) -> None:
    """
    Stores the team information in the Redis database.

    Args:
        team_id (str): The unique identifier of the team.
        team_info (Union[Dict[str, Any], str]): The team information to store. Can be a dictionary or a JSON string.
        last_fetched (float, optional): The timestamp of when the team info was fetched. Defaults to 0.

    Returns:
        None

    Raises:
        RedisError: If there's an error while storing data in Redis.
    """
    if isinstance(team_info, dict):
        team_info = json.dumps(team_info)

    # Store team info in Redis
    r.set(f"team_info:{team_id}", team_info)
    r.set(f"team_info_time:{team_id}", last_fetched)
    logging.info(f"Team info for ID {team_id} stored in the database.")


def store_last_three_matches(team_id: str, formatted_matches: str) -> None:
    """
    Stores the last three formatted matches for a given team ID in Redis.

    Args:
        team_id (str): The unique identifier of the team.
        formatted_matches (str): The formatted match information to store.

    Returns:
        None

    Raises:
        RedisError: If there's an error while storing data in Redis.
    """
    if formatted_matches:
        logging.info(f"Storing matches for team ID {team_id}: {formatted_matches}")
        r.set(f'team_previous_matches:{team_id}', formatted_matches)
        logging.info(f"Stored formatted matches for team ID {team_id} in Redis.")
    else:
        logging.warning(f"No matches to store for team ID {team_id}.")


def store_next_three_matches(team_id: str, next_three_matches: List[Dict[str, Any]]) -> None:
    """
    Stores the next three matches for a given team ID in Redis.

    Args:
        team_id (str): The unique identifier of the team.
        next_three_matches (List[Dict[str, Any]]): A list of dictionaries containing the next three matches.

    Returns:
        None

    Raises:
        RedisError: If there's an error while storing data in Redis.
    """
    if next_three_matches:
        logging.info(f"Storing matches for team ID {team_id}: {next_three_matches}")
        match_info = []
        for match in next_three_matches:
            match_string = (
                f"Tournament: {match['tournament_name']}\n"
                f"{match['home_team']} vs {match['away_team']}\n"
                f"Status: {match['status']}\n"
                f"Start Timestamp: {match['start_timestamp']}\n"
                f"Match ID: {match['match_id']}\n"
            )
            match_info.append(match_string)
        r.set(f'team_next_matches:{team_id}', "\n\n".join(match_info))
        logging.info(f"Stored next three matches for team ID {team_id} in Redis.")
    else:
        logging.warning(f"No matches to store for team ID {team_id}.")


def store_league_season_info(league_id: str, season_id: str, info: Dict[str, Any]) -> None:
    """
    Stores league season info in Redis.

    Args:
        league_id (str): The unique identifier of the league.
        season_id (str): The unique identifier of the season.
        info (Dict[str, Any]): The league season information to store.

    Returns:
        None

    Raises:
        RedisError: If there's an error while storing data in Redis.
    """
    if info:
        key = f'league_season_info:{league_id}:{season_id}'
        r.set(key, json.dumps(info))
        logging.info(f"Stored league season info for league ID {league_id} and season ID {season_id} in Redis.")
    else:
        logging.warning(f"No league season info to store for league ID {league_id} and season ID {season_id}.")


def store_league_season_info(league_id: str, season_id: str, info: Dict[str, Any]) -> None:
    """
    Stores league season info in Redis.

    Args:
        league_id (str): The unique identifier of the league.
        season_id (str): The unique identifier of the season.
        info (Dict[str, Any]): The league season information to store.

    Returns:
        None

    Raises:
        RedisError: If there's an error while storing data in Redis.
    """
    if info:
        key = f'league_season_info:{league_id}:{season_id}'
        r.set(key, json.dumps(info))
        logging.info(f"Stored league season info for league ID {league_id} and season ID {season_id} in Redis.")
    else:
        logging.warning(f"No league season info to store for league ID {league_id} and season ID {season_id}.")
    # store_standings("8",61643,fetch_standings("8","61643"))
# store_league_info("8",fetch_league_info("8"))
# store_league_image("8",fetch_league_image("8"))
# store_league_seasons("8",fetch_league_seasons(8))
