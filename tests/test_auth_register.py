import pytest
from backend.models import User

# =============================================================================
# Tests for user registration
# =============================================================================

def test_register_successful(client, app):
    with app.app_context():
        username = "user1"
        password = "Secret123" # Strong password
        email = "user1@gmail.com"
        
        payload = {
            "username": username,
            "password": password,
            "email": email
        }
        
        response = client.post("/api/register", json=payload)
        
        assert response.status_code == 200
        assert response.get_json() == {
            "message": "Registration successful"
        }
        assert User.query.filter_by(username=username).first() is not None

def test_register_missing_key(client, app):
    with app.app_context():
        username = "user1"
        email = "user1@gmail.com"
        
        payload = {
            "username": username,
            "email": email
        }
        
        response = client.post("/api/register", json=payload)
        
        assert response.status_code == 400
        assert response.get_json() == {
            "message": "Bad request"
        }
        assert User.query.filter_by(username=username).first() is None

def test_register_invalid_credentials(client, app):
    with app.app_context():
        username = "a" # Too short
        password = "Secret123"
        email = "user1@gmail.com"
        
        payload = {
            "username": username,
            "password": password,
            "email": email
        }
        
        response1 = client.post("/api/register", json=payload)
        
        assert response1.status_code == 400
        # New regex error message for username or email
        assert response1.get_json() == {
            "message": "Invalid username or email"
        }
        assert User.query.filter_by(username=username).first() is None
        
        username = "goodusername"
        password = "Secret123"
        email = "@gmail[]'user1@gmail.com" # Invalid email
        
        payload = {
            "username": username,
            "password": password,
            "email": email
        }
        
        response2 = client.post("api/register", json=payload)
        
        assert response2.status_code == 400
        assert response2.get_json() == {
            "message": "Invalid username or email"
        }
        assert User.query.filter_by(username=username).first() is None

# New test for weak passwords
def test_register_weak_password(client, app):
    with app.app_context():
        payload = {
            "username": "validuser",
            "password": "weak", 
            "email": "valid@gmail.com"
        }
        
        response = client.post("/api/register", json=payload)
        assert response.status_code == 400
        assert "Password must be 8-72 chars long" in response.get_json()["message"] or "Incorrect password format" in response.get_json()["message"]

def test_register_username_taken(client, registered_user, app):
    with app.app_context():
        user, password = registered_user
        assert User.query.filter_by(username=user.username).first() is not None

        username2 = user.username
        password2 = "Secret123"
        email2 = "user2@gmail.com"
        
        payload = {
            "username": username2,
            "password": password2,
            "email": email2
        }
        
        response = client.post("/api/register", json=payload)
        
        assert response.status_code == 409
        assert response.get_json() == {
            "message": "Username already taken"
        }
        assert len(User.query.filter_by(username=username2).all()) == 1

def test_register_email_exists(client, registered_user, app):
    with app.app_context():
        user, password = registered_user
        assert User.query.filter_by(username=user.username).first() is not None

        username2 = "user2"
        password2 = "Secret123"
        email2 = user.email
        
        payload = {
            "username": username2,
            "password": password2,
            "email": email2
        }
        
        response = client.post("/api/register", json=payload)
        
        assert response.status_code == 409
        assert response.get_json() == {
            "message": "Account with this email already exists"
        }
        assert len(User.query.filter_by(email=email2).all()) == 1