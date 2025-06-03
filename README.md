# pushgate

A gateway for forwarding HTTP messages to Pushover, with token management, rate limiting, and secure storage.

## Initialization & Setup

Before running Pushgate for the first time, you must initialize secrets and the database:

1. **Run the guided setup script:**
   ```bash
   python tools/setup_pushgate.py
   ```
   This will prompt you for the admin password, Pushover app token, user key, and optionally generate an encryption key. It will also initialize the database.

2. **(Re)initialize the database only:**
   ```bash
   python tools/init_db.py
   ```
   Use this if you want to reset the database tables without changing secrets.

Secrets are stored in `/run/secrets/` by default, or a directory you specify during setup.

---

## Features
- Accepts messages via HTTP and forwards to Pushover
- Token-based authentication and management (create, rotate, delete)
- Admin web UI for tokens, Pushover config, message history, and sending messages via a form
- **Admin dashboard with links to all features**
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

**Admin UI Note:** When sending a message from the admin web interface, you can select which Pushover config to use from a dropdown menu. This allows testing or sending messages with different app/user credentials.

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

## Message History Endpoint

- `/pushgate/messages` (GET): Admin UI to view message history. Supports filtering by token, status, and text search. Results are paginated.

### Features
- Filter by token (dropdown)
- Filter by status (dropdown)
- Text search in message contents
- Pagination controls
- Displays time, token, message, and status for each entry

## Per-Token Rate Limiting

- Each token now has a configurable rate limit (messages per hour).
- Set the rate limit when creating or rotating a token in the admin UI.
- The `/send` endpoint enforces this limit per token.
- If the limit is exceeded, the API returns HTTP 429 with a message indicating the allowed rate.

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

## Troubleshooting

- **App does not start:**
  - Ensure all required secrets (`fernet_key`, `admin_password`) are present in `/run/secrets/` or your specified secrets directory.
  - Check Docker logs for errors: `docker logs <container_id>`
  - Make sure the database file is writable by the container (if using SQLite).
- **Cannot log in as admin:**
  - Double-check the admin password in your secrets directory.
- **Pushover messages not delivered:**
  - Verify the selected Pushover config is valid and active.
  - Check rate limits and message logs in the admin UI.
- **Other issues:**
  - Review the documentation and ensure all setup steps were followed.
  - For further help, see the logs or open an issue.
