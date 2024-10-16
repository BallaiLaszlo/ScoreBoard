import json
import logging
from redis_connection import r


logging.basicConfig(
    filename='log.txt',  # Log file name
    level=logging.INFO,  # Log level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log message format
)

with open('settings.json', 'r') as f:
    settings = json.load(f)

leagues = settings["leagues"]


def get_league_names(league_id):
    """
    Retrieve league information from Redis by league ID.
    """
    league_info = r.get(f"league_info:{league_id}")
    if league_info:
        league_info_dict = json.loads(league_info.decode('utf-8'))
        logging.info(f"Retrieved league info for league ID {league_id}.")
        return league_info_dict
    logging.warning(f"No league info found for league ID {league_id}.")
    return None

def get_league_name_list():
    """
    Get a list of league IDs and names.
    """
    league_name_list = []
    for league_id in leagues:
        league_info_dict = get_league_names(league_id)
        if league_info_dict:
            unique_tournament = league_info_dict.get('uniqueTournament', {})
            league_name = unique_tournament.get('name')
            if league_name:
                league_name_list.append((league_id, league_name))
                logging.info(f"Added league ID {league_id} with name '{league_name}' to the league name list.")
            else:
                logging.warning(f"No name found for league ID {league_id}.")
        else:
            logging.warning(f"League info not found for league ID {league_id}.")
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
        logging.info(f"Retrieved seasons for league ID {league_id}: {season_ids}.")
        return season_ids
    logging.warning(f"No seasons found for league ID {league_id}.")
    return None

def get_first_season_id(league_id):
    """
    Retrieve the first season ID from Redis.
    """
    temp = get_seasons(league_id)
    if temp:
        logging.info(f"First season ID for league ID {league_id} is {temp[0]}.")
        return temp[0]
    logging.warning(f"No seasons available to retrieve first season ID for league ID {league_id}.")
    return None

def get_league_image_from_db(league_id):
    """
    Retrieve league image from Redis by league ID.
    """
    image_key = f"league_image:{league_id}"
    if r.exists(image_key):
        image = r.get(image_key)
        logging.info(f"Retrieved image for league ID {league_id}.")
        return image
    logging.warning(f"No image found for league ID {league_id}.")
    return None

def get_standings(league_id, season_id):
    """
    Retrieve standings for a specific league and season from Redis.
    """
    key = f"standings:{league_id}:{season_id}"
    standings = r.get(key)
    if standings:
        standings_dict = json.loads(standings.decode('utf-8'))
        logging.info(f"Retrieved standings for league ID {league_id}, season ID {season_id}.")
        return standings_dict
    logging.warning(f"No standings found for league ID {league_id}, season ID {season_id}.")
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
    if league_info:
        logging.info(f"Retrieved league info for league ID {league_id}.")
    else:
        logging.warning(f"No league info found for league ID {league_id}.")
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
    key = f"standings_time:{league_id}:{season_id}"
    last_fetched = r.get(key)
    if last_fetched:
        logging.info(f"Retrieved last fetched time for league ID {league_id}, season ID {season_id}.")
        return float(last_fetched.decode('utf-8'))
    logging.warning(f"No last fetched time found for league ID {league_id}, season ID {season_id}.")
    return None


def delete_standings(league_id):
    """
    Deletes the standings data for the given league from the Redis database.

    Args:
        league_id (str): The ID of the league whose standings will be deleted.
    """
    try:
        redis_key = f"standings:{league_id}"
        if r.exists(redis_key):
            r.delete(redis_key)
            logging.info(f"Deleted standings for league {league_id} from Redis.")
        else:
            logging.warning(f"No standings found for league {league_id} in Redis.")
    except Exception as e:
        logging.error(f"Error deleting standings for league {league_id}: {e}")


def get_team_info(team_id):
    """
    Retrieves the team information from the database.

    Args:
        team_id (str): The ID of the team.

    Returns:
        dict: The team information including name, location, manager, venue, country, etc.
    """
    # Fetch the team info as a string from Redis
    team_info = r.get(f"team_info:{team_id}")

    if team_info:
        # Log the raw data for debugging
        logging.info(f"Raw team info retrieved for team ID {team_id}: {team_info}")

        # Parse the string into a dictionary (since it's stored as a JSON string)
        try:
            team_info = json.loads(team_info)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON for team ID {team_id}: {e}")
            return None

        # Log the parsed data
        logging.info(f"Parsed team info for team ID {team_id}: {team_info}")

        # Accessing the nested structure to get the required fields
        team = team_info.get('team', {})
        team_name = team.get('name', 'Unknown')
        manager_name = team.get('manager', {}).get('name', 'Unknown')
        venue = team.get('venue', {}).get('name', 'Unknown')
        venue_capacity = team.get('venue', {}).get('capacity', 'Unknown')

        # Extracting country and location from the venue's city
        venue_city = team.get('venue', {}).get('city', {}).get('name', 'Unknown')
        country_name = team.get('country', {}).get('name', 'Unknown')

        # Extracting team colors
        team_colors = team.get('teamColors', {})
        primary_color = team_colors.get('primary', 'Unknown')
        secondary_color = team_colors.get('secondary', 'Unknown')
        text_color = team_colors.get('text', 'Unknown')

        # Return the relevant details including location and country
        return {
            'name': team_name,
            'manager': manager_name,
            'venue': venue,
            'venue_capacity': venue_capacity,
            'location': venue_city,
            'country': country_name,
            'team_colors': {
                'primary': primary_color,
                'secondary': secondary_color,
                'text': text_color
            }
        }
    else:
        logging.warning(f"No team info found for team ID {team_id}.")
        return None


def get_team_id_from_standings(standings, team_name):
    """
    Retrieves the team ID for a specific team from the standings data.

    Args:
        standings (dict): The standings data.
        team_name (str): The name of the team to find.

    Returns:
        int: The ID of the team if found, otherwise None.
    """
    # Iterate through the standings rows to find the team by its name
    for row in standings.get('standings', [])[0].get('rows', []):
        team = row.get('team', {})
        if team.get('name') == team_name:
            return team.get('id')

    logging.warning(f"No team ID found for team name {team_name}")
    return None

def get_team_scores(response):
    """
    Extract team scores from the API response and return the entire response.
    """
    try:
        # Log the raw response for debugging
        logging.info(f"Raw API response: {response}")

        # If you want to extract specific data later, you can still do so
        team_scores = response.get('matches', [])  # Adjust according to the actual structure of your response

        # Log the team scores for debugging
        logging.info(f"Extracted team scores: {team_scores}")

        # Return the entire response for further processing
        return response
    except Exception as e:
        logging.error(f"Error extracting team scores: {e}")
        return None


import json


def get_previous_matches(team_id):
    """
    Retrieve previous matches for a team from Redis.

    Args:
        team_id (str): The ID of the team.

    Returns:
        list: A list of previous matches for the specified team, or None if not found.
    """
    # Use the correct Redis key format
    previous_matches_json = r.get(f"team_previous_matches:{team_id}")

    if previous_matches_json:
        try:
            # Deserialize the JSON string into a Python object (dictionary)
            previous_matches = json.loads(previous_matches_json)

            # Log the deserialized data (optional, for debugging)
            print(f"Deserialized data for team {team_id}: {previous_matches}")

            # Return the list of events (matches)
            return previous_matches.get('events') if 'events' in previous_matches else None

        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON: {e}")
            return None
    else:
        print(f"No previous matches found for team ID {team_id}.")
        return None


# getters.py
def get_last_three_matches(team_id):
    """
    Fetches the last 3 matches for a given team ID, with Redis caching.
    """
    # Check if matches exist in the Redis database
    cached_matches = r.get(f'team_previous_matches:{team_id}')

    if cached_matches:
        try:
            matches = cached_matches.decode('utf-8').split('\n\n')  # Split the string into a list of matches
            logging.info(f"Retrieved matches for team ID {team_id}: {matches}")
        except Exception as e:
            logging.error(f"Error parsing matches for team ID {team_id}: {e}")
            return []
        # Return the last three matches
        return matches[-3:] if len(matches) >= 3 else matches
    else:
        logging.warning(f"No cached matches found for team ID {team_id}.")
        return []


def format_last_three_matches(matches_data):
    # Get the list of events (matches)
    events = matches_data.get('events', [])

    # Initialize an empty list to store formatted match information
    formatted_matches = []

    # Iterate through the last three matches (or less if there aren't three)
    for event in events[:3]:
        tournament_name = event['tournament']['name']
        home_team = event['homeTeam']['name']
        away_team = event['awayTeam']['name']
        home_score = event['homeScore']['current']
        away_score = event['awayScore']['current']
        status = event['status']['description']

        # Create a formatted string for the match
        match_info = (
            f"Tournament: {tournament_name}\n"
            f"{home_team} {home_score} - {away_score} {away_team}\n"
            f"Status: {status}\n"
        )
        formatted_matches.append(match_info)

    return "\n".join(formatted_matches)


def get_next_three_matches(response):
    """
    Extract the next three matches from the API response.

    Args:
        response (dict): The API response.

    Returns:
        list: A list of the next three matches.
    """
    try:
        # Get the list of events (matches)
        events = response.get('events', [])

        # Initialize an empty list to store the next three matches
        next_three_matches = []

        # Iterate through the next three matches (or less if there aren't three)
        for event in events[:3]:
            tournament_name = event['tournament']['name']
            home_team = event['homeTeam']['name']
            away_team = event['awayTeam']['name']
            status = event['status']['description']
            start_timestamp = event['startTimestamp']
            match_id = event['id']  # Extract the match ID

            # Create a formatted string for the match
            match_info = {
                'tournament_name': tournament_name,
                'home_team': home_team,
                'away_team': away_team,
                'status': status,
                'start_timestamp': start_timestamp,
                'match_id': match_id  # Include the match ID
            }
            next_three_matches.append(match_info)

        return next_three_matches

    except Exception as e:
        logging.error(f"Error extracting next three matches: {e}")
        return []


def get_next_match_info(upcoming_matches):
    if not upcoming_matches or not isinstance(upcoming_matches, list):
        return None

    for match in upcoming_matches:
        match_id = match.get('match_id')
        home_team = match.get('home_team')
        away_team = match.get('away_team')
        if match_id and home_team and away_team:
            return match_id, home_team, away_team
    return None


def get_match_prediction_info(match_id):
    """
    Retrieves all necessary information for match prediction.

    Args:
        match_id (str): The ID of the match.

    Returns:
        dict: A dictionary containing league_id, season_id, home_team_id, away_team_id, and match_id.
              Returns None if any information is missing.
    """
    logging.info(f"Fetching prediction info for match ID: {match_id}")

    try:
        # Fetch match details
        match_details_json = r.get(f"match_details:{match_id}")
        if not match_details_json:
            logging.error(f"Match details not found for match ID: {match_id}")
            return None

        match_details = json.loads(match_details_json)
        event = match_details.get('event', {})

        # Extract required information
        league_id = event.get('tournament', {}).get('uniqueTournament', {}).get('id')
        season_id = event.get('season', {}).get('id')
        home_team_id = event.get('homeTeam', {}).get('id')
        away_team_id = event.get('awayTeam', {}).get('id')

        if not all([league_id, season_id, home_team_id, away_team_id]):
            logging.error(f"Missing required information for match ID: {match_id}")
            return None

        return {
            'league_id': league_id,
            'season_id': season_id,
            'home_team_id': home_team_id,
            'away_team_id': away_team_id,
            'match_id': match_id
        }

    except Exception as e:
        logging.error(f"Error in get_match_prediction_info: {str(e)}")
        return None

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
#print(get_team_info("17"))

