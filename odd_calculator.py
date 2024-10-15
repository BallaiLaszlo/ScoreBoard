import json
import logging

from api_call import api_host, make_api_request
from redis_connection import r


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
    # Initialize an empty dictionary to store the percentages
    percentages = {}

    # Initialize a variable to store the total probability
    total_probability = 0

    # Iterate over each outcome in the odds
    for outcome, values in odds.items():
        # Split the fractional value into numerator and denominator
        numerator, denominator = map(int, values['fractional_value'].split('/'))

        # Calculate the decimal odds
        decimal_odds = (numerator + denominator) / numerator

        # Calculate the probability
        probability = 1 / decimal_odds

        # Add the probability to the total probability
        total_probability += probability

    # Iterate over each outcome in the odds again
    for outcome, values in odds.items():
        # Split the fractional value into numerator and denominator
        numerator, denominator = map(int, values['fractional_value'].split('/'))

        # Calculate the decimal odds
        decimal_odds = (numerator + denominator) / numerator

        # Calculate the probability
        probability = 1 / decimal_odds

        # Calculate the percentage
        percentage = (probability / total_probability) * 100

        # Store the percentage in the dictionary
        percentages[outcome] = round(percentage, 2)

    return percentages