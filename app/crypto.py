from cryptography.fernet import Fernet
import os

# Improved Fernet key file resolution for all environments

def _find_fernet_key_file():
    # 1. Environment variable
    env_path = os.environ.get("FERNET_KEY_FILE")
    if env_path and os.path.exists(env_path):
        return env_path
    # 2. Local dev default (relative to project root, not __file__)
    local_path = os.path.abspath(os.path.join(os.getcwd(), "secrets", "fernet_key"))
    if os.path.exists(local_path):
        return local_path
    # 3. Docker default
    docker_path = "/run/secrets/fernet_key"
    if os.path.exists(docker_path):
        return docker_path
    # 4. Fallback: error
    raise Exception(f"Fernet key not found (checked: $FERNET_KEY_FILE, {local_path}, {docker_path})")

FERNET_KEY_FILE = _find_fernet_key_file()

def get_fernet():
    with open(FERNET_KEY_FILE, "rb") as f:
        key = f.read().strip()
    return Fernet(key)

def encrypt(data: str) -> str:
    f = get_fernet()
    return f.encrypt(data.encode()).decode()

def decrypt(token: str) -> str:
    f = get_fernet()
    return f.decrypt(token.encode()).decode()
