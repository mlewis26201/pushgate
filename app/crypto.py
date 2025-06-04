from cryptography.fernet import Fernet
import os

# Improved Fernet key file resolution for all environments

def _find_fernet_key_file():
    # 1. Environment variable
    env_path = os.environ.get("FERNET_KEY_FILE")
    if env_path and os.path.exists(env_path):
        return env_path
    # 2. Local dev default (relative to project root, not CWD)
    local_path = os.path.abspath(os.path.join(os.getcwd(), "secrets", "fernet_key"))
    # Do not raise if not found, just return None
    if os.path.exists(local_path):
        return local_path
    # 3. Docker default
    docker_path = "/run/secrets/fernet_key"
    if os.path.exists(docker_path):
        return docker_path
    # 4. Fallback: return None
    return None

FERNET_KEY_FILE = _find_fernet_key_file()

def get_fernet():
    if not FERNET_KEY_FILE or not os.path.exists(FERNET_KEY_FILE) or os.path.getsize(FERNET_KEY_FILE) == 0:
        raise Exception(f"Fernet key not found or empty (checked: $FERNET_KEY_FILE, ./secrets/fernet_key, /run/secrets/fernet_key)")
    with open(FERNET_KEY_FILE, "rb") as f:
        key = f.read().strip()
    return Fernet(key)

def encrypt(data: str) -> str:
    f = get_fernet()
    return f.encrypt(data.encode()).decode()

def decrypt(token: str) -> str:
    f = get_fernet()
    return f.decrypt(token.encode()).decode()
