import requests
import json

# Load settings
with open('settings.json', 'r') as f:
    settings = json.load(f)

api_key = settings["api_key"]
api_host = "footapi7.p.rapidapi.com"

# Extract leagues from settings
leagues = settings["leagues"]

# Create a dictionary for league ID lookup
league_id_lookup = {league['name']: league['id'] for league in leagues}

# General request handler
def make_api_request(url):
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': api_host
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 429:
        print("Error: You have exceeded the number of allowed requests. Please try again later.")
        return None
    elif response.status_code != 200:
        print(f"Error: Unable to fetch data (Status Code: {response.status_code})")
        return None

    if "application/json" in response.headers.get("Content-Type", ""):
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            print("Error: Failed to parse JSON response.")
            return None
    else:
        return response.content  # Return raw content for non-JSON data

# Fetch league information
# Fetch league information and retrieve the season IDs
# Fetch league information (no need to fetch seasons from API)
def fetch_league_info(league_id):
    url = f"https://{api_host}/api/tournament/{league_id}"
    league_info = make_api_request(url)
    return league_info  # Only return league info

# Fetch first season ID from settings
def get_first_season_id(league_name):
    league = next((league for league in leagues if league['name'] == league_name), None)
    return league['seasons'][0] if league and 'seasons' in league and league['seasons'] else None

# Fetch standings based on league_id and season_id
def fetch_standings(league_id, season_id):
    url = f"https://{api_host}/api/tournament/{league_id}/season/{season_id}/standings/total"
    return make_api_request(url)



# Fetch league image
def fetch_league_image(league_id):
    url = f"https://{api_host}/api/tournament/{league_id}/image"
    return make_api_request(url)

# Fetch standings based on the league_id and season_id
def fetch_standings(league_id, season_id):
    url = f"https://{api_host}/api/tournament/{league_id}/season/{season_id}/standings/total"
    return make_api_request(url)

# Print standings to console
def print_standings(standings):
    if standings and 'standings' in standings:
        rows = standings['standings'][0].get('rows', [])
        if rows:  # Check if there are rows to print
            print("League Standings:")
            for row in rows:
                team = row['team']['name']
                position = row['position']
                points = row['points']
                matches = row['matches']
                wins = row['wins']
                draws = row['draws']
                losses = row['losses']

                # Print the team's standings to the console
                print(f"Position: {position} | Team: {team} | Matches: {matches} | "
                      f"Wins: {wins} | Draws: {draws} | Losses: {losses} | Points: {points}")
        else:
            print("No standings rows found.")
    else:
        print("Standings data is not in the expected format.")

# Helper functions to get league names and IDs
def get_league_names():
    return [league['name'] for league in leagues]

def get_league_id(league_name):
    return league_id_lookup.get(league_name)
