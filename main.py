from ttkthemes.themed_tk import ThemedTk

from football_app import FootballApp

if __name__ == "__main__":
    root = ThemedTk(theme="arc")
    app = FootballApp(root)
    root.mainloop()
