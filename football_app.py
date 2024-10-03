import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk
import io
from ttkthemes import ThemedTk
from api_utils import fetch_league_info, get_league_names, get_league_id, fetch_league_image, fetch_standings, print_standings, get_first_season_id


def update_league_info(event):
    """
    Updates league information when a league is selected.

    Args:
        event: The event triggered by selecting a league from the combobox.
    """
    league_name = league_combobox.get()
    league_id = get_league_id(league_name)

    if league_id:
        league_info = fetch_league_info(league_id)

        if league_info:
            display_league_info(league_info)
            display_league_icon(league_id)

            season_id = get_first_season_id(league_name)
            if season_id:
                standings = fetch_standings(league_id, season_id)
                if standings:
                    display_standings(standings)
                    print_standings(standings)
                else:
                    print("No standings data returned for the selected league.")
            else:
                print("No valid season ID found for the selected league.")


def display_league_info(league_info):
    """
    Displays the fetched league information.

    Args:
        league_info (dict): The league information dictionary.
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

    Args:
        league_id (str): The ID of the league.
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

    Args:
        standings (dict): The standings information dictionary.
    """
    matches_label.config(text="")
    if standings and 'standings' in standings:
        rows = standings['standings'][0].get('rows', [])
        standings_text = ""

        for row in rows:
            team = row['team']['name']
            position = row['position']
            points = row['points']
            matches = row['matches']
            wins = row['wins']
            draws = row['draws']
            losses = row['losses']

            standings_text += (f"Position: {position} | Team: {team} | Matches: {matches} | "
                               f"Wins: {wins} | Draws: {draws} | Losses: {losses} | Points: {points}\n")

        matches_label.config(text=standings_text)


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

# League Table display
matches_label = tk.Label(root, text="", font=custom_font, bg="#f2f2f2", justify=tk.LEFT)
matches_label.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

# Run the application loop
root.mainloop()
