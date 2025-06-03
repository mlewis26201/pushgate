# Tools for Pushgate

This directory contains utility scripts for managing the Pushgate application.

## Database Initialization

- `init_db.py`: Initializes the SQLite database with all required tables. Run this script before first use or when starting with a fresh database.

### Usage

```bash
python tools/init_db.py
```

This will create all tables as defined in the current models.

---
