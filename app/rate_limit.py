from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import Message, Token

RATE_LIMIT_COUNT = 5  # Example: 5 messages
RATE_LIMIT_PERIOD = timedelta(minutes=1)  # per 1 minute

def check_token_rate_limit(db: Session, token_id: int):
    now = datetime.utcnow()
    window_start = now - RATE_LIMIT_PERIOD
    count = db.query(Message).filter(
        Message.token_id == token_id,
        Message.timestamp >= window_start
    ).count()
    if count >= RATE_LIMIT_COUNT:
        return False
    return True
