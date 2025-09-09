import json
import os

COFFEE_DIR = os.path.expanduser("~/.tmux/coffee")
LOCK_FILE_PATH = os.path.join(COFFEE_DIR, "caffeine-lock.json")


def read_lock_file():
    try:
        with open(LOCK_FILE_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        return {"plugins": []}


def write_lock_file(data):
    try:
        with open(LOCK_FILE_PATH, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"💥 Error writing lock file: {e}")
