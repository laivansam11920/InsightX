from app import create_app
from config import Config
from time import sleep
import os

app = create_app()

if os.getenv("WERKZEUG_RUN_MAIN") != "true":
    print("InsightX has running", end="", flush=True)
    for i in range(3):
        print(".", end="", flush=True)
        sleep(0.5)
    print()

if __name__ == "__main__":
    app.run(port=Config.PORT, debug=True)
