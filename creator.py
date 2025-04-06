from modules.config import Config
from modules.seleniumbot import runbot
from modules.requestbot import runBot

def accountCreator():
    try:
        # Use the Selenium bot
        runbot()

        # If you prefer using the requests-based bot, comment above and uncomment below:
        # runBot()

    except Exception as e:
        print(f"[ERROR] Something went wrong: {e}")
        print("It's possible your IP is banned or a dependency is misconfigured.")

if __name__ == "__main__":
    accountCreator()
