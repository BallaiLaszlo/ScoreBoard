from tkinter import messagebox
from getters import get_team_info

def show_team_info(team_id):
    """
    Displays detailed team information in a message box.

    Args:
        team_id (str): The ID of the team.
    """
    # Fetch the team info using the getter function
    team_info = get_team_info(team_id)

    if team_info:
        info_message = (
            f"Team: {team_info['name']}\n"
            f"Location: {team_info['location']}\n"
            f"Manager: {team_info.get('manager', 'N/A')}\n"
            f"Venue: {team_info.get('venue', 'N/A')}\n"
            f"Venue Location: {team_info.get('venue_location', 'N/A')}\n"
            f"Capacity: {team_info.get('venue_capacity', 'N/A')}\n"
            f"Team Colors: {team_info['team_colors']}\n"
            f"Country: {team_info.get('country', 'N/A')}"
        )
    else:
        info_message = "No information available for this team."

    # Display the team info in a messagebox
    messagebox.showinfo("Team Information", info_message)
