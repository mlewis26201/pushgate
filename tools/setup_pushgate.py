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
from app.db import init_db

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
    secrets_dir = input(f"Secrets directory [{DEFAULT_SECRETS_DIR}]: ").strip() or DEFAULT_SECRETS_DIR
    os.makedirs(secrets_dir, exist_ok=True)

    # Fernet key
    fernet_path = os.path.join(secrets_dir, "fernet_key")
    if os.path.exists(fernet_path):
        print(f"Fernet key already exists at {fernet_path}.")
    else:
        gen = input("Generate new Fernet encryption key? [Y/n]: ").strip().lower()
        if gen in ("", "y", "yes"):
            key = Fernet.generate_key().decode()
            write_secret(fernet_path, key)
        else:
            key = input("Paste Fernet key (44 chars, base64): ").strip()
            write_secret(fernet_path, key)

    # Admin password
    admin_path = os.path.join(secrets_dir, "admin_password")
    if os.path.exists(admin_path):
        print(f"Admin password already exists at {admin_path}.")
    else:
        pw = prompt_secret("Set admin password: ")
        write_secret(admin_path, pw)

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
