# Automated Testing for Pushgate

## Overview
This directory contains automated tests for the Pushgate application, using `pytest` and FastAPI's `TestClient`.

## Prerequisites
- Install dependencies:
  ```bash
  pip install pytest httpx
  ```

## Running the Tests
From the root of your project (where `tests/` is located), run:

```bash
pytest
```

This will discover and run all test scripts in the `tests/` directory.

## Running Tests in a Python Virtual Environment

To ensure a clean environment and avoid dependency conflicts, it is recommended to run tests inside a Python virtual environment (venv):

1. Create a virtual environment:

   ```bash
   python3 -m venv venv
   ```

2. Activate the virtual environment:
   - On Linux/macOS:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```cmd
     venv\Scripts\activate
     ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the tests (from the project root):

   ```bash
   PYTHONPATH=. pytest
   ```

This ensures the `app` module is discoverable and all dependencies are isolated to your venv.

## System Package Installation (Python & pip)

If you do not have Python 3 and pip installed, you can install them using your system package manager:

### Debian/Ubuntu:
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

### RedHat/CentOS/Fedora:
```bash
sudo dnf install python3 python3-venv python3-pip
```
# (On older systems, use `yum` instead of `dnf`)

After installing these packages, proceed with the virtual environment and Python module installation steps below.

## Notes
- Tests use an in-memory or temporary database by default. If you want to test with a specific database or environment, adjust the test setup accordingly.
- You can add more test files (e.g., `test_tokens.py`, `test_admin.py`) to cover additional functionality.

## Secrets Management
- The only secret that must remain in the `secrets/` directory is the Fernet encryption key (`fernet_key`).
- Admin password and Pushover keys are now stored encrypted in the database and managed via the admin UI.
- You may safely remove `admin_password`, `pushover_app_token`, and `pushover_user_key` from the secrets directory after migration.

---
