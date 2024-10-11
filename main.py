from ttkthemes.themed_tk import ThemedTk
from football_app import FootballApp
from logger_setup import setup_logger
import logging

if __name__ == "__main__":
    try:
        setup_logger()
        logging.info("Application startup initiated.")
        root = ThemedTk(theme="arc")
        app = FootballApp(root)
        logging.info("FootballApp successfully initialized.")
        root.mainloop()
        logging.info("Main loop running.")
    except Exception as e:
        logging.error(f"An error occurred during application initialization or runtime: {e}")
        print(f"An error occurred: {e}")
