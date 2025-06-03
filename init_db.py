#!/usr/bin/env python3
"""
Database initialization script for Pushgate.
Creates all tables using the current models.
Usage:
    python init_db.py
"""
from app.db import init_db

if __name__ == "__main__":
    print("Initializing Pushgate database...")
    init_db()
    print("Database initialized.")
