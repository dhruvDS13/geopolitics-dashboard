import json
from pathlib import Path

FILE_PATH = Path("subscribers.json")

def get_users():
    if not FILE_PATH.exists():
        return []
    try:
        return json.loads(FILE_PATH.read_text())
    except:
        return []

def add_user(user_id):
    users = get_users()
    if user_id not in users:
        users.append(user_id)
        FILE_PATH.write_text(json.dumps(users))