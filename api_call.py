import json
import logging
import requests

logging.basicConfig(
    filename='log.txt',  # Log file name
    level=logging.INFO,  # Log level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log message format
)

# Load API settings from the JSON file
with open('settings.json', 'r') as f:
    settings = json.load(f)

api_key = settings["api_key"]
api_host = "footapi7.p.rapidapi.com"


def make_api_request(url):
    """
    General request handler to make API calls.

    Args:
        url (str): The API endpoint to call.

    Returns:
        dict or bytes: The JSON response if the content type is JSON, otherwise raw content.
    """
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': api_host
    }

    try:
        logging.info(f"Making API request to {url}.")
        response = requests.get(url, headers=headers)
        logging.info(f"API response status code for {url}: {response.status_code}")

        if response.status_code == 429:
            logging.error("Error: You have exceeded the number of allowed requests. Please try again later.")
            return None
        elif response.status_code != 200:
            logging.error(f"Error: Unable to fetch data (Status Code: {response.status_code}).")
            return None

        if "application/json" in response.headers.get("Content-Type", ""):
            try:
                json_data = response.json()
                logging.info("Successfully parsed JSON response.")
                return json_data
            except requests.exceptions.JSONDecodeError:
                logging.error("Error: Failed to parse JSON response.")
                return None
        else:
            logging.warning("Response content is not JSON, returning raw content.")
            return response.content  # Return raw content for non-JSON data

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None
