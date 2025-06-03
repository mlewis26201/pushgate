# Pushgate Setup Tools

This directory contains utility scripts for setting up and managing Pushgate.

## Guided Setup Script

- `setup_pushgate.py`: Interactive script to help you set up secrets and initialize the database.
  - Prompts for admin password, Pushover app token, and user key.
  - Offers to generate a Fernet encryption key (or use an existing one).
  - Writes secrets to `/run/secrets/` (or a directory you specify).
  - Initializes the database.

### Usage

```bash
python tools/setup_pushgate.py
```

Follow the prompts to complete setup. You can re-run this script to update secrets or re-initialize the database.

## Database Initialization Only

- `init_db.py`: Initializes the database tables only (no secrets setup).

### Usage

```bash
python tools/init_db.py
```

This will create all tables as defined in the current models.

---
