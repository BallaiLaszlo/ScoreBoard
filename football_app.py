import logging
import tkinter as tk
from tkinter import font, ttk
from PIL import Image, ImageTk
import io
from ttkthemes import ThemedTk
from api_utils import *
from getters import *
from redis_utils import *
from logger_setup import setup_logger
from button_actions import show_team_info
from initialize import init_leagues


setup_logger()

# Initialize leagues before creating the GUI
init_leagues()

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

        self.league_combobox = ttk.Combobox(self.selectors_frame, values=[f"{league_id}: {league_name}" for league_id, league_name in get_league_name_list()], font=self.custom_font, width=25)
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

    def update_league_info(self, event):
        """
        Updates league information when a league is selected.

        Args:
            event: The event triggered by selecting a league from the combobox.
        """
        selected_value = self.league_combobox.get()
        league_id, league_name = selected_value.split(": ")

        logging.info(f"League selected: {league_name}")

        if league_id:
            league_info = fetch_league_info(league_id)
            if league_info:
                league_info = league_info.decode('utf-8')  # Decode the bytes object into a string
                league_info_dict = json.loads(league_info)  # Parse the JSON string into a dictionary

                logging.info(f"Fetched league info for {league_name} from API.")
                self.display_league_info(league_info_dict)
                self.display_league_icon(league_id)

                season_id = get_first_season_id(league_id)
                if season_id:
                    standings = get_standings(league_id, season_id)
                    if standings:
                        standings = fetch_standings(league_id, season_id)
                        if standings:
                            if 'from_db' in standings and standings['from_db']:
                                logging.info(f"Standings for {league_name} retrieved from the database.")
                            else:
                                logging.info(f"Fetched standings for {league_name} from API.")
                            self.display_standings(standings)
                        else:
                            logging.warning(f"No standings data returned for {league_name}.")
                    else:
                        logging.warning(f"No valid season ID found for {league_name}.")
                else:
                    logging.warning(f"No seasons found for {league_name}.")
            else:
                logging.warning(f"No league info returned for {league_name}.")
        else:
            logging.warning(f"No league ID found for {league_name}.")

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
                position = row['position']
                team = row['team']['name']
                matches = row['matches']
                wins = row['wins']
                draws = row['draws']
                losses = row['losses']
                points = row['points']

                # Create a button for the team name
                team_button = tk.Button(self.matches_label, text=team, command=lambda t=team: show_team_info(t),
                                        bg="#b2ebf2", anchor="w")
                team_button.grid(row=row_index, column=1, sticky="ew", padx=5, pady=2)

                # Create buttons for other columns with message boxes
                matches_button = tk.Button(self.matches_label, text=matches,
                                           command=lambda m=matches: self.show_info("Matches", m), bg="#b2ebf2")
                matches_button.grid(row=row_index, column=2, padx=5, pady=2)

                wins_button = tk.Button(self.matches_label, text=wins, command=lambda w=wins: self.show_info("Wins", w),
                                        bg="#b2ebf2")
                wins_button.grid(row=row_index, column=3, padx=5, pady=2)

                draws_button = tk.Button(self.matches_label, text=draws,
                                         command=lambda d=draws: self.show_info("Draws", d), bg="#b2ebf2")
                draws_button.grid(row=row_index, column=4, padx=5, pady=2)

                losses_button = tk.Button(self.matches_label, text=losses,
                                          command=lambda l=losses: self.show_info("Losses", l), bg="#b2ebf2")
                losses_button.grid(row=row_index, column=5, padx=5, pady=2)

                points_button = tk.Button(self.matches_label, text=points,
                                          command=lambda p=points: self.show_info("Points", p), bg="#b2ebf2")
                points_button.grid(row=row_index, column=6, padx=5, pady=2)

                # Label for position (as it's not clickable)
                tk.Label(self.matches_label, text=position, bg="#e0f7fa").grid(row=row_index, column=0, padx=5, pady=2)
        else:
            logging.warning("No standings data available to display.")

    def show_info(self, category, value):
        """
        Displays information about a specific category in a message box.

        Args:
            category: The category of the clicked button (e.g., Matches, Wins).
            value: The value of the clicked button.
        """
        message = f"{category}: {value}"
        tk.messagebox.showinfo("Information", message)

    def handle_click(self, category, value):
        """
        Handles clicks on standings buttons.

        Args:
            category: The category of the clicked button (e.g., Matches, Wins).
            value: The value of the clicked button.
        """
        logging.info(f"{category} button clicked with value: {value}")
        # Here you can implement further actions based on the button clicked.
        # For example, showing a popup with detailed stats or navigating to a different view.

