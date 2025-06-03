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

## Token Management Endpoints

- `/pushgate/tokens` (GET): Admin UI to view all tokens.
- `/pushgate/tokens/create` (POST): Create a new token.
- `/pushgate/tokens/rotate` (POST): Rotate (replace) an existing token.
- `/pushgate/tokens/delete` (POST): Delete a token.

All actions require admin authentication. Tokens are encrypted at rest and displayed in the admin UI. Use the UI to manage tokens for client access.

## Admin Authentication

- `/pushgate/login` (GET/POST): Admin login page. Requires password (stored in Docker secret).
- `/pushgate/logout` (GET): Log out admin session.

All admin endpoints require authentication. Sessions are managed securely using FastAPI's session middleware.

## Message Sending Endpoint

- `/pushgate/send` (POST): Accepts a `token` and `message` via form data. Validates the token, checks per-token Pushover rate limit, sends the message to Pushover, and logs the message in the database. Returns a JSON response with status or error.

Example request:

```bash
curl -X POST \
  -F "token=YOUR_TOKEN" \
  -F "message=Hello from Pushgate!" \
  https://your.domain/pushgate/send
```

Possible responses:
- `200 OK`: `{ "status": "ok", "pushover_response": "..." }`
- `401 Unauthorized`: Invalid token
- `429 Too Many Requests`: Rate limit exceeded
- `502 Bad Gateway`: Pushover error

## Pushover Configuration Endpoint

- `/pushgate/pushover-config` (GET): Admin UI to view current Pushover app token and user key (decrypted for display).
- `/pushgate/pushover-config/update` (POST): Update and save new Pushover credentials (encrypted at rest).

All actions require admin authentication. Credentials are encrypted in the database and used for sending notifications.

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
