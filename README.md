# pushgate

A gateway for forwarding HTTP messages to Pushover, with token management, rate limiting, and secure storage.

## Features
- Accepts messages via HTTP and forwards to Pushover
- Token-based authentication and management (create, rotate, delete)
- Admin web UI for tokens and Pushover config
- Per-token Pushover rate limiting
- SQLite for persistent storage
- All secrets and sensitive data encrypted with a key from Docker secrets
- Dockerized for easy deployment
- **Supports running behind a proxy with a path prefix (e.g. `/pushgate/`)**

## Quick Start

1. Build and run with Docker:

```sh
docker build -t pushgate .
docker run -d \
  -v /path/to/secrets:/run/secrets \
  -p 8000:8000 \
  pushgate
```

2. Place your secrets (fernet_key, admin_password) in `/path/to/secrets/`.

## Endpoints
- `/pushgate/send` (POST): Send a message (requires token)
- `/pushgate/tokens`: Token management UI (admin)
- `/pushgate/pushover-config`: Pushover config UI (admin)

## Environment
- Python 3.11+
- FastAPI
- SQLAlchemy
- cryptography
- Docker

## Security
- All secrets excluded from git via `.gitignore`
- Tokens and Pushover config encrypted at rest

## Reverse Proxy/Path Prefix
If running behind a reverse proxy with a path prefix (e.g. `/pushgate/`), the app is pre-configured to work with this using FastAPI's `root_path` setting.
