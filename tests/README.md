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

## Notes
- Tests use an in-memory or temporary database by default. If you want to test with a specific database or environment, adjust the test setup accordingly.
- You can add more test files (e.g., `test_tokens.py`, `test_admin.py`) to cover additional functionality.

---
