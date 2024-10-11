# logger_setup.py
import logging

def setup_logger(log_level=logging.DEBUG):
    """
    Sets up the logger to write logs to log.txt.

    Args:
        log_level (int): Logging level (DEBUG, INFO, WARNING, etc.)
    """
    logging.basicConfig(
        filename='log.txt',
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

setup_logger()
