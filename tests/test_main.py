import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_page():
    response = client.get("/pushgate/login")
    assert response.status_code == 200
    assert "Admin Login" in response.text

def test_send_invalid_token():
    response = client.post("/pushgate/send", data={"token": "invalidtoken1234567890123456", "message": "Hello"})
    assert response.status_code in (400, 401)

def test_send_missing_message():
    # Use a valid-length token for this test
    response = client.post("/pushgate/send", data={"token": "A"*30})
    assert response.status_code == 400
    assert "Message is required" in response.text

# New: test that secrets files are not required except for fernet_key
def test_no_admin_password_file(monkeypatch):
    import os
    # Simulate missing admin_password file
    monkeypatch.setattr(os.path, "exists", lambda p: False if "admin_password" in p else os.path.exists(p))
    # The app should still run and require login via DB password
    response = client.get("/pushgate/login")
    assert response.status_code == 200
    assert "Admin Login" in response.text

# New: test that pushover keys are not required in secrets dir
def test_no_pushover_key_files(monkeypatch):
    import os
    monkeypatch.setattr(os.path, "exists", lambda p: False if "pushover_app_token" in p or "pushover_user_key" in p else os.path.exists(p))
    response = client.get("/pushgate/pushover-config")
    # Should still load the config page (may be empty)
    assert response.status_code in (200, 303)
