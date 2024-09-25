import tkinter as tk
from tkinter import ttk
from tkinter import font
from PIL import Image, ImageTk
import io
from ttkthemes import ThemedTk
from api_utils import fetch_league_info, fetch_teams, fetch_matches, get_league_names, get_league_id, fetch_league_image

# Function to update league information when a league is selected

def update_league_info(event):
    league_name = league_combobox.get()
    league_id = get_league_id(league_name)
    if league_id:
        league_info = fetch_league_info(league_id)
        display_league_info(league_info)
        update_teams()
        display_league_icon(league_id)  # Now display icon instead of background

# Function to display the fetched league information
def display_league_info(league_info):
    league_name = league_info['uniqueTournament']['name']
    league_id = league_info['uniqueTournament']['id']
    most_titles_team = league_info['uniqueTournament']['mostTitlesTeams'][0]['name'] if league_info['uniqueTournament'].get('mostTitlesTeams') else 'N/A'
    title_holder = league_info['uniqueTournament']['titleHolder']['name'] if league_info['uniqueTournament'].get('titleHolder') else 'N/A'

    info_text = f"League: {league_name}\nID: {league_id}\nCurrent Title Holder: {title_holder}\nMost Titles Team: {most_titles_team}"
    league_info_label.config(text=info_text)

# Function to display the league icon next to the league info
def display_league_icon(league_id):
    image_data = fetch_league_image(league_id)

    if image_data:
        # Convert the image data to a format that Tkinter can use
        image = Image.open(io.BytesIO(image_data))
        image = image.resize((50, 50), Image.LANCZOS)  # Adjust the size of the icon

        # Convert image to Tkinter format and display next to league info
        league_icon = ImageTk.PhotoImage(image)
        league_icon_label.config(image=league_icon)
        league_icon_label.image = league_icon  # Keep reference to avoid garbage collection
    else:
        league_icon_label.config(image='')  # Remove icon if no image is available

# Function to update the team selector when a league is selected
def update_teams():
    league_name = league_combobox.get()
    league_id = get_league_id(league_name)
    if league_id:
        teams = fetch_teams(league_id)
        team_combobox['values'] = [team['name'] for team in teams]
        team_combobox.set('')

# Function to display matches when a team is selected
def update_matches(event):
    team_name = team_combobox.get()
    league_name = league_combobox.get()
    league_id = get_league_id(league_name)
    if league_id:
        teams = fetch_teams(league_id)
        team_id = next((team['id'] for team in teams if team['name'] == team_name), None)
        if team_id:
            matches = fetch_matches(team_id)
            matches_text = '\n'.join(
                [f"{match['home_team']} vs {match['away_team']} - {match['date']}" for match in matches])
            matches_label.config(text=matches_text)

# Main application window using ThemedTk for improved UI
root = ThemedTk(theme="arc")  # Add modern theme support
root.title("Football Score Application")
root.geometry("1000x800")
root.configure(bg="#f0f8ff")  # Subtle background color for the app

# Font settings
custom_font = font.Font(family="Helvetica", size=12, weight="bold")

# Frame for the selectors
selectors_frame = tk.Frame(root, bg="#e0f7fa", padx=20, pady=20)
selectors_frame.pack(pady=20, fill=tk.X)

# Grid configuration for better layout control
selectors_frame.grid_rowconfigure(0, weight=1)
selectors_frame.grid_columnconfigure(0, weight=1)
selectors_frame.grid_columnconfigure(1, weight=1)
selectors_frame.grid_columnconfigure(2, weight=1)
selectors_frame.grid_columnconfigure(3, weight=1)

# League selector
league_label = tk.Label(selectors_frame, text="Select League:", font=custom_font, bg="#e0f7fa", fg="#00796b")
league_label.grid(row=0, column=0, padx=10, pady=5, sticky=tk.E)

league_combobox = ttk.Combobox(selectors_frame, values=get_league_names(), font=custom_font, width=25)
league_combobox.bind("<<ComboboxSelected>>", update_league_info)
league_combobox.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)

# Team selector
team_label = tk.Label(selectors_frame, text="Select Team:", font=custom_font, bg="#e0f7fa", fg="#00796b")
team_label.grid(row=0, column=2, padx=10, pady=5, sticky=tk.E)

team_combobox = ttk.Combobox(selectors_frame, font=custom_font, width=25)
team_combobox.bind("<<ComboboxSelected>>", update_matches)
team_combobox.grid(row=0, column=3, padx=10, pady=5, sticky=tk.W)

# Frame for the league info box
league_info_frame = tk.Frame(root, bg="#ffffff", bd=2, relief=tk.RIDGE, padx=20, pady=20)
league_info_frame.pack(pady=20, fill=tk.X)

# League info label
league_info_label = tk.Label(league_info_frame, text="", font=custom_font, bg="#ffffff", justify=tk.LEFT, anchor="w")
league_info_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# League icon label (this will hold the icon image)
league_icon_label = tk.Label(league_info_frame, bg="#ffffff")
league_icon_label.pack(side=tk.LEFT, padx=10)

# Matches display
matches_label = tk.Label(root, text="", font=custom_font, bg="#f2f2f2", justify=tk.LEFT)
matches_label.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

# Ensure responsive layout
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

# Run the application loop
root.mainloop()
