import logging
import tkinter as tk
from tkinter import messagebox

from redis_connection import r
from redis_utils import store_team_info, store_last_three_matches
from api_utils import fetch_team_info, fetch_previous_matches
from getters import get_team_info, get_last_three_matches, format_last_three_matches
import time


def show_team_info(team_id):
    """
    Fetches and displays team information. Checks Redis database first,
    and if not found, fetches from API.
    """

    # Create a new Toplevel window for displaying team info
    team_window = tk.Toplevel()
    team_window.title("Team Information")
    team_window.geometry("400x300")

    # Create a loading message
    loading_message = messagebox.showinfo("Loading", "Fetching team information... Please wait.")

    # Function to handle fetching and displaying team info
    def fetch_and_display():
        # Try fetching the team information
        try:
            # Attempt to retrieve team info from the Redis database
            team_info = get_team_info(team_id)

            if team_info:
                logging.info(f"Team info for ID {team_id} retrieved from the database.")
                # Display team info immediately if found in Redis
                display_team_info(team_info, team_window)
            else:
                # Log the attempt to fetch from API
                logging.info(f"Fetching team info for ID {team_id} from API.")
                # Fetch team info from API
                team_info = fetch_team_info(team_id)

                if team_info:
                    # Store the retrieved team info in Redis
                    store_team_info(team_id, team_info)

                    # Wait for a few seconds to ensure it's stored
                    time.sleep(3)  # Delay for 3 seconds

                    # Retrieve the team info again from Redis
                    team_info = get_team_info(team_id)

                    if team_info:
                        # Display the team info
                        display_team_info(team_info, team_window)
                    else:
                        # Handle the case where the team info could not be fetched after storing
                        messagebox.showerror("Error", f"Could not fetch team info for ID {team_id}.")
                        logging.error(f"Could not fetch team info for ID {team_id} after storing.")
                else:
                    # Handle the case where the team info could not be fetched from the API
                    messagebox.showerror("Error", f"Could not fetch team info for ID {team_id}.")
                    logging.error(f"Could not fetch team info for ID {team_id}.")

        except Exception as e:
            logging.error(f"Error fetching team info for team ID {team_id}: {e}")
            messagebox.showerror("Error", f"Failed to fetch team info for team ID {team_id}. Please try again.")
        finally:
            # Close the loading message if it's still open
            if loading_message:
                loading_message.destroy()

    # Delay the fetching process to allow the loading message to display
    team_window.after(1000, fetch_and_display)  # Adjust delay as needed


def display_team_info(team_info, team_window):
    """
    Displays the team information in the specified Tkinter window.
    """
    # Extract team details
    team_name = team_info.get('name', 'Unknown')
    manager_name = team_info.get('manager', 'Unknown')
    venue = team_info.get('venue', 'Unknown')
    venue_capacity = team_info.get('venue_capacity', 'Unknown')
    location = team_info.get('location', 'Unknown')
    country = team_info.get('country', 'Unknown')
    team_colors = team_info.get('team_colors', {})

    # Extracting team colors
    primary_color = team_colors.get('primary', '#ffffff')  # Default to white if not available
    secondary_color = team_colors.get('secondary', '#000000')  # Default to black if not available

    # Set the background color of the team window
    team_window.configure(bg=primary_color)

    # Determine text color based on the background color
    text_color = 'white' if primary_color == '#000000' else 'black'

    # Create labels to display team info with specified formatting
    label_font = ("Helvetica", 16, "bold")  # Larger font size and bold

    team_name_label = tk.Label(team_window, text=f"Team Name: {team_name}", font=label_font, bg=primary_color,
                               fg=text_color)
    team_name_label.pack(pady=10)

    manager_label = tk.Label(team_window, text=f"Manager: {manager_name}", font=label_font, bg=primary_color,
                             fg=text_color)
    manager_label.pack(pady=10)

    venue_label = tk.Label(team_window, text=f"Venue: {venue}", font=label_font, bg=primary_color, fg=text_color)
    venue_label.pack(pady=10)

    venue_capacity_label = tk.Label(team_window, text=f"Venue Capacity: {venue_capacity}", font=label_font,
                                    bg=primary_color, fg=text_color)
    venue_capacity_label.pack(pady=10)

    location_label = tk.Label(team_window, text=f"Location: {location}", font=label_font, bg=primary_color,
                              fg=text_color)
    location_label.pack(pady=10)

    country_label = tk.Label(team_window, text=f"Country: {country}", font=label_font, bg=primary_color, fg=text_color)
    country_label.pack(pady=10)

    # Close button
    close_button = tk.Button(team_window, text="Close", command=team_window.destroy, bg=secondary_color, fg='black')
    close_button.pack(pady=10)
