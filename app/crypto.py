from cryptography.fernet import Fernet
import os

# Try to get Fernet key file from env, else use local dev default, else Docker default
FERNET_KEY_FILE = os.environ.get("FERNET_KEY_FILE") or "./secrets/fernet_key" if os.path.exists("./secrets/fernet_key") else "/run/secrets/fernet_key"

def get_fernet():
    try:
        with open(FERNET_KEY_FILE, "rb") as f:
            key = f.read().strip()
        return Fernet(key)
    except Exception:
        raise Exception(f"Fernet key not found (tried: {FERNET_KEY_FILE})")

def encrypt(data: str) -> str:
    f = get_fernet()
    return f.encrypt(data.encode()).decode()

def decrypt(token: str) -> str:
    f = get_fernet()
    return f.decrypt(token.encode()).decode()
