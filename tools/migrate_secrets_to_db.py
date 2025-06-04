#!/usr/bin/env python3
"""
Migrate Pushgate secrets from files to encrypted database storage.
- Migrates admin password from secrets/admin_password to the DB (encrypted).
- Migrates pushover_app_token and pushover_user_key from secrets/ to the DB (encrypted, as a PushoverConfig named 'Migrated').
- Does not overwrite existing DB values unless --force is specified.

Usage:
    python tools/migrate_secrets_to_db.py [--secrets-dir DIR] [--force]

Run this with the app stopped for safety.
"""
import os
import sys
from app.db import SessionLocal, init_db
from app.models import AdminSettings, PushoverConfig
from app.crypto import encrypt

def migrate_admin_password(secrets_dir, force=False):
    path = os.path.join(secrets_dir, "admin_password")
    if not os.path.exists(path):
        print("No admin_password file found, skipping admin password migration.")
        return
    pw = open(path).read().strip()
    db = SessionLocal()
    exists = db.query(AdminSettings).first()
    if exists and not force:
        print("Admin password already exists in DB. Use --force to overwrite.")
        db.close()
        return
    enc_pw = encrypt(pw)
    if exists:
        exists.encrypted_password = enc_pw
    else:
        db.add(AdminSettings(encrypted_password=enc_pw))
    db.commit()
    db.close()
    print("Admin password migrated to DB.")

def migrate_pushover_keys(secrets_dir, force=False):
    app_path = os.path.join(secrets_dir, "pushover_app_token")
    user_path = os.path.join(secrets_dir, "pushover_user_key")
    if not (os.path.exists(app_path) and os.path.exists(user_path)):
        print("No pushover_app_token or pushover_user_key file found, skipping pushover config migration.")
        return
    app_token = open(app_path).read().strip()
    user_key = open(user_path).read().strip()
    db = SessionLocal()
    exists = db.query(PushoverConfig).filter_by(name="Migrated").first()
    if exists and not force:
        print("A PushoverConfig named 'Migrated' already exists in DB. Use --force to overwrite.")
        db.close()
        return
    enc_app = encrypt(app_token)
    enc_user = encrypt(user_key)
    if exists:
        exists.encrypted_app_token = enc_app
        exists.encrypted_user_key = enc_user
    else:
        db.add(PushoverConfig(name="Migrated", encrypted_app_token=enc_app, encrypted_user_key=enc_user))
    db.commit()
    db.close()
    print("Pushover keys migrated to DB as config 'Migrated'.")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Migrate Pushgate secrets from files to DB.")
    parser.add_argument("--secrets-dir", default="./secrets", help="Directory containing secret files")
    parser.add_argument("--force", action="store_true", help="Overwrite existing DB values")
    args = parser.parse_args()
    secrets_dir = args.secrets_dir
    print(f"Using secrets directory: {secrets_dir}")
    print("Ensuring DB tables exist...")
    init_db()
    migrate_admin_password(secrets_dir, force=args.force)
    migrate_pushover_keys(secrets_dir, force=args.force)
    print("\nMigration complete. You may now remove the old secret files if desired.")

if __name__ == "__main__":
    main()
