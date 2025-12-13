import pytest
from re import search
from backend.extensions import mail

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
            token_only = reset_url.split('/')[-1]
            token_path = f"/reset_password/{token_only}"
            
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

def test_password_reset_revokes_all_tokens(client, registered_user, app):
    with app.app_context():
        user, password = registered_user

        login_response = client.post("/api/login", json={"username": user.username, "password": password})
        login_data = login_response.get_json()
        initial_access_token = login_data["access_token"]
        initial_refresh_token = login_data["refresh_token"]

        email_payload = {"email": user.email}
        with mail.record_messages() as outbox:
            client.post("/reset_password_request", json=email_payload)

            match = search(r'/reset_password/([a-zA-Z0-9\-\._]+)', outbox[0].body)
            assert match, "Reset path not found in email"
            token_path = f"/reset_password/{match.group(1)}"

            password_payload = {"new_password": "NewSecret123"}
            response = client.post(token_path, json=password_payload)

            assert response.status_code == 200

        protected_response = client.get("/user", headers={"Authorization": f"Bearer {initial_access_token}"})
        assert protected_response.status_code == 401
        
        refresh_response = client.post("/refresh", headers={"Authorization": f"Bearer {initial_refresh_token}"})
        assert refresh_response.status_code == 401

        login_response_new = client.post("/api/login", json={"username": user.username, "password": "NewSecret123"})
        assert login_response_new.status_code == 200
