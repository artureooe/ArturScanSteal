import json

CONFIG = {
    "token": "8364189800:AAHHsHHgKZ7oB6XSHExPWn0-0G5Fp8fGNi4",
    "admin_id": 7725796090,
    "webhook_url": "https://zonastealer-bot.onrender.com",
    "database": "users.db"
}

def save_config():
    with open('config.json', 'w') as f:
        json.dump(CONFIG, f, indent=4)

def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except:
        save_config()
        return CONFIG
