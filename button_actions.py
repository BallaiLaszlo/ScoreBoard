from getters import get_team_info
from redis_utils import store_team_info
from api_utils import fetch_team_info
import logging
import tkinter as tk
from tkinter import messagebox
import time  # Import time for sleep function


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
    # Create labels to display team info
    team_name_label = tk.Label(team_window, text=f"Team Name: {team_info['name']}", font=("Helvetica", 14))
    team_name_label.pack(pady=10)

    # Add additional info as needed
    if 'manager' in team_info:
        manager_label = tk.Label(team_window, text=f"Manager: {team_info['manager']}")
        manager_label.pack(pady=10)

    if 'venue' in team_info:
        venue_label = tk.Label(team_window, text=f"Venue: {team_info['venue']}")
        venue_label.pack(pady=10)

    if 'location' in team_info:
        location_label = tk.Label(team_window, text=f"Location: {team_info['location']}")
        location_label.pack(pady=10)

    if 'country' in team_info:
        country_label = tk.Label(team_window, text=f"Country: {team_info['country']}")
        country_label.pack(pady=10)

    # Close button
    close_button = tk.Button(team_window, text="Close", command=team_window.destroy)
    close_button.pack(pady=10)
