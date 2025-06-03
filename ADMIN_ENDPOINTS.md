# Pushgate Admin Endpoints Documentation

## Overview
The Pushgate admin endpoints allow authorized administrators to manage tokens and Pushover configuration through a secure web interface. All admin endpoints require authentication using the admin password (stored as a Docker secret). Sessions are managed securely.

## Authentication
- **Login:**
  - `GET /pushgate/login`: Show the login form.
  - `POST /pushgate/login`: Submit the admin password. On success, starts an admin session.
- **Logout:**
  - `GET /pushgate/logout`: Ends the admin session.

## Token Management
- **View Tokens:**
  - `GET /pushgate/tokens`: Lists all tokens, their creation and last used times. Requires admin login.
- **Create Token:**
  - `POST /pushgate/tokens/create`: Generates and stores a new token. Token is encrypted at rest.
- **Rotate Token:**
  - `POST /pushgate/tokens/rotate`: Rotates (replaces) an existing token with a new one.
- **Delete Token:**
  - `POST /pushgate/tokens/delete`: Deletes a token from the system.

## Pushover Configuration
- **View/Update Config:**
  - `GET /pushgate/pushover-config`: View current Pushover API credentials (decrypted for display).
  - `POST /pushgate/pushover-config/update`: Update and save new Pushover API credentials (encrypted at rest).

## Send Message (Admin UI)
- Go to `/pushgate/send-message` after logging in.
- Enter your message and select the desired Pushover config from the dropdown.
- Submit the form to send a test message using the selected config.

## Security
- All admin endpoints require a valid session (login required).
- Password is never stored in the database; it is read from a Docker secret at runtime.
- All sensitive data (tokens, Pushover credentials) are encrypted at rest using Fernet with a key from Docker secrets.

## Example: Logging In
```
1. Visit https://your.domain/pushgate/login
2. Enter the admin password.
3. Upon success, you are redirected to the token management UI.
```

## Example: Creating a Token
```
1. Log in as admin.
2. Go to https://your.domain/pushgate/tokens
3. Click "Create New Token".
4. The new token will appear in the list.
```

## Notes
- All admin actions are performed via the web UI for security and auditability.
- If your session expires or you log out, you will be prompted to log in again.

---
For more details, see the main README or contact your Pushgate administrator.
