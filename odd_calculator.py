import json
import logging
from tkinter import messagebox

import numpy as np

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


def fetch_match_odds(match_id):
    url = f"https://{api_host}/api/match/{match_id}/odds"
    response = make_api_request(url)

    if response:
        logging.info(f"Match odds for match ID {match_id} successfully fetched from API.")
        return response
    else:
        logging.error(f"Failed to fetch match odds for match ID {match_id} from API.")
        return None


def store_match_odds(match_id, match_odds):
    if match_odds:
        logging.info(f"Storing match odds for match ID {match_id}: {match_odds}")
        r.set(f'match_odds:{match_id}', json.dumps(match_odds))
        logging.info(f"Stored match odds for match ID {match_id} in Redis.")
    else:
        logging.warning(f"No match odds to store for match ID {match_id}.")


def get_match_odds(match_id):
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


def calculate_percentage(odds):
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


def get_team_position(standings, team_id):
    for row in standings['standings'][0]['rows']:
        if row['team']['id'] == team_id:
            return row['position']
    return 0


def get_league_info(tournament_id, season_id):
    url = f"https://{api_host}/api/tournament/{tournament_id}/season/{season_id}/info"
    league_info = make_api_request(url)
    if league_info and 'info' in league_info:
        return league_info['info']
    return None


def predict_match(match_id):
    """
    Predicts the match score based on form, odds, league standing, recent goals, and league information.
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


def get_match_prediction_info(match_details):
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


def extract_team_and_tournament_info(prediction_info):
    return (prediction_info['home_team_id'], prediction_info['away_team_id'],
            prediction_info['tournament_id'], prediction_info['season_id'])


def get_team_data(team_id, match_id, standings, league_info, is_home):
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


def calculate_prediction_factor(form, odds, position, goals, league_info, is_home):
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


def calculate_expected_goals(home_factor, away_factor, league_info):
    league_avg_goals = league_info.get('goals', 0) / (
            league_info.get('homeTeamWins', 0) + league_info.get('awayTeamWins', 0) + league_info.get('draws', 0))
    return league_avg_goals * (1 + home_factor - away_factor) * 1.1, league_avg_goals * (1 + away_factor - home_factor)


def simulate_multiple_matches(home_expected_goals, away_expected_goals, num_simulations):
    home_scores = np.random.poisson(home_expected_goals, num_simulations)
    away_scores = np.random.poisson(away_expected_goals, num_simulations)
    return home_scores, away_scores


def calculate_form_and_goals(matches):
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


def calculate_decimal_odds(fractional_odds):
    try:
        numerator, denominator = map(int, fractional_odds.split('/'))
        return 1 + (numerator / denominator)  # Return decimal odds
    except ValueError:
        logging.error(f"Invalid fractional odds format: {fractional_odds}")
        return 2.0  # Default to even odds if parsing fails


def generate_prediction_message(home_team_name, away_team_name, home_scores, away_scores, home_expected_goals,
                                away_expected_goals):
    avg_home_score = np.mean(home_scores)
    avg_away_score = np.mean(away_scores)
    home_wins = sum(1 for h, a in zip(home_scores, away_scores) if h > a)
    away_wins = sum(1 for h, a in zip(home_scores, away_scores) if a > h)
    draws = sum(1 for h, a in zip(home_scores, away_scores) if h == a)
    home_win_prob = home_wins / len(home_scores)
    away_win_prob = away_wins / len(home_scores)
    draw_prob = draws / len(home_scores)
    return f"Predicted Average Score after {len(home_scores)} simulations:\n{home_team_name} {avg_home_score:.2f} - {avg_away_score:.2f} {away_team_name}\n\nWin Probabilities:\n{home_team_name}: {home_win_prob:.2%}\n{away_team_name}: {away_win_prob:.2%}\nDraw: {draw_prob:.2%}\n\nExpected Goals:\n{home_team_name}: {home_expected_goals:.2f}\n{away_team_name}: {away_expected_goals:.2f}\n"
