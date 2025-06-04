#!/usr/bin/env python3
"""
Rotate the Fernet encryption key for all encrypted secrets in Pushgate.
- Decrypts all encrypted fields in the database using the old key.
- Re-encrypts them with a new Fernet key.
- Overwrites the Fernet key file.
- Backs up the old key and optionally the DB.

Usage:
    python tools/rotate_fernet_key.py [--secrets-dir DIR] [--db-backup]

Stop the Pushgate app before running this script!
"""
import os
import sys
import shutil
from cryptography.fernet import Fernet
from app.db import SessionLocal
from app.models import Token, PushoverConfig, AdminSettings
from app.crypto import get_fernet, decrypt

DEFAULT_SECRETS_DIR = "./secrets"
FERNET_KEY_FILENAME = "fernet_key"

def backup_file(path):
    backup_path = path + ".bak"
    shutil.copy2(path, backup_path)
    print(f"Backed up {path} to {backup_path}")

def main():
    print("--- Pushgate Fernet Key Rotation ---")
    secrets_dir = sys.argv[sys.argv.index("--secrets-dir")+1] if "--secrets-dir" in sys.argv else DEFAULT_SECRETS_DIR
    fernet_path = os.path.join(secrets_dir, FERNET_KEY_FILENAME)
    if not os.path.exists(fernet_path):
        print(f"Fernet key file not found: {fernet_path}")
        sys.exit(1)
    backup_file(fernet_path)
    old_key = open(fernet_path, "rb").read().strip()
    old_fernet = Fernet(old_key)
    new_key = Fernet.generate_key()
    new_fernet = Fernet(new_key)
    # Optionally backup DB
    if "--db-backup" in sys.argv:
        db_path = os.getenv("DATABASE_URL", "sqlite:///./pushgate.db").replace("sqlite:///", "")
        if os.path.exists(db_path):
            backup_file(db_path)
    db = SessionLocal()
    # Rotate tokens
    for t in db.query(Token).all():
        try:
            plain = old_fernet.decrypt(t.encrypted_token.encode()).decode()
            t.encrypted_token = new_fernet.encrypt(plain.encode()).decode()
        except Exception as e:
            print(f"Token ID {t.id} decryption failed: {e}")
    # Rotate pushover configs
    for c in db.query(PushoverConfig).all():
        try:
            app_token = old_fernet.decrypt(c.encrypted_app_token.encode()).decode()
            user_key = old_fernet.decrypt(c.encrypted_user_key.encode()).decode()
            c.encrypted_app_token = new_fernet.encrypt(app_token.encode()).decode()
            c.encrypted_user_key = new_fernet.encrypt(user_key.encode()).decode()
        except Exception as e:
            print(f"PushoverConfig ID {c.id} decryption failed: {e}")
    # Rotate admin password
    for a in db.query(AdminSettings).all():
        try:
            pw = old_fernet.decrypt(a.encrypted_password.encode()).decode()
            a.encrypted_password = new_fernet.encrypt(pw.encode()).decode()
        except Exception as e:
            print(f"AdminSettings ID {a.id} decryption failed: {e}")
    db.commit()
    db.close()
    # Overwrite Fernet key file
    with open(fernet_path, "wb") as f:
        f.write(new_key)
    print(f"Fernet key rotated and all secrets re-encrypted. New key written to {fernet_path}.")
    print("Restart Pushgate to use the new key.")

if __name__ == "__main__":
    main()
