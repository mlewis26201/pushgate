from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import Message, Token

def check_token_rate_limit(db: Session, token_id: int, rate_limit_per_hour: int):
    now = datetime.utcnow()
    window_start = now - timedelta(hours=1)
    count = db.query(Message).filter(
        Message.token_id == token_id,
        Message.timestamp >= window_start
    ).count()
    if count >= rate_limit_per_hour:
        return False
    return True
