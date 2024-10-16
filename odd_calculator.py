import json
import logging
from tkinter import messagebox

from api_call import api_host, make_api_request
from api_utils import fetch_previous_matches, fetch_and_store_upcoming_matches, fetch_standings
from getters import get_team_info
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

def predict_match(league_id, season_id, home_team_id, away_team_id, match_id):
    """
    Predicts the score of a match based on team standings, last 3 matches, and odds.
    """
    logging.info(f"Predicting match: {home_team_id} vs {away_team_id}")

    # 1. Get team standings
    standings = fetch_standings(league_id, season_id)
    if not standings:
        return "Unable to fetch standings data."

    home_standing = next((team for team in standings['standings'][0]['rows'] if team['team']['id'] == home_team_id), None)
    away_standing = next((team for team in standings['standings'][0]['rows'] if team['team']['id'] == away_team_id), None)

    if not home_standing or not away_standing:
        return "Unable to find team standings."

    # 2. Get last 3 matches for each team
    home_previous = fetch_previous_matches(home_team_id)
    away_previous = fetch_previous_matches(away_team_id)

    if not home_previous or not away_previous:
        return "Unable to fetch previous matches."

    # 3. Get match odds
    odds_1x2 = get_match_odds_1x2(match_id)
    if not odds_1x2:
        return "Unable to fetch match odds."

    # 4. Calculate prediction factors
    home_factor = calculate_team_factor(home_standing, home_previous[-3:], odds_1x2['home'])
    away_factor = calculate_team_factor(away_standing, away_previous[-3:], odds_1x2['away'])

    # 5. Predict score
    home_score = round(home_factor * 2)  # Multiply by 2 as a baseline
    away_score = round(away_factor * 2)

    # 6. Adjust for home advantage
    home_score += 1

    # Get team names
    home_team_name = get_team_info(home_team_id)['name']
    away_team_name = get_team_info(away_team_id)['name']

    prediction_message = f"Predicted Score:\n{home_team_name} {home_score} - {away_score} {away_team_name}\n\n"
    prediction_message += f"Prediction Factors:\n"
    prediction_message += f"{home_team_name}: {home_factor:.2f}\n"
    prediction_message += f"{away_team_name}: {away_factor:.2f}\n"

    logging.info(f"Prediction: {prediction_message}")

    return prediction_message

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