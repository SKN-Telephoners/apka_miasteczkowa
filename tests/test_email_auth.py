import pytest
from re import search
from backend.extensions import mail ,db 
from backend.models import User


# =============================================================================
# Tests for auth user
# =============================================================================

def test_auth_user(client, app):
    with app.app_context():
        username = "test_user"
        password = "123456flask"
        email = "test_user@gmail.com"
        user = User(username=username, password=password, email=email)
        
        db.session.add(user)
        db.session.commit()

        assert user.is_confirmed is False

        email_payload = {
            "email": email
        }

        with mail.record_messages() as outbox:
            response = client.post("/api/email/verify_request", json=email_payload)

            assert response.status_code == 200
            assert len(outbox) == 1
            assert outbox[0].subject == 'Auth account'

            match = search(r'(https?://.+/api/email/verify/\S+)', outbox[0].body)
            assert match, "No auth URL found in email body"

            auth_url = match.group()
            token_path = auth_url.replace("http://localhost", "")
            token_path = auth_url.replace("https://localhost", "")
            
            assert response.status_code == 200 

            response = client.get(token_path)
            assert response.status_code == 200
            assert response.get_json()["message"] == "Verification succesful"


        user_answer=User.query.filter_by(email=email).first()
        assert user_answer.is_confirmed is True

def test_auth_user_invalid_email(client, app):
    with app.app_context():
        email_payload = {
            "email": "invalid_user@gmail.com"
        }

        with mail.record_messages() as outbox:
            response = client.post("/api/email/verify_request", json=email_payload)

            assert response.status_code == 401
            assert len(outbox) == 0

def test_auth_user_confirmed(client, app, registered_user):
    with app.app_context():
        user = registered_user[0]

        assert user.is_confirmed is True

        email_payload = {
            "email": user.email
        }

        with mail.record_messages() as outbox:
            response = client.post("/api/email/verify_request", json=email_payload)

            assert response.status_code == 400
            assert response.get_json()["message"] == "User already confirmed"
            assert len(outbox) == 0