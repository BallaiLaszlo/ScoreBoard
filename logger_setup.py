# logger_setup.py
import logging

def setup_logger():
    """
    Sets up the logger to write logs to log.txt.
    """
    logging.basicConfig(
        filename='log.txt',
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

setup_logger()
