from ttkthemes.themed_tk import ThemedTk

from football_app import FootballApp
from logger_setup import setup_logger

if __name__ == "__main__":
    setup_logger()
    root = ThemedTk(theme="arc")
    app = FootballApp(root)
    root.mainloop()
