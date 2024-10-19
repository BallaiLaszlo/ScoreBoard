import json
import logging
from tkinter import messagebox

from api_call import api_host, make_api_request
from api_utils import fetch_previous_matches, fetch_and_store_upcoming_matches, fetch_standings, \
    fetch_and_store_match_details
from getters import get_team_info, get_last_three_matches, get_first_season_id
from redis_connection import r

logging.basicConfig(
    filename='log.txt',  # Log file name
    level=logging.INFO,  # Log level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log message format
)


def fetch_match_odds(match_id):
    """
    Fetches the match odds for a given match ID.

    Args:
        match_id (str): The ID of the match.

    Returns:
        dict: The match odds.
    """
    url = f"https://{api_host}/api/match/{match_id}/odds"
    response = make_api_request(url)

    if response:
        logging.info(f"Match odds for match ID {match_id} successfully fetched from API.")
        return response
    else:
        logging.error(f"Failed to fetch match odds for match ID {match_id} from API.")
        return None


def store_match_odds(match_id, match_odds):
    """
    Stores the match odds for a given match ID in Redis.

    Args:
        match_id (str): The ID of the match.
        match_odds (dict): The match odds.
    """
    if match_odds:
        logging.info(f"Storing match odds for match ID {match_id}: {match_odds}")
        r.set(f'match_odds:{match_id}', json.dumps(match_odds))
        logging.info(f"Stored match odds for match ID {match_id} in Redis.")
    else:
        logging.warning(f"No match odds to store for match ID {match_id}.")


def get_match_odds(match_id):
    """
    Retrieves the match odds for a given match ID from Redis.

    Args:
        match_id (str): The ID of the match.

    Returns:
        dict: The match odds.
    """
    match_odds = r.get(f'match_odds:{match_id}')

    if match_odds:
        logging.info(f"Match odds for match ID {match_id} retrieved from Redis.")
        return json.loads(match_odds)
    else:
        logging.info(f"Fetching match odds for match ID {match_id} from API.")
        match_odds = fetch_match_odds(match_id)

        if match_odds:
            store_match_odds(match_id, match_odds)
            logging.info(f"Match odds for match ID {match_id} successfully fetched and stored.")
        else:
            logging.error(f"Failed to fetch match odds for match ID {match_id} from API.")

        return match_odds


def get_match_odds_1x2(match_id):
    """
    Retrieves the 1x2 odds and their corresponding changes for a given match ID.

    Args:
        match_id (str): The ID of the match.

    Returns:
        dict: A dictionary containing the 1x2 odds and their corresponding changes.
    """
    match_odds = get_match_odds(match_id)

    if match_odds:
        markets = match_odds.get('markets', [])

        for market in markets:
            if market['marketName'] == 'Full time':
                choices = market.get('choices', [])

                odds_1x2 = {}
                for choice in choices:
                    name = choice['name']
                    fractional_value = choice['fractionalValue']
                    change = choice['change']

                    odds_1x2[name] = {'fractional_value': fractional_value, 'change': change}

                return odds_1x2

    return None

def get_match_prediction_info(match_details):
    """
    Retrieves all necessary information for match prediction.

    Args:
        match_details (dict): The match details dictionary.

    Returns:
        dict: A dictionary containing tournament_id, season_id, home_team_id, away_team_id, and match_id.
              Returns None if any information is missing.
    """
    logging.info("Extracting prediction info from match details.")

    try:
        # Extract required information
        event = match_details.get('event', {})
        tournament = event.get('tournament', {})
        tournament_id = tournament.get('uniqueTournament', {}).get('id')
        season_id = event.get('season', {}).get('id')
        home_team_id = event.get('homeTeam', {}).get('id')
        away_team_id = event.get('awayTeam', {}).get('id')
        match_id = event.get('id')

        if not all([tournament_id, season_id, home_team_id, away_team_id, match_id]):
            logging.error("Missing required information in match details.")
            return None

        return {
            'tournament_id': tournament_id,
            'season_id': season_id,
            'home_team_id': home_team_id,
            'away_team_id': away_team_id,
            'match_id': match_id
        }

    except Exception as e:
        logging.error(f"Error in get_match_prediction_info: {str(e)}")
        return None

def calculate_percentage(odds):
    """
    Calculates the percentage from the given odds.

    Args:
        odds (dict): A dictionary containing the odds.

    Returns:
        dict: A dictionary where each key is a possible outcome and each value is the corresponding percentage.
    """
    # Initialize an empty dictionary to store the probabilities
    probabilities = {}

    # Calculate the implied probability for each outcome
    for outcome, values in odds.items():
        # Split the fractional value into numerator and denominator
        numerator, denominator = map(int, values['fractional_value'].split('/'))

        # Calculate the implied probability
        implied_probability = denominator / (numerator + denominator)
        probabilities[outcome] = implied_probability

    # Calculate the total implied probability
    total_probability = sum(probabilities.values())

    # Normalize the probabilities to get the fair percentages
    percentages = {}
    for outcome, probability in probabilities.items():
        percentage = (probability / total_probability) * 100
        percentages[outcome] = round(percentage, 2)

    return percentages

def parse_upcoming_matches(upcoming_match_dict):
    matches = upcoming_match_dict.split('\n\n')
    parsed_matches = []
    for match in matches:
        lines = match.split('\n')
        match_dict = {
            'tournament': lines[0].split(': ')[1],
            'teams': lines[1].split(' vs '),
            'status': lines[2].split(': ')[1],
            'match_id': lines[4].split(': ')[1]
        }
        parsed_matches.append(match_dict)
    return parsed_matches


def predict_match(match_id):
    """
    Predicts the match score based on form (40%), odds (30%), league standing (10%), and recent goals (20%).
    """
    # Fetch match details
    match_details = fetch_and_store_match_details(match_id)
    if not match_details:
        logging.error(f"Unable to fetch match details for match ID: {match_id}")
        return f"Unable to fetch match details for match ID: {match_id}. Check if the match ID is correct."

    # Log the match details for debugging
    logging.info(f"Match details: {match_details}")

    # Extract prediction info
    prediction_info = get_match_prediction_info(match_details)
    if not prediction_info:
        logging.error(f"Unable to extract prediction info for match ID: {match_id}")
        return f"Unable to extract prediction info for match ID: {match_id}. Match details might be incomplete."

    # Log the prediction info for debugging
    logging.info(f"Prediction info: {prediction_info}")

    home_team_id = prediction_info['home_team_id']
    away_team_id = prediction_info['away_team_id']
    tournament_id = prediction_info['tournament_id']
    season_id = prediction_info['season_id']

    # Get last 3 matches
    home_last_matches = get_last_three_matches(home_team_id)
    away_last_matches = get_last_three_matches(away_team_id)

    # Calculate form and recent goals
    home_form, home_goals = calculate_form_and_goals(home_last_matches)
    away_form, away_goals = calculate_form_and_goals(away_last_matches)

    # Get odds
    odds = get_match_odds_1x2(match_id)
    if not odds:
        logging.error(f"Unable to fetch odds for match ID: {match_id}")
        return "Unable to fetch odds."

    home_odds = odds.get('Home', {'fractional_value': '1/1'})['fractional_value']
    away_odds = odds.get('Away', {'fractional_value': '1/1'})['fractional_value']

    # Convert fractional odds to decimal
    home_odds = calculate_decimal_odds(home_odds)
    away_odds = calculate_decimal_odds(away_odds)

    # Get league standings
    standings = fetch_standings(tournament_id, season_id)
    if not standings:
        logging.error(f"Unable to fetch standings for tournament ID: {tournament_id}, season ID: {season_id}")
        return "Unable to fetch standings."

    home_position = get_team_position(standings, home_team_id)
    away_position = get_team_position(standings, away_team_id) # This function is not defined in the provided code

    # Calculate prediction factors
    home_factor = calculate_prediction_factor(home_form, home_odds, home_position, home_goals)
    away_factor = calculate_prediction_factor(away_form, away_odds, away_position, away_goals)

    # Predict score
    home_score = round(home_factor * 2)  # Multiply by 2 as a baseline
    away_score = round(away_factor * 2)

    # Get team names
    home_team_name = get_team_info(home_team_id)['name']
    away_team_name = get_team_info(away_team_id)['name']

    prediction_message = f"Predicted Score:\n{home_team_name} {home_score} - {away_score} {away_team_name}\n\n"
    prediction_message += f"Prediction Factors:\n"
    prediction_message += f"{home_team_name}: {home_factor:.2f}\n"
    prediction_message += f"{away_team_name}: {away_factor:.2f}\n"

    logging.info(f"Prediction: {prediction_message}")

    return prediction_message

def calculate_decimal_odds(fractional_odds):
    """
    Converts fractional odds to decimal odds.
    """
    numerator, denominator = map(int, fractional_odds.split('/'))
    return denominator / numerator

def calculate_form_and_goals(matches):
    form = 0
    goals = 0
    for match in matches:
        lines = match.split('\n')
        scores = lines[1].split(' - ')
        home_score = int(scores[0])
        away_score = int(scores[1])

        if lines[0].startswith("Home"):  # This condition is not necessary if the matches are always in the same order
            form += 3 if home_score > away_score else (1 if home_score == away_score else 0)
            goals += home_score
        else:
            form += 3 if away_score > home_score else (1 if home_score == away_score else 0)
            goals += away_score
    return form, goals


def get_team_position(self, standings, team_id):
    for row in standings['standings'][0]['rows']:
        if row['team']['id'] == team_id:
            return row['position']
    return None


def get_team_position(self, standings, team_id):
    for row in standings['standings'][0]['rows']:
        if row['team']['id'] == team_id:
            return row['position']
    return None

def get_team_position(self, standings, team_id):
    """
    Get the team's position in the league standings.
    """
    for row in standings['standings'][0]['rows']:
        if row['team']['id'] == team_id:
            return row['position']
    return 0  # Return 0 if team not found


def get_team_position(self, standings, team_id):
    """
    Get the team's position in the league standings.
    """
    for row in standings['standings'][0]['rows']:
        if row['team']['id'] == team_id:
            return row['position']
    return 0  # Return 0 if team not found

def calculate_team_factor(standing, last_3_matches, odds):
    """
    Calculates a team's factor based on standing, recent form, and odds.
    """
    # Standing factor (normalized)
    standing_factor = (20 - standing['position']) / 20  # Assumes 20 teams in league

    # Recent form factor
    form_factor = sum(3 if match['winner'] == 'home' else (1 if match['winner'] == 'draw' else 0) for match in last_3_matches) / 9

    # Odds factor (inverse of odds, normalized)
    odds_factor = 1 / odds / 3  # Divide by 3 to normalize

    # Combine factors (you can adjust weights as needed)
    team_factor = (standing_factor * 0.4) + (form_factor * 0.4) + (odds_factor * 0.2)

    return team_factor