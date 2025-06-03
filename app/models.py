from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class Token(Base):
    __tablename__ = "tokens"
    id = Column(Integer, primary_key=True, index=True)
    encrypted_token = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    # Optionally: rate_limit fields
    messages = relationship("Message", back_populates="token")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(Integer, ForeignKey("tokens.id"))
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String)
    token = relationship("Token", back_populates="messages")

class PushoverConfig(Base):
    __tablename__ = "pushover_config"
    id = Column(Integer, primary_key=True, index=True)
    encrypted_app_token = Column(String, nullable=False)
    encrypted_user_key = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)
