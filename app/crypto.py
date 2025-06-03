from cryptography.fernet import Fernet
import os

FERNET_KEY_FILE = "/run/secrets/fernet_key"

def get_fernet():
    try:
        with open(FERNET_KEY_FILE, "rb") as f:
            key = f.read().strip()
        return Fernet(key)
    except Exception:
        raise Exception("Fernet key not found")

def encrypt(data: str) -> str:
    f = get_fernet()
    return f.encrypt(data.encode()).decode()

def decrypt(token: str) -> str:
    f = get_fernet()
    return f.decrypt(token.encode()).decode()
