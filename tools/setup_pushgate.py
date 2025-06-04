#!/usr/bin/env python3
"""
Guided setup script for Pushgate secrets and database initialization.
- Prompts for admin password, Pushover app token, and user key.
- Offers to generate a Fernet encryption key (or use existing).
- Writes secrets to /run/secrets/ (or a user-specified directory).
- Initializes the database.

Usage:
    python tools/setup_pushgate.py
"""
import os
import getpass
from cryptography.fernet import Fernet
from app.db import init_db, SessionLocal
from app.models import AdminSettings

DEFAULT_SECRETS_DIR = "./secrets"


def prompt_secret(prompt, confirm=True, allow_empty=False):
    while True:
        value = getpass.getpass(prompt)
        if not value and not allow_empty:
            print("Value cannot be empty.")
            continue
        if confirm:
            value2 = getpass.getpass("Confirm: ")
            if value != value2:
                print("Values do not match. Try again.")
                continue
        return value

def write_secret(path, value, mode=0o600):
    with open(path, "w") as f:
        f.write(value)
    os.chmod(path, mode)
    print(f"Wrote secret: {path}")

def main():
    print("--- Pushgate Guided Setup ---")
    # Ensure app/static directory exists for FastAPI static files
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "static")
    os.makedirs(static_dir, exist_ok=True)
    # Optionally add a .gitkeep file so the directory is tracked by git
    gitkeep_path = os.path.join(static_dir, ".gitkeep")
    if not os.path.exists(gitkeep_path):
        with open(gitkeep_path, "w") as f:
            f.write("")

    secrets_dir = input(f"Secrets directory [{DEFAULT_SECRETS_DIR}]: ").strip() or DEFAULT_SECRETS_DIR
    # Ensure secrets directory exists before using it
    os.makedirs(secrets_dir, exist_ok=True)
    # Set permissions to 0o700 for the secrets directory to ensure write access (especially for Docker volume)
    try:
        os.chmod(secrets_dir, 0o700)
    except Exception as e:
        print(f"Warning: Could not set permissions on {secrets_dir}: {e}")

    # Prompt if this is a new install
    print("\nIs this a new Pushgate install?")
    is_new = input("Type 'yes' to initialize a new secrets directory and Fernet key, or 'no' to use existing secrets [yes/no]: ").strip().lower()
    fernet_path = os.path.join(secrets_dir, "fernet_key")
    if is_new in ("yes", "y"):
        # Create secrets directory and Fernet key
        if not os.path.exists(secrets_dir):
            os.makedirs(secrets_dir, exist_ok=True)
            try:
                os.chmod(secrets_dir, 0o700)
            except Exception as e:
                print(f"Warning: Could not set permissions on {secrets_dir}: {e}")
        if os.path.exists(fernet_path):
            print(f"Fernet key already exists at {fernet_path}. Aborting to avoid overwrite.")
            return
        key = Fernet.generate_key().decode()
        write_secret(fernet_path, key)
        print(f"New Fernet key created at {fernet_path}.")
        # Ensure the Fernet key is written before importing encrypt
        from app.crypto import encrypt
    else:
        if not os.path.exists(fernet_path) or os.path.getsize(fernet_path) == 0:
            print("\nNo Fernet key found. You must manually migrate your Fernet key and secrets. See the documentation or use a migration script.")
            return
        from app.crypto import encrypt

    # Admin password
    # Only store encrypted admin password in the database (no file)
    pw = prompt_secret("Set admin password: ")
    db = SessionLocal()
    enc_pw = encrypt(pw)
    admin_settings = AdminSettings(encrypted_password=enc_pw)
    db.add(admin_settings)
    db.commit()
    db.close()
    print("Admin password stored encrypted in the database.")

    # Pushover app token
    pushover_app_path = os.path.join(secrets_dir, "pushover_app_token")
    if os.path.exists(pushover_app_path):
        print(f"Pushover app token already exists at {pushover_app_path}.")
    else:
        app_token = input("Enter Pushover app token (30 chars): ").strip()
        write_secret(pushover_app_path, app_token)

    # Pushover user key
    pushover_user_path = os.path.join(secrets_dir, "pushover_user_key")
    if os.path.exists(pushover_user_path):
        print(f"Pushover user key already exists at {pushover_user_path}.")
    else:
        user_key = input("Enter Pushover user key (30 chars): ").strip()
        write_secret(pushover_user_path, user_key)

    # Database initialization
    print("\nInitializing database...")
    init_db()
    print("Database initialized.")
    print("\nSetup complete!")

if __name__ == "__main__":
    main()
