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
