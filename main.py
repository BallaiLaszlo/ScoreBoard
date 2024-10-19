from ttkthemes import ThemedTk
from football_app import FootballApp
from logger_setup import setup_logger
import logging

if __name__ == "__main__":
    try:
        setup_logger()
        logging.info("Application startup initiated.")

        # Create the themed root window
        root = ThemedTk(theme="arc")

        # Initialize the FootballApp
        app = FootballApp(root)

        logging.info("FootballApp successfully initialized.")

        # Start the main event loop
        root.mainloop()

        logging.info("Main loop running.")
    except Exception as e:
        logging.error(f"An error occurred during application initialization or runtime: {e}")
        print(f"An error occurred: {e}")
