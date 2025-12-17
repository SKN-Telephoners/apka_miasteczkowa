import pytest
from backend.models import User
import json
from backend.helpers import is_token_revoked
from flask_jwt_extended import decode_token


# =============================================================================
# Tests for user login
# =============================================================================

def test_login_success(client, registered_user, app):
    with app.app_context():
        user, password = registered_user
        assert User.query.filter_by(username=user.username).first() is not None
        
        response = client.post("/api/login", json={"username": user.username, "password": password})
        
        assert response.status_code == 200
        data = response.get_json()

        assert data["message"] == "Login successful"
        assert data["user"]["username"] == user.username
        
def test_login_missing_key(client, registered_user, app):
    with app.app_context():
        user = registered_user[0]
        assert User.query.filter_by(username=user.username).first() is not None
        
        response = client.post("/api/login", json={"username": user.username})
        
        assert response.status_code == 400
        assert response.get_json()["message"] == "Bad request"


def test_login_invalid_credentials(client, registered_user, app):
    with app.app_context():
        user = registered_user[0]
        assert User.query.filter_by(username=user.username).first() is not None
        
        response = client.post("/api/login", json={"username": user.username, "password": "different_passwd123"})
        
        assert response.status_code == 401
        assert response.get_json()["message"] == "Invalid username or password"


# =============================================================================
# Tests for jwt authorization
# =============================================================================

def test_jwt_login(client, registered_user, app):
    with app.app_context():
        user, password = registered_user
        assert User.query.filter_by(username=user.username).first() is not None

        payload = {
            "username": user.username,
            "password": password,
        }
        response = client.post("/api/login", json=payload)
        
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "access_token" in data
        assert "refresh_token" in data

        token = data["access_token"]
        protected_response = client.get("/user", headers={
            "Authorization": f"Bearer {token}"
        })

        assert protected_response.status_code == 200

def test_jwt_invalid_token(client, app):
    with app.app_context():
        invalid_token = "invalid_token"
        protected_response = client.get("/user", headers={
            "Authorization": f"Bearer {invalid_token}"
        })

        assert protected_response.get_json()["message"] == "Incorrect token"
        assert protected_response.status_code == 401

def test_jwt_no_token(client, app):
    with app.app_context():
        protected_response = client.get("/user")

        assert protected_response.get_json()["message"] == "Missing or invalid token"
        assert protected_response.status_code == 401

def test_jwt_revoke_access(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

        protected_response1 = client.get("/user", headers={
            "Authorization": f"Bearer {token}"
        })
        assert protected_response1.status_code == 200

        # Changed GET to DELETE
        revoke_response = client.delete("/revoke_access", headers={
            "Authorization": f"Bearer {token}"
        })
        assert revoke_response.status_code == 200
        assert revoke_response.get_json()["message"] == "Access token revoked"

        protected_response2 = client.get("/user", headers={
            "Authorization": f"Bearer {token}"
        })
        assert protected_response2.status_code == 401

def test_jwt_revoke_refresh_token(client, registered_user, app):
    with app.app_context():
        user, password = registered_user
        assert User.query.filter_by(username=user.username).first() is not None

        payload = {
            "username": user.username,
            "password": password,
        }
        response = client.post("/api/login", json=payload)
        assert response.status_code == 200

        data = json.loads(response.data)
        refresh_token = data["refresh_token"]

        # Changed GET to DELETE
        revoke_response = client.delete("/revoke_refresh", headers={
            "Authorization": f"Bearer {refresh_token}"
        })
        assert revoke_response.status_code == 200
        assert revoke_response.get_json()["message"] == "Refresh token revoked"

        refresh_response = client.post("/refresh", headers={
            "Authorization": f"Bearer {refresh_token}"
        })
        assert refresh_response.status_code == 401

# =============================================================================
# Tests for user logout
# =============================================================================

def test_logout_success(client, registered_user, app):
    user, password = registered_user

    payload = {"username": user.username, "password": password}
    response = client.post("/api/login", json=payload)
    data = response.get_json()

    refresh_token = data["refresh_token"]
    access_token = data["access_token"]
    
    headers = {'Authorization': f'Bearer {refresh_token}'}
    body = {'access_token': access_token}
    
    response = client.delete('/api/logout', headers=headers, json=body)
    
    assert response.status_code == 200
    assert response.json['message'] == 'Logged out successfully'

    assert is_token_revoked(decode_token(refresh_token)) == True
    # Note: Access token might not be revoked in DB if we ignore errors, 
    # but for the purpose of this test, if it was passed, it should be.
    
def test_logout_refresh_only(client, registered_user, app):
    user, password = registered_user

    payload = {"username": user.username, "password": password}
    response = client.post("/api/login", json=payload)
    data = response.get_json()

    refresh_token = data["refresh_token"]
    access_token = data["access_token"]
    
    headers = {'Authorization': f'Bearer {refresh_token}'}
    body = {} 
    
    response = client.delete('/api/logout', headers=headers, json=body)

    assert response.status_code == 200
    assert response.json['message'] == 'Logged out successfully'
 
    assert is_token_revoked(decode_token(refresh_token)) == True
    assert is_token_revoked(decode_token(access_token)) == False 

def test_logout_invalid_access_token_in_body(client, registered_user, app):
    user, password = registered_user

    payload = {"username": user.username, "password": password}
    response = client.post("/api/login", json=payload)
    data = response.get_json()

    refresh_token = data["refresh_token"]
    
    headers = {'Authorization': f'Bearer {refresh_token}'}
    body = {'access_token': 'not.a.real.token'}
    
    response = client.delete('/api/logout', headers=headers, json=body)

    assert response.status_code == 200
    assert response.json['message'] == 'Logged out successfully'

    assert is_token_revoked(decode_token(refresh_token)) == True

def test_logout_no_auth_header(client):
    response = client.delete('/api/logout', json={'access_token': '...'})
    
    assert response.status_code == 401
    assert response.json['message'] == 'Missing or invalid token' 

def test_logout_with_access_token_in_header(client, registered_user):
    user, password = registered_user

    payload = {"username": user.username, "password": password}
    response = client.post("/api/login", json=payload)
    data = response.get_json()

    access_token = data["access_token"]
    
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = client.delete('/api/logout', headers=headers, json={})
    
    assert response.status_code == 401 