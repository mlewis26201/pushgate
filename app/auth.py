from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
import os

from .models import AdminSettings
from .crypto import decrypt

ADMIN_PASSWORD_FILE = "/run/secrets/admin_password"

def get_admin_password():
    # Try to get from DB first
    from .db import SessionLocal
    db: Session = SessionLocal()
    admin_settings = db.query(AdminSettings).order_by(AdminSettings.updated_at.desc()).first()
    db.close()
    if admin_settings:
        try:
            return decrypt(admin_settings.encrypted_password)
        except Exception:
            pass
    # Fallback to file
    try:
        with open(ADMIN_PASSWORD_FILE) as f:
            return f.read().strip()
    except Exception:
        return None

def get_current_admin(request: Request):
    # Dummy implementation: check session or prompt for password
    # Replace with real session-based auth
    if request.session.get("admin_authenticated"):
        return True
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
