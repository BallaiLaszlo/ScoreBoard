import logging
import tkinter as tk
from tkinter import font, messagebox
from PIL import Image, ImageTk
import io
from ttkthemes import ThemedTk
from api_utils import *
from initialize import initialize_leagues
from redis_utils import *
from logger_setup import setup_logger
from button_actions import show_team_info
from getters import *
import time
from datetime import datetime, timedelta, date

setup_logger()
initialize_leagues()
class FootballApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Football Score Application")
        self.root.geometry("1000x800")
        self.root.configure(bg="#f0f8ff")

        # Font settings
        self.custom_font = font.Font(family="Helvetica", size=12, weight="bold")

        self.create_widgets()

    def create_widgets(self):
        # Frame for the selectors
        self.selectors_frame = tk.Frame(self.root, bg="#e0f7fa", padx=20, pady=20)
        self.selectors_frame.pack(pady=20, fill=tk.X)

        # League selector
        self.league_label = tk.Label(self.selectors_frame, text="Select League:", font=self.custom_font, bg="#e0f7fa", fg="#00796b")
        self.league_label.grid(row=0, column=0, padx=10, pady=5, sticky=tk.E)

        self.league_combobox = tk.ttk.Combobox(self.selectors_frame,
            values=[f"{league_id}: {league_name}" for league_id, league_name in get_league_name_list()],
            font=self.custom_font, width=25)
        self.league_combobox.bind("<<ComboboxSelected>>", self.update_league_info)
        self.league_combobox.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)

        # Frame for the league info box
        self.league_info_frame = tk.Frame(self.root, bg="#ffffff", bd=2, relief=tk.RIDGE, padx=20, pady=20)
        self.league_info_frame.pack(pady=20, fill=tk.X)

        # League info label
        self.league_info_label = tk.Label(self.league_info_frame, text="", font=self.custom_font, bg="#ffffff", justify=tk.LEFT, anchor="w")
        self.league_info_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # League icon label
        self.league_icon_label = tk.Label(self.league_info_frame, bg="#ffffff")
        self.league_icon_label.pack(side=tk.LEFT, padx=10)

        # Frame for the standings box
        self.standings_frame = tk.Frame(self.root, bg="#f2f2f2")
        self.standings_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

        # Add a canvas for scrolling
        self.standings_canvas = tk.Canvas(self.standings_frame, bg="#f2f2f2")
        self.standings_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add a scrollbar
        self.scrollbar = tk.Scrollbar(self.standings_frame, orient=tk.VERTICAL, command=self.standings_canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure the canvas to work with the scrollbar
        self.standings_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.standings_canvas.bind('<Configure>', lambda e: self.standings_canvas.configure(scrollregion=self.standings_canvas.bbox("all")))

        # Add a frame inside the canvas to hold the standings content
        self.standings_content_frame = tk.Frame(self.standings_canvas, bg="#f2f2f2")
        self.standings_canvas.create_window((0, 0), window=self.standings_content_frame, anchor="nw")

        # Label for standings
        self.matches_label = tk.Frame(self.standings_content_frame, bg="#f2f2f2")
        self.matches_label.pack()

        self.refresh_button = tk.Button(self.root, text="Refresh Standings", font=self.custom_font, bg="#00796b",
                                        fg="white", command=self.refresh_standings)
        self.refresh_button.pack(pady=10)

    def update_league_info(self, event):
        selected_value = self.league_combobox.get()
        league_id, league_name = selected_value.split(": ")

        logging.info(f"League selected: {league_name}")

        if league_id:
            try:
                league_info = fetch_league_info(league_id)
                if league_info:
                    league_info = league_info.decode('utf-8')
                    league_info_dict = json.loads(league_info)
                    logging.info(f"Fetched league info for {league_name} from API.")
                    self.display_league_info(league_info_dict)
                    self.display_league_icon(league_id)

                    season_id = get_first_season_id(league_id)
                    if season_id:
                        standings = fetch_standings(league_id, season_id)  # Fetch standings
                        if standings:
                            self.process_standings(standings, league_name)
                        else:
                            logging.warning(f"No valid standings found for {league_name}.")
                    else:
                        logging.warning(f"No seasons found for {league_name}.")
                else:
                    logging.warning(f"No league info returned for {league_name}.")
            except Exception as e:
                logging.error(f"Error while fetching league info: {e}")
        else:
            logging.warning(f"No league ID found for {league_name}.")

    def process_standings(self, standings, league_name):
        """
        Process the standings data.
        """
        if 'from_db' in standings and standings['from_db']:
            logging.info(f"Standings for {league_name} retrieved from the database.")
        else:
            logging.info(f"Fetched standings for {league_name} from API.")
        self.display_standings(standings)

    def refresh_standings(self):
        selected_value = self.league_combobox.get()

        if not selected_value:
            messagebox.showwarning("Warning", "Please select a league first!")
            return

        league_id, league_name = selected_value.split(": ")

        try:
            # Delete the standings from the Redis database
            delete_standings(league_id)
            logging.info(f"Deleted standings for {league_name} from database.")

            # Redownload the standings
            season_id = get_first_season_id(league_id)
            if season_id:
                standings = fetch_standings(league_id, season_id)
                if standings:
                    logging.info(f"Fetched new standings for {league_name} from API.")
                    self.process_standings(standings, league_name)
                else:
                    logging.warning(f"No valid standings found for {league_name}.")
                    messagebox.showinfo("Info", "No standings data available for this league.")
            else:
                logging.warning(f"No seasons found for {league_name}.")
                messagebox.showwarning("Warning", f"No season data found for {league_name}.")

        except Exception as e:
            logging.error(f"Error refreshing standings: {e}")
            messagebox.showerror("Error", "An error occurred while refreshing standings.")

    def display_league_info(self, league_info):
        """
        Displays the fetched league information.
        """
        if league_info and 'uniqueTournament' in league_info:
            league_name = league_info['uniqueTournament'].get('name', 'N/A')
            league_id = league_info['uniqueTournament'].get('id', 'N/A')
            most_titles_team = league_info['uniqueTournament'].get('mostTitlesTeams', [{}])[0].get('name', 'N/A')
            title_holder = league_info['uniqueTournament'].get('titleHolder', {}).get('name', 'N/A')

            info_text = (f"League: {league_name}\nID: {league_id}\nCurrent Title Holder: {title_holder}\n"
                         f"Most Titles Team: {most_titles_team}")
            self.league_info_label.config(text=info_text)

    def display_league_icon(self, league_id):
        """
        Displays the league icon based on the league ID.
        """
        image_data = fetch_league_image(league_id)
        if image_data:
            image = Image.open(io.BytesIO(image_data))
            image = image.resize((50, 50), Image.LANCZOS)
            league_icon = ImageTk.PhotoImage(image)
            self.league_icon_label.config(image=league_icon)
            self.league_icon_label.image = league_icon
        else:
            self.league_icon_label.config(image='')

    def display_standings(self, standings):
        """
        Displays the league standings in the GUI using a grid layout.
        """
        # Clear previous standings
        for widget in self.matches_label.winfo_children():
            widget.destroy()

        if standings and 'standings' in standings:
            rows = standings['standings'][0].get('rows', [])

            # Create headers
            headers = ["Position", "Team", "Matches", "Wins", "Draws", "Losses", "Points"]
            for col_index, header in enumerate(headers):
                header_label = tk.Label(self.matches_label, text=header, font=("Helvetica", 12, "bold"), bg="#e0f7fa")
                header_label.grid(row=0, column=col_index, padx=5, pady=5)

            # Add each team's information
            for row_index, row in enumerate(rows, start=1):
                self.create_standing_row(row, row_index)
        else:
            logging.warning("No standings data available to display.")
            # Show a message to the user if no standings are available
            no_data_label = tk.Label(self.matches_label, text="No standings data available.", bg="#f2f2f2",
                                     font=("Helvetica", 12))
            no_data_label.grid(row=1, column=0, columnspan=7, pady=10)

    def create_standing_row(self, row, row_index):
        position = row['position']
        team = row['team']['name']
        matches = row['matches']
        wins = row['wins']
        draws = row['draws']
        losses = row['losses']
        points = row['points']
        team_id = row['team']['id']

        team_button = tk.Button(self.matches_label, text=team,
                                command=lambda: show_team_info(team_id), bg="#00796b", fg="white",
                                font=self.custom_font)
        team_button.grid(row=row_index, column=1, padx=5, pady=5)

        matches_button = tk.Button(self.matches_label, text=matches,
                                   command=lambda: self.show_last_matches(team_id), bg="#00796b", fg="white",
                                   font=self.custom_font)
        matches_button.grid(row=row_index, column=2, padx=5, pady=5)


        row_data = [position, team_button, matches, wins, draws, losses, points]
        for col_index, data in enumerate(row_data):
            if col_index != 1 and col_index!= 2:  # Skip the team button column
                label = tk.Label(self.matches_label, text=data, bg="#f2f2f2", font=self.custom_font)
                label.grid(row=row_index, column=col_index, padx=5, pady=5)

    def create_standing_button(self, value, row_index, column, command=None):
        """
        Creates a button for standing values.
        """
        button = tk.Button(self.matches_label, text=value, bg="#b2ebf2", anchor="w", command=command)
        button.grid(row=row_index, column=column, sticky="ew", padx=5, pady=2)

    def show_last_matches(self, team_id):
        """
        Fetches and displays the last 3 matches for a given team ID.
        Checks Redis database first, and if not found, fetches from API.
        """
        try:
            # Try fetching the last matches
            logging.info(f"Fetching last matches for team ID {team_id}...")
            last_matches = get_last_three_matches(team_id)

            if not last_matches:
                logging.info(f"No cached matches found for team ID {team_id}. Fetching from API...")
                # Log the attempt to fetch from API
                logging.info(f"Fetching last matches for team ID {team_id} from API...")
                matches_data = fetch_previous_matches(team_id)

                if matches_data:
                    logging.info(f"Last matches for team ID {team_id} successfully fetched from API.")
                    # Store the retrieved last matches in Redis
                    logging.info(f"Storing last matches for team ID {team_id} in Redis...")
                    store_last_three_matches(team_id, format_last_three_matches(matches_data))

                    # Wait for a few seconds to ensure it's stored
                    logging.info(f"Waiting for 3 seconds to ensure last matches are stored in Redis...")
                    time.sleep(3)  # Delay for 3 seconds

                    # Retrieve the last matches again from Redis
                    logging.info(f"Retrieving last matches for team ID {team_id} from Redis again...")
                    last_matches = get_last_three_matches(team_id)

            if last_matches:
                # Create a new Toplevel window for displaying last matches
                matches_window = tk.Toplevel(self.root)
                matches_window.title(f"Last 3 Matches for Team ID: {team_id}")
                matches_window.geometry("400x300")

                # Display last matches
                logging.info(f"Displaying last matches for team ID {team_id}...")
                self.display_last_matches(last_matches, matches_window)
            else:
                # Handle the case where the last matches could not be fetched
                logging.error(f"Could not fetch last matches for team ID {team_id}.")
                messagebox.showerror("Error", f"Could not fetch last matches for team ID {team_id}.")
        except Exception as e:
            logging.error(f"Error fetching last matches for team ID {team_id}: {e}")
            messagebox.showerror("Error", f"Failed to fetch last matches for team ID {team_id}. Please try again.")

    def display_last_matches(self, last_matches, window):
        # Format matches for display
        formatted_matches = '\n\n'.join(last_matches)

        # Display formatted matches
        matches_label = tk.Label(window, text=formatted_matches, padx=20, pady=20)
        matches_label.pack()