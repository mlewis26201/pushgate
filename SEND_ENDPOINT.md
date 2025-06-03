# Pushgate /send Endpoint Documentation

## Overview
The `/send` endpoint allows clients to send messages to Pushover via HTTP POST requests. Each request must include a valid token and a message. The endpoint enforces per-token rate limiting and logs all messages.

## Endpoint
```
POST /pushgate/send
```

## Request Format
- Content-Type: `application/x-www-form-urlencoded` (standard HTML form or curl `-F`)
- Required fields:
  - `token`: The client token (string, must be valid and active)
  - `message`: The message to send (string, required by Pushover)

### Example Request (curl)
```
curl -X POST \
  -F "token=YOUR_TOKEN" \
  -F "message=Hello from Pushgate!" \
  https://your.domain/pushgate/send
```

## Response Format
- On success (HTTP 200):
  ```json
  {
    "status": "ok",
    "pushover_response": "...pushover API response..."
  }
  ```
- On error (HTTP 401, 429, 502):
  ```json
  {
    "detail": "Error message"
  }
  ```

## Error Codes
- `401 Unauthorized`: Invalid token
- `429 Too Many Requests`: Rate limit exceeded for this token
- `502 Bad Gateway`: Error from Pushover API

## Notes
- Each token is subject to rate limiting (see admin settings for limits).
- All messages and attempts are logged in the database for auditing.
- The endpoint is designed for integration with non-Pushover-aware applications and scripts.

---
For more details, see the main README or contact your Pushgate administrator.
