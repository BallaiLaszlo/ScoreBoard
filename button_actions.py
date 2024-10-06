# button_actions.py

import tkinter as tk
from tkinter import messagebox

def show_team_info(team_name):
    """
    Displays team information in a message box.

    Args:
        team_name (str): The name of the team.
    """
    # Fetch or generate more information about the team here.
    info = f"Information about {team_name}."
    messagebox.showinfo("Team Information", info)
