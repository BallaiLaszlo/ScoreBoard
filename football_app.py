import logging
import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk
import io
from ttkthemes import ThemedTk
from api_utils import fetch_league_info, get_league_names, get_league_id, fetch_league_image, fetch_standings, get_first_season_id
from logger_setup import setup_logger

setup_logger()

def update_league_info(event):
    """
    Updates league information when a league is selected.

    Args:
        event: The event triggered by selecting a league from the combobox.
    """
    league_name = league_combobox.get()
    league_id = get_league_id(league_name)

    logging.info(f"League selected: {league_name}")

    if league_id:
        league_info = fetch_league_info(league_id)

        if league_info:
            logging.info(f"Fetched league info for {league_name} from API.")
            display_league_info(league_info)
            display_league_icon(league_id)

            season_id = get_first_season_id(league_name)
            if season_id:
                standings = fetch_standings(league_id, season_id)
                if standings:
                    if 'from_db' in standings and standings['from_db']:
                        logging.info(f"Standings for {league_name} retrieved from the database.")
                    else:
                        logging.info(f"Fetched standings for {league_name} from API.")
                    display_standings(standings)
                else:
                    logging.warning(f"No standings data returned for {league_name}.")
            else:
                logging.warning(f"No valid season ID found for {league_name}.")
        else:
            logging.warning(f"No league info returned for {league_name}.")
    else:
        logging.warning(f"No league ID found for {league_name}.")


def display_league_info(league_info):
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
        league_info_label.config(text=info_text)

def display_league_icon(league_id):
    """
    Displays the league icon based on the league ID.
    """
    image_data = fetch_league_image(league_id)
    if image_data:
        image = Image.open(io.BytesIO(image_data))
        image = image.resize((50, 50), Image.LANCZOS)
        league_icon = ImageTk.PhotoImage(image)
        league_icon_label.config(image=league_icon)
        league_icon_label.image = league_icon
    else:
        league_icon_label.config(image='')

def display_standings(standings):
    """
    Displays the league standings in the GUI.
    """
    # Clear the previous standings
    for widget in standings_content_frame.winfo_children():
        widget.destroy()

    if standings and 'standings' in standings:
        rows = standings['standings'][0].get('rows', [])
        for row in rows:
            team = row['team']['name']
            position = row['position']
            points = row['points']
            matches = row['matches']
            wins = row['wins']
            draws = row['draws']
            losses = row['losses']

            # Add the standings rows as labels inside the standings_content_frame
            standings_label = tk.Label(
                standings_content_frame, text=(f"Position: {position} | Team: {team} | "
                                               f"Matches: {matches} | Wins: {wins} | "
                                               f"Draws: {draws} | Losses: {losses} | Points: {points}"),
                font=custom_font, bg="#f2f2f2", justify=tk.LEFT, anchor="w"
            )
            standings_label.pack(fill=tk.X, padx=10, pady=2)

# Main application window using ThemedTk
root = ThemedTk(theme="arc")
root.title("Football Score Application")
root.geometry("1000x800")
root.configure(bg="#f0f8ff")

# Font settings
custom_font = font.Font(family="Helvetica", size=12, weight="bold")

# Frame for the selectors
selectors_frame = tk.Frame(root, bg="#e0f7fa", padx=20, pady=20)
selectors_frame.pack(pady=20, fill=tk.X)

# League selector
league_label = tk.Label(selectors_frame, text="Select League:", font=custom_font, bg="#e0f7fa", fg="#00796b")
league_label.grid(row=0, column=0, padx=10, pady=5, sticky=tk.E)

league_combobox = tk.ttk.Combobox(selectors_frame, values=get_league_names(), font=custom_font, width=25)
league_combobox.bind("<<ComboboxSelected>>", update_league_info)
league_combobox.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)

# Frame for the league info box
league_info_frame = tk.Frame(root, bg="#ffffff", bd=2, relief=tk.RIDGE, padx=20, pady=20)
league_info_frame.pack(pady=20, fill=tk.X)

# League info label
league_info_label = tk.Label(league_info_frame, text="", font=custom_font, bg="#ffffff", justify=tk.LEFT, anchor="w")
league_info_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# League icon label
league_icon_label = tk.Label(league_info_frame, bg="#ffffff")
league_icon_label.pack(side=tk.LEFT, padx=10)

# Frame for the standings box
standings_frame = tk.Frame(root, bg="#f2f2f2")
standings_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

# Add a canvas for scrolling
standings_canvas = tk.Canvas(standings_frame, bg="#f2f2f2")
standings_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Add a scrollbar
scrollbar = tk.Scrollbar(standings_frame, orient=tk.VERTICAL, command=standings_canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Configure the canvas to work with the scrollbar
standings_canvas.configure(yscrollcommand=scrollbar.set)
standings_canvas.bind('<Configure>', lambda e: standings_canvas.configure(scrollregion=standings_canvas.bbox("all")))

# Add a frame inside the canvas to hold the standings content
standings_content_frame = tk.Frame(standings_canvas, bg="#f2f2f2")

# Add the frame to the canvas
standings_canvas.create_window((0, 0), window=standings_content_frame, anchor="nw")

# Run the application loop
root.mainloop()
