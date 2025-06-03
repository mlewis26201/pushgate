import requests
from .db import get_db
from .models import PushoverConfig
from .crypto import decrypt
from sqlalchemy.orm import Session

PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"

def send_pushover_message(db: Session, message: str, config=None):
    if config is None:
        config = db.query(PushoverConfig).first()
    if not config:
        raise Exception("Pushover config not set")
    app_token = decrypt(config.encrypted_app_token)
    user_key = decrypt(config.encrypted_user_key)
    data = {
        "token": app_token,
        "user": user_key,
        "message": message
    }
    resp = requests.post(PUSHOVER_API_URL, data=data)
    return resp.status_code, resp.text
