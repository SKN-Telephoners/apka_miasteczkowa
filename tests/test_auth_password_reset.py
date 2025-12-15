import pytest
from re import search
from backend.extensions import mail ,db 
from backend.models import User

# =============================================================================
# Tests for password resetting
# =============================================================================

def test_password_reset(client, registered_user, app):
    with app.app_context():
        user, password = registered_user

        email_payload = {
            "email": user.email
        }

        with mail.record_messages() as outbox:
            response = client.post("/reset_password_request", json=email_payload)

            assert response.status_code == 200
            assert len(outbox) == 1
            assert outbox[0].subject == 'Reset password'

            match = search(r'(http://.+/reset_password/\S+)', outbox[0].body)
            assert match, "No reset URL found in email body"

            reset_url = match.group()
            token_path = reset_url.replace("http://localhost", "")
            
            assert response.status_code == 200 
            
            password_payload = {
                "new_password": "Dupa!123"
            }

            response = client.post(token_path, json=password_payload)
            assert response.status_code == 200

        response = client.post("/api/login", json={"username": user.username, "password": "Dupa!123"})
        assert response.status_code == 200

def test_password_reset_invalid_email(client, app):
    with app.app_context():
        email_payload = {
            "email": "invalid_user@gmail.com"
        }

        with mail.record_messages() as outbox:
            response = client.post("/reset_password_request", json=email_payload)

            assert response.status_code == 200
            assert len(outbox) == 0


