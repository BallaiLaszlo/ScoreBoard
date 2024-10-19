import json
import logging
from tkinter import messagebox

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from api_call import api_host, make_api_request
from api_utils import fetch_previous_matches, fetch_and_store_upcoming_matches, fetch_standings, \
    fetch_and_store_match_details
from getters import get_team_info, get_last_three_matches, get_first_season_id
from redis_connection import r

logging.basicConfig(
    filename='log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def fetch_match_odds(match_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches match odds from the API for a given match ID.

    Args:
        match_id (str): The ID of the match.

    Returns:
        Optional[Dict[str, Any]]: The match odds data if successful, None otherwise.
    """
    url = f"https://{api_host}/api/match/{match_id}/odds"
    response = make_api_request(url)

    if response:
        logging.info(f"Match odds for match ID {match_id} successfully fetched from API.")
        return response
    else:
        logging.error(f"Failed to fetch match odds for match ID {match_id} from API.")
        return None


def store_match_odds(match_id: str, match_odds: Dict[str, Any]) -> None:
    """
    Stores match odds in Redis for a given match ID.

    Args:
        match_id (str): The ID of the match.
        match_odds (Dict[str, Any]): The match odds data to store.
    """
    if match_odds:
        logging.info(f"Storing match odds for match ID {match_id}: {match_odds}")
        r.set(f'match_odds:{match_id}', json.dumps(match_odds))
        logging.info(f"Stored match odds for match ID {match_id} in Redis.")
    else:
        logging.warning(f"No match odds to store for match ID {match_id}.")


def get_match_odds(match_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves match odds from Redis or fetches from API if not available.

    Args:
        match_id (str): The ID of the match.

    Returns:
        Optional[Dict[str, Any]]: The match odds data if available, None otherwise.
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


def get_match_odds_1x2(match_id: str) -> Optional[Dict[str, Dict[str, str]]]:
    """
    Retrieves 1X2 match odds for a given match ID.

    Args:
        match_id (str): The ID of the match.

    Returns:
        Optional[Dict[str, Dict[str, str]]]: The 1X2 odds data if available, None otherwise.
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


def get_match_prediction_info(match_details: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Extracts prediction information from match details.

    Args:
        match_details (Dict[str, Any]): The match details.

    Returns:
        Optional[Dict[str, str]]: A dictionary containing prediction info if successful, None otherwise.
    """
    logging.info("Extracting prediction info from match details.")

    try:
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
            'away_team_id': away_team_id,  # Fixed the typo here
            'match_id': match_id
        }

    except Exception as e:
        logging.error(f"Error in get_match_prediction_info: {str(e)}")
        return None


def calculate_percentage(odds: Dict[str, Dict[str, str]]) -> Dict[str, float]:
    """
    Calculates percentage probabilities from fractional odds.

    Args:
        odds (Dict[str, Dict[str, str]]): The odds data.

    Returns:
        Dict[str, float]: A dictionary of calculated percentages.
    """
    probabilities = {}

    for outcome, values in odds.items():
        numerator, denominator = map(int, values['fractional_value'].split('/'))
        implied_probability = denominator / (numerator + denominator)
        probabilities[outcome] = implied_probability

    total_probability = sum(probabilities.values())
    percentages = {}
    for outcome, probability in probabilities.items():
        percentage = (probability / total_probability) * 100
        percentages[outcome] = round(percentage, 2)

    return percentages


def parse_upcoming_matches(upcoming_match_dict: str) -> List[Dict[str, Any]]:
    """
    Parses upcoming matches from a string representation.

    Args:
        upcoming_match_dict (str): A string containing upcoming match information.

    Returns:
        List[Dict[str, Any]]: A list of parsed match dictionaries.
    """
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


def get_team_position(standings: Dict[str, Any], team_id: str) -> int:
    """
    Retrieves a team's position from standings data.

    Args:
        standings (Dict[str, Any]): The standings' data.
        team_id (str): The ID of the team.

    Returns:
        int: The team's position in the standings.
    """

    for row in standings['standings'][0]['rows']:
        if row['team']['id'] == team_id:
            return row['position']
    return 0


def get_league_info(tournament_id: str, season_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves league information for a given tournament and season.

    Args:
        tournament_id (str): The ID of the tournament.
        season_id (str): The ID of the season.

    Returns:
        Optional[Dict[str, Any]]: League information if available, None otherwise.
    """
    url = f"https://{api_host}/api/tournament/{tournament_id}/season/{season_id}/info"
    league_info = make_api_request(url)
    if league_info and 'info' in league_info:
        return league_info['info']
    return None


def predict_match(match_id: str) -> str:
    """
    Predicts the outcome of a match based on various factors.

    Args:
        match_id (str): The ID of the match to predict.

    Returns:
        str: A message containing the prediction results.
    """
    match_details = fetch_and_store_match_details(match_id)
    if not match_details:
        return f"Unable to fetch match details for match ID: {match_id}. Check if the match ID is correct."

    prediction_info = get_match_prediction_info(match_details)
    if not prediction_info:
        return f"Unable to extract prediction info for match ID: {match_id}. Match details might be incomplete."

    home_team_id, away_team_id, tournament_id, season_id = extract_team_and_tournament_info(prediction_info)

    league_info = get_league_info(tournament_id, season_id)
    if not league_info:
        return "Unable to fetch league info."

    standings = fetch_standings(tournament_id, season_id)
    if not standings:
        return "Unable to fetch standings."

    home_team_data = get_team_data(home_team_id, match_id, standings, league_info, is_home=True)
    away_team_data = get_team_data(away_team_id, match_id, standings, league_info, is_home=False)

    home_factor = calculate_prediction_factor(**{k: v for k, v in home_team_data.items() if k != 'name'})
    away_factor = calculate_prediction_factor(**{k: v for k, v in away_team_data.items() if k != 'name'})

    home_expected_goals, away_expected_goals = calculate_expected_goals(home_factor, away_factor, league_info)

    num_simulations = 100
    home_scores, away_scores = simulate_multiple_matches(home_expected_goals, away_expected_goals, num_simulations)

    prediction_message = generate_prediction_message(home_team_data['name'], away_team_data['name'],
                                                     home_scores, away_scores, home_expected_goals, away_expected_goals)

    logging.info(f"Prediction: {prediction_message}")
    return prediction_message


def get_match_prediction_info(match_details: Dict[str, Any]) -> Dict[str, str]:
    """
    Extracts relevant prediction information from match details.

    Args:
        match_details (Dict[str, Any]): The match details.

    Returns:
        Dict[str, str]: A dictionary containing extracted prediction information.
    """
    event = match_details.get('event', {})
    tournament = event.get('tournament', {})
    return {
        'tournament_id': tournament.get('uniqueTournament', {}).get('id'),
        'season_id': event.get('season', {}).get('id'),
        'home_team_id': event.get('homeTeam', {}).get('id'),
        'away_team_id': event.get('awayTeam', {}).get('id'),
        'home_team_name': event.get('homeTeam', {}).get('name'),
        'away_team_name': event.get('awayTeam', {}).get('name')
    }


def extract_team_and_tournament_info(prediction_info: Dict[str, str]) -> Tuple[str, str, str, str]:
    """
    Extracts team and tournament information from prediction data.

    Args:
        prediction_info (Dict[str, str]): The prediction data.

    Returns:
        Tuple[str, str, str, str]: A tuple containing team and tournament IDs.
    """
    return (prediction_info['home_team_id'], prediction_info['away_team_id'],
            prediction_info['tournament_id'], prediction_info['season_id'])


def get_team_data(team_id: str, match_id: str, standings: Dict[str, Any], league_info: Dict[str, Any], is_home: bool) -> \
Dict[str, Any]:
    """
    Retrieves team data for prediction purposes.

    Args:
        team_id (str): The ID of the team.
        match_id (str): The ID of the match.
        standings (Dict[str, Any]): The standings data.
        league_info (Dict[str, Any]): The league information.
        is_home (bool): Whether the team is playing at home.

    Returns:
        Dict[str, Any]: A dictionary containing team data.
    """
    last_matches = get_last_three_matches(team_id)
    form, goals = calculate_form_and_goals(last_matches)
    odds = get_match_odds_1x2(match_id).get('Home' if is_home else 'Away', {'fractional_value': '1/1'})[
        'fractional_value']
    odds = calculate_decimal_odds(odds)
    position = get_team_position(standings, team_id)
    name = next((row['team']['name'] for row in standings['standings'][0]['rows'] if row['team']['id'] == team_id),
                None)
    return {
        'form': form,
        'odds': odds,
        'position': position,
        'goals': goals,
        'league_info': league_info,
        'is_home': is_home,
        'name': name  # Keep the name, but separate from the prediction factors
    }


def calculate_prediction_factor(form: int, odds: float, position: int, goals: int, league_info: Dict[str, Any],
                                is_home: bool) -> float:
    """
    Calculates a prediction factor based on team performance and odds.

    Args:
        form (int): The team's form.
        odds (float): The team's odds.
        position (int): The team's position in the standings.
        goals (int): The team's goals.
        league_info (Dict[str, Any]): The league information.
        is_home (bool): Whether the team is playing at home.

    Returns:
        float: The calculated prediction factor.
    """
    form_factor = min(form / 9, 1)
    odds_factor = 1 / (odds + 1)
    position_factor = (20 - min(position, 20)) / 20
    goals_factor = min(goals / (league_info.get('goals', 0) / (
            league_info.get('homeTeamWins', 0) + league_info.get('awayTeamWins', 0) + league_info.get('draws',
                                                                                                      0)) * 3), 1)
    home_advantage_factor = (league_info.get('homeTeamWins', 0) / (
            league_info.get('homeTeamWins', 0) + league_info.get('awayTeamWins', 0) + league_info.get('draws',
                                                                                                      0)) - 0.5) * (
                                1 if is_home else -1)
    return (form_factor * 0.35) + (odds_factor * 0.25) + (position_factor * 0.15) + (goals_factor * 0.15) + (
            home_advantage_factor * 0.1)


def calculate_expected_goals(home_factor: float, away_factor: float, league_info: Dict[str, Any]) -> Tuple[
    float, float]:
    """
    Calculates expected goals for a match based on team performance and league information.

    Args:
        home_factor (float): The home team's prediction factor.
        away_factor (float): The away team's prediction factor.
        league_info (Dict[str, Any]): The league information.

    Returns:
        Tuple[float, float]: A tuple containing expected goals for both teams.
    """
    league_avg_goals = league_info.get('goals', 0) / (
            league_info.get('homeTeamWins', 0) + league_info.get('awayTeamWins', 0) + league_info.get('draws', 0))
    return league_avg_goals * (1 + home_factor - away_factor) * 1.1, league_avg_goals * (1 + away_factor - home_factor)


def simulate_multiple_matches(home_expected_goals: float, away_expected_goals: float, num_simulations: int) -> Tuple[
    np.ndarray, np.ndarray]:
    """
    Simulates multiple matches to estimate win probabilities.

    Args:
        home_expected_goals (float): The home team's expected goals.
        away_expected_goals (float): The away team's expected goals.
        num_simulations (int): The number of simulations to run.

    Returns:
        Tuple[np.ndarray, np.ndarray]: A tuple containing simulated scores for both teams.
    """
    home_scores = np.random.poisson(home_expected_goals, num_simulations)
    away_scores = np.random.poisson(away_expected_goals, num_simulations)
    return home_scores, away_scores


def calculate_form_and_goals(matches: List[str]) -> Tuple[int, int]:
    """
    Calculates a team's form and goals from a list of matches.

    Args:
        matches (List[str]): A list of match strings.

    Returns:
        Tuple[int, int]: A tuple containing the team's form and goals.
    """

    form = 0
    goals = 0
    for match in matches:
        lines = match.split('\n')
        scores = lines[1].split(' - ')
        home_score = int(scores[0])
        away_score = int(scores[1])

        if lines[0].startswith("Home"):
            form += 3 if home_score > away_score else (1 if home_score == away_score else 0)
            goals += home_score
        else:
            form += 3 if away_score > home_score else (1 if home_score == away_score else 0)
            goals += away_score
    return form, goals


def calculate_decimal_odds(fractional_odds: str) -> float:
    """
    Converts fractional odds to decimal odds.

    Args:
        fractional_odds (str): The fractional odds.

    Returns:
        float: The decimal odds.
    """
    try:
        numerator, denominator = map(int, fractional_odds.split('/'))
        return 1 + (numerator / denominator)  # Return decimal odds
    except ValueError:
        logging.error(f"Invalid fractional odds format: {fractional_odds}")
        return 2.0  # Default to even odds if parsing fails


def generate_prediction_message(home_team_name: str, away_team_name: str, home_scores: np.ndarray,
                                away_scores: np.ndarray, home_expected_goals: float, away_expected_goals: float) -> str:
    """
    Generates a prediction message based on simulated match results.

    Args:
        home_team_name (str): The name of the home team.
        away_team_name (str): The name of the away team.
        home_scores (np.ndarray): The simulated scores for the home team.
        away_scores (np.ndarray): The simulated scores for the away team.
        home_expected_goals (float): The home team's expected goals.
        away_expected_goals (float): The away team's expected goals.

    Returns:
        str: A message containing the prediction results.
    """
    avg_home_score = np.mean(home_scores)
    avg_away_score = np.mean(away_scores)
    home_wins = sum(1 for h, a in zip(home_scores, away_scores) if h > a)
    away_wins = sum(1 for h, a in zip(home_scores, away_scores) if a > h)
    draws = sum(1 for h, a in zip(home_scores, away_scores) if h == a)
    home_win_prob = home_wins / len(home_scores)
    away_win_prob = away_wins / len(home_scores)
    draw_prob = draws / len(home_scores)
    return f"Predicted Average Score after {len(home_scores)} simulations:\n{home_team_name} {avg_home_score:.2f} - {avg_away_score:.2f} {away_team_name}\n\nWin Probabilities:\n{home_team_name}: {home_win_prob:.2%}\n{away_team_name}: {away_win_prob:.2%}\nDraw: {draw_prob:.2%}\n\nExpected Goals:\n{home_team_name}: {home_expected_goals:.2f}\n{away_team_name}: {away_expected_goals:.2f}\n"
