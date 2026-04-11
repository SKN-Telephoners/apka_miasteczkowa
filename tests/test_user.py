import pytest
from re import search
from backend.app import create_app
from backend.extensions import db, mail
from sqlalchemy.exc import IntegrityError
from backend.models import User, TokenBlocklist, FriendRequest, Friendship, Event
from datetime import datetime
import json
import uuid

# =============================================================================
# Helper for Auth Headers
# =============================================================================
def get_auth_header(token):
    return {"Authorization": f"Bearer {token}"}

# =============================================================================
# Tests for GET /api/users/profile
# =============================================================================
def test_get_user_info_success(client, logged_in_user):
    user, token = logged_in_user
    
    user.academy = "AGH"
    user.course = "Computer Science"
    user.year = 2
    db.session.commit()

    response = client.get(f"/api/users/profile/{user.user_id}", headers=get_auth_header(token))
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["username"] == user.username
    assert data["email"] == user.email
    assert data["academy"] == "AGH"
    assert data["course"] == "Computer Science"
    assert data["year"] == 2
    
def test_get_user_info_deleted_account(client, logged_in_user):
    user, token = logged_in_user
    user.deleted = True
    db.session.commit()

    response = client.get(f"/api/users/profile/{user.user_id}", headers=get_auth_header(token))
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["username"] == "[deleted]"
    assert data["deleted"] is True

# =============================================================================
# Tests for PUT /api/users/update_profile
# =============================================================================
@pytest.fixture
def mock_app_config(app):
    """Fixture to inject required config data for update_profile."""
    app.config['ACADEMY_DATA'] = {"AGH": {}, "UW": {}}
    app.config['COURSES_DATA'] = ["Computer Science", "Physics"]
    app.config['CLUBS_DATA'] = {"Bite": {}, "DataScience": {}}
    return app

def test_update_profile_success(client, logged_in_user, app):
    user, token = logged_in_user
    
    payload = {
        "username": "new_valid_name",
        "description": "This is my new bio.",
        "academy": "AGH"
    }
    
    response = client.put("/api/users/update_profile", json=payload, headers=get_auth_header(token))
    
    assert response.status_code == 200
    assert response.get_json()["message"] == "Profile updated successfully"
    
    with app.app_context():
        u = db.session.get(User, user.user_id)
        assert u.username == "new_valid_name"
        assert u.description == "This is my new bio."
        assert u.academy == "AGH"

def test_update_profile_username_taken(client, logged_in_user, registered_friend, app):
    user, token = logged_in_user
    friend = registered_friend[0] 

    payload = {
        "username": friend.username 
    }
    
    response = client.put("/api/users/update_profile", json=payload, headers=get_auth_header(token))
    
    assert response.status_code == 400
    assert "Username already taken" in response.get_json()["message"]

def test_update_profile_invalid_academy(client, logged_in_user, app):
    user, token = logged_in_user
    
    payload = {
        "academy": "Hogwarts"
    }
    
    response = client.put("/api/users/update_profile", json=payload, headers=get_auth_header(token))
    
    assert response.status_code == 400
    assert "Such academy doesn't exist" in response.get_json()["message"]

def test_update_profile_missing_data(client, logged_in_user):
    _, token = logged_in_user
    
    response = client.put("/api/users/update_profile", json={}, headers=get_auth_header(token))
    
    assert response.status_code == 400
    assert "Invalid JSON or missing data" in response.get_json()["message"]

def test_update_profile_invalid_username(client, logged_in_user, registered_friend, mock_app_config):
    _, token = logged_in_user
    friend, _ = registered_friend

    payload = {"username": friend.username}
    response = client.put("/api/users/update_profile", json=payload, headers=get_auth_header(token))
    
    assert response.status_code == 400
    assert response.get_json()["message"] == "Username already taken"

def test_update_academic_details_success(client, logged_in_user, mock_app_config, app):
    user, token = logged_in_user
    
    with app.app_context():
        user.academy = "AGH"
        db.session.commit()
        
    u = User.query.filter_by(user_id=user.user_id).first()
    assert u.academy == "AGH"
        
    payload = {
        "course": "Computer Science",
        "year": "3",
        "academic_clubs": "Bite, DataScience"
    }
    
    response = client.put("/api/users/update_academic_details", json=payload, headers=get_auth_header(token))
    assert response.status_code == 200
    
    with app.app_context():
        u = User.query.filter_by(user_id=user.user_id).first()
        assert u.course == "Computer Science"
        assert u.year == 3
        assert "Bite" in u.academic_clubs
        assert "DataScience" in u.academic_clubs


def test_update_academic_details_fails_for_non_primary(client, logged_in_user, app):
    user, token = logged_in_user
    
    with app.app_context():
        user = User.query.filter_by(user_id=user.user_id).first()
        user.academy = "UW" 
        db.session.commit()
        
    payload = {"course": "Computer Science", "year": "2"}
    response = client.put("/api/users/update_academic_details", json=payload, headers=get_auth_header(token))
    
    assert response.status_code == 400

    assert "Only AGH students can add academic details" in response.get_json()["message"]


def test_update_academic_details_fails_missing_pair(client, logged_in_user, app):
    user, token = logged_in_user
    
    with app.app_context():
        user.academy = "AGH"
        db.session.commit()
        
    u = User.query.filter_by(user_id=user.user_id).first()
    assert u.academy == "AGH"

    payload = {"course": "Computer Science"}
    response = client.put("/api/users/update_academic_details", json=payload, headers=get_auth_header(token))
    
    assert response.status_code == 400
    assert response.get_json()["message"] == "Both course and year must be provided together"


def test_update_academic_details_invalid_year(client, logged_in_user, app):
    user, token = logged_in_user
    
    with app.app_context():
        user.academy = "AGH"
        db.session.commit()
        
    u = User.query.filter_by(user_id=user.user_id).first()
    assert u.academy == "AGH"

    payload = {
        "course": "Computer Science",
        "year": "7" 
    }
    
    response = client.put("/api/users/update_academic_details", json=payload, headers=get_auth_header(token))
    
    assert response.status_code == 400
    assert response.get_json()["message"] == "Year must be between 1 and 6"

# =============================================================================
# Tests for PUT /api/users/settings/password
# =============================================================================
def test_change_password_success(client, logged_in_user):
    user, token = logged_in_user
    
    payload = {
        "old_password": "Secret123!", #from fixture
        "new_password": "NewStrongPassword!1"
    }

    response = client.put("/api/users/settings/password", json=payload, headers=get_auth_header(token))
    
    assert response.status_code == 200
    assert user.validate_password("NewStrongPassword!1") is True
    
    # Check if old tokens were revoked
    revoked_token = TokenBlocklist.query.filter_by(user_id=user.user_id).first()
    assert revoked_token is not None

def test_change_password_wrong_old_password(client, logged_in_user):
    _, token = logged_in_user
    payload = {
        "old_password": "WrongPassword123",
        "new_password": "NewStrongPassword!1"
    }
    response = client.put("/api/users/settings/password", json=payload, headers=get_auth_header(token))
    assert response.status_code == 401
    assert response.get_json()["message"] == "Old password incorrect"

# =============================================================================
# Tests for PUT /api/users/settings/change_email
# =============================================================================
def test_change_email_success(client, app, logged_in_user):
    user, token = logged_in_user
    new_email = "new_email@gmail.com"
    old_email = user.email

    with app.app_context():
        yield app
        db.session.rollback()
        db.session.remove()
        db.session.query(User).delete()
        db.session.commit()

@pytest.fixture
def client(app):
    """Create a test client for making requests."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Provide a test CLI runner."""
    return app.test_cli_runner()

# =============================================================================
# Tests for user database connectivity
# =============================================================================

def test_add_user_to_db(app):
    '''Test if a user can be added to the database'''
    with app.app_context():
        username = "test_user"
        password = "123456flask"
        email = "test_user@gmail.com"
        user = User(username, password, email)
        
        db.session.add(user)
        db.session.commit()
        
        retrived_user = User.query.filter_by(username=username).first()
        assert retrived_user is not None

        db.session.delete(retrived_user)
        db.session.commit()
        
        deleted_user = User.query.filter_by(username=username).first()
        assert deleted_user is None
        
        db.session.query(User).delete()
        db.session.commit()

def test_unique_integrity_exception(app):
    '''Test if 2 users with the same email cannot be added to database'''
    with app.app_context():
        username1 = "user1"
        password1 = "root"
        email1 = "example@gmail.com"
        user1 = User(username1, password1, email1)
        
        username2 = "user2"
        password2 = "toor"
        email2 = email1
        user2 = User(username2, password2, email2)
        
        db.session.add(user1)
        db.session.commit()
        
        with pytest.raises(IntegrityError):
            db.session.add(user2)
            db.session.commit()
        
        db.session.rollback()
        db.session.query(User).delete()
        db.session.commit()

def test_email_check_integrity_exception(app):
    '''Test if databse reject invalid email address'''
    with app.app_context():
        username = "user1"
        password = "root"
        email = "wrong.email@@email.com"
        user = User(username, password, email)
        
        with pytest.raises(IntegrityError):
            db.session.add(user)
            db.session.commit()
        
        db.session.rollback()
        db.session.query(User).delete()
        db.session.commit()
        
# =============================================================================
# Tests for user login
# =============================================================================

def test_login_success(client, app):
    with app.app_context():
        username = "user1"
        password = "secret"
        email = "user1@gmail.com"
        user = User(username, password, email)
        
        db.session.add(user)
        db.session.commit()
        assert User.query.filter_by(username=username).first() is not None
        
        response = client.post("/api/login", json={"username": username, "password": password})
        
        assert response.status_code == 200

        assert ("message", "Login successful") and ("username", user.username) in response.get_json()["user"].items()
        
        db.session.rollback()
        db.session.query(User).delete()
        db.session.commit()   
        
def test_login_missing_key(client, app):
    with app.app_context():
        username = "user1"
        password = "secret"
        email = "user1@gmail.com"
        user = User(username, password, email)
        
        db.session.add(user)
        db.session.commit()
        assert User.query.filter_by(username=username).first() is not None
        
        response = client.post("/api/login", json={"username": username})
        
        assert response.status_code == 400
        assert response.get_json() == {
            "message": "Bad request"
        }
        
        db.session.rollback()
        db.session.query(User).delete()
        db.session.commit()

def test_login_invalid_credentials(client, app):
    with app.app_context():
        username = "user1"
        password = "secret"
        email = "user1@gmail.com"
        user = User(username, password, email)
        
        db.session.add(user)
        db.session.commit()
        assert User.query.filter_by(username=username).first() is not None
        
        response = client.post("/api/login", json={"username": username, "password": "different_passwd123"})
        
        assert response.status_code == 401
        assert response.get_json() == {
            "message": "Invalid username or password"
        }
        
        db.session.rollback()
        db.session.query(User).delete()
        db.session.commit()

# =============================================================================
# Tests for user registration
# =============================================================================

def test_register_successful(client, app):
    with app.app_context():
        username = "user1"
        password = "secret"
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
        
        db.session.rollback()
        db.session.query(User).delete()
        db.session.commit()

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
        
        db.session.rollback()
        db.session.query(User).delete()
        db.session.commit()

def test_register_invalid_credentials(client, app):
    with app.app_context():
        username = "a"
        password = "secret"
        email = "user1@gmail.com"
        
        payload = {
            "username": username,
            "password": password,
            "email": email
        }
        
        response1 = client.post("/api/register", json=payload)
        
        assert response1.status_code == 400
        assert response1.get_json() == {
            "message": "Invalid username or email"
        }
        assert User.query.filter_by(username=username).first() is None
        
        username = "goodusername"
        password = "secret"
        email = "@gmail[]'user1@gmail.com"
        
        payload = {
            "username": username,
            "password": password,
            "email": email
        }
        
        response2 = client.post("api/register", json=payload)
        
        assert response1.status_code == 400
        assert response1.get_json() == {
            "message": "Invalid username or email"
        }
        assert User.query.filter_by(username=username).first() is None
        
        db.session.rollback()
        db.session.query(User).delete()
        db.session.commit()
        
def test_register_username_taken(client, app):
    with app.app_context():
        username1 = "user1"
        password1 = "secret"
        email1 = "user1@gmail.com"
        
        user1 = User(username1, password1, email1)
        db.session.add(user1)
        db.session.commit()
        
        assert User.query.filter_by(username=username1).first() is not None

        username2 = username1
        password2 = "secret"
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
        
        db.session.rollback()
        db.session.query(User).delete()
        db.session.commit()

def test_register_email_exists(client, app):
    with app.app_context():
        username1 = "user1"
        password1 = "secret"
        email1 = "user1@gmail.com"
        
        user1 = User(username1, password1, email1)
        db.session.add(user1)
        db.session.commit()
        
        assert User.query.filter_by(username=username1).first() is not None

        username2 = "user2"
        password2 = "secret"
        email2 = email1
        
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
        
        db.session.rollback()
        db.session.query(User).delete()
        db.session.commit()

# =============================================================================
# Tests for jwt authorization
# =============================================================================

def test_jwt_login(client, app):
    with app.app_context():
        username1 = "user1"
        password1 = "secret"
        email1 = "user1@gmail.com"
        
        user1 = User(username1, password1, email1)
        db.session.add(user1)
        db.session.commit()

        assert User.query.filter_by(username=username1).first() is not None

        payload = {
            "username": username1,
            "password": password1,
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

        assert protected_response.get_json() == {
            "message": "Incorrect token"
        }
        assert protected_response.status_code == 401

def test_jwt_no_token(client, app):
    with app.app_context():
        protected_response = client.get("/user")

        assert protected_response.get_json() == {
            "message": "Missing or invalid token"
        }
        assert protected_response.status_code == 401

def test_jwt_revoke_token(client, app):
    with app.app_context():
        username1 = "user1"
        password1 = "secret"
        email1 = "user1@gmail.com"
        
        user1 = User(username1, password1, email1)
        db.session.add(user1)
        db.session.commit()

        assert User.query.filter_by(username=username1).first() is not None

        payload = {
            "username": username1,
            "password": password1,
        }
        response = client.post("/api/login", json=payload)
        assert response.status_code == 200

        data = json.loads(response.data)
        token = data["access_token"]

        protected_response1 = client.get("/user", headers={
            "Authorization": f"Bearer {token}"
        })
        assert protected_response1.status_code == 200

        revoke_response = client.get("/revoke_access", headers={
            "Authorization": f"Bearer {token}"
        })
        assert revoke_response.status_code == 200
        assert revoke_response.get_json() == {
            "message": "access token revoked"
        }

        protected_response2 = client.get("/user", headers={
            "Authorization": f"Bearer {token}"
        })
        assert protected_response2.status_code == 401
        assert protected_response2.get_json() == {
            "msg": "Token has been revoked"
        }

        db.session.rollback()
        db.session.query(User).delete()
        db.session.query(TokenBlocklist).delete()
        db.session.commit()

def test_jwt_revoke_refresh_token(client, app):
    with app.app_context():
        username1 = "user1"
        password1 = "secret"
        email1 = "user1@gmail.com"
        
        user1 = User(username1, password1, email1)
        db.session.add(user1)
        db.session.commit()

        assert User.query.filter_by(username=username1).first() is not None

        payload = {
            "username": username1,
            "password": password1,
        }
        response = client.post("/api/login", json=payload)
        assert response.status_code == 200

        data = json.loads(response.data)
        refresh_token = data["refresh_token"]

        revoke_response = client.get("/revoke_refresh", headers={
            "Authorization": f"Bearer {refresh_token}"
        })
        assert revoke_response.status_code == 200
        assert revoke_response.get_json() == {
            "message": "refresh token revoked"
        }

        refresh_response = client.post("/refresh")
        assert refresh_response.status_code == 401
        
        db.session.rollback()
        db.session.query(User).delete()
        db.session.query(TokenBlocklist).delete()
        db.session.commit()

# =============================================================================
# Tests for password resetting
# =============================================================================

def test_password_reset(client, app):
    with app.app_context():
        username = "test_user"
        password = "123456flask"
        email = "test_user@gmail.com"
        user = User(username, password, email)
        
        db.session.add(user)
        db.session.commit()

        email_payload = {
            "email": email
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
                "new_password": "dupa123"
            }

            response = client.post(token_path, json=password_payload)
            assert response.status_code == 200

        response = client.post("/api/login", json={"username": user.username, "password": "dupa123"})
        assert response.status_code == 200

        db.session.rollback()
        db.session.query(User).delete()
        db.session.commit()

def test_password_reset_invalid_email(client, app):
    with app.app_context():
        email_payload = {
            "email": "invalid_user@gmail.com"
        }

        with mail.record_messages() as outbox:
            response = client.post("/reset_password_request", json=email_payload)

            assert response.status_code == 401
            assert len(outbox) == 0

# =============================================================================
# Tests for handling friend requests
# =============================================================================
def test_accept_friend_request(client, app):
    with app.app_context():
        username1 = "user1"
        password1 = "root"
        email1 = "example1@gmail.com"
        user = User(username1, password1, email1)
        
        username2 = "user2"
        password2 = "toor"
        email2 = "example2@gmail.com"
        friend = User(username2, password2, email2)

        db.session.add(user)
        db.session.add(friend)
        db.session.commit()

        #user logs in
        response_login = client.post("/api/login", json={"username": username1, "password": password1})
        assert response_login.status_code == 200

        data = json.loads(response_login.data)
        token = data["access_token"]

        #create friend request
        response_create_request = client.post(f"/create_friend_request/{friend.user_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_create_request.status_code == 200
        assert response_create_request.get_json() == {
            "message": "Friend request created"
        }

        assert FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend.user_id).first() is not None
        
        #friend logs in
        response_friend_login = client.post("/api/login", json={"username": username2, "password": password2})
        assert response_friend_login.status_code == 200

        friend_data = json.loads(response_friend_login.data)
        friend_token = friend_data["access_token"]

        #accept friend request
        response_accept_request = client.post(f"/accept_friend_request/{user.user_id}", headers={
            "Authorization": f"Bearer {friend_token}"
        })

        assert response_accept_request.status_code == 200
        assert response_accept_request.get_json() == {
            "message": "Friend request accepted"
        }

    response = client.post(f"/api/email/confirm_change/{token}")
    assert response.status_code == 401

# =============================================================================
# Test display_name property
# =============================================================================

#/api/users/profile
def test_profile_displays_deleted_username(client, logged_in_user):
    user, token = logged_in_user
    
    user.deleted = True
    user.username = "del_a1b2c3d4e5"
    db.session.commit()

    response = client.get(f"/api/users/profile/{user.user_id}", headers=get_auth_header(token))
    
    assert response.status_code == 200
    data = response.get_json()
    
    assert data["username"] == "[deleted]"
    assert data["deleted"] is True

#/api/friends/list
def test_friends_list_shows_deleted_user(client, app, logged_in_user):
    active_user, token = logged_in_user
    
    with app.app_context():
        deleted_friend = User(
            username="del_123456789", 
            email="del_123@del.local", 
            password="scrambled",
            deleted=True
        )
        db.session.add(deleted_friend)
        db.session.commit()

        id1, id2 = str(active_user.user_id), str(deleted_friend.user_id)
        u_id, f_id = (id1, id2) if id1 < id2 else (id2, id1)

        friendship = Friendship(user_id=u_id, friend_id=f_id)
        db.session.add(friendship)
        db.session.commit()

    response = client.get("/api/friends/list", headers=get_auth_header(token))
    
    assert response.status_code == 200
    data = response.get_json()["friends"]
    
    assert len(data) == 1
    assert data[0]["username"] == "[deleted]"


#/api/events/feed
def test_feed_shows_deleted_creator(client, app, logged_in_user):
    active_user, token = logged_in_user
    
    with app.app_context():
        deleted_creator = User(
            username="del_987654321", 
            email="del_987@del.local", 
            password="scrambled",
            deleted=True
        )
        db.session.add(deleted_creator)
        db.session.commit()

        future_date = datetime.now(timezone.utc) + timedelta(days=1)
        
        assert FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend.user_id).first() is None

        db.session.rollback()
        db.session.query(User).delete()
        db.session.query(FriendRequest).delete()
        db.session.query(Friendship).delete()
        db.session.commit()

def test_decline_friend_request(client, app):
    with app.app_context():
        username1 = "user1"
        password1 = "root"
        email1 = "example1@gmail.com"
        user = User(username1, password1, email1)
        
        username2 = "user2"
        password2 = "toor"
        email2 = "example2@gmail.com"
        friend = User(username2, password2, email2)

        db.session.add(user)
        db.session.add(friend)
        db.session.commit()

        #user logs in
        response_login = client.post("/api/login", json={"username": username1, "password": password1})
        assert response_login.status_code == 200

        data = json.loads(response_login.data)
        token = data["access_token"]

        #create friend request
        response_create_request = client.post(f"/create_friend_request/{friend.user_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_create_request.status_code == 200
        assert response_create_request.get_json() == {
            "message": "Friend request created"
        }

        assert FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend.user_id).first() is not None
        
        #friend logs in
        response_friend_login = client.post("/api/login", json={"username": username2, "password": password2})
        assert response_friend_login.status_code == 200

        friend_data = json.loads(response_friend_login.data)
        friend_token = friend_data["access_token"]

        #declne friend request
        response_decline_request = client.post(f"/decline_friend_request/{user.user_id}", headers={
            "Authorization": f"Bearer {friend_token}"
        })

        assert response_decline_request.status_code == 200
        assert response_decline_request.get_json() == {
            "message": "Friend request declined"
        }

        assert (Friendship.query.filter_by(user_id=user.user_id, friend_id=friend.user_id).first() and
                Friendship.query.filter_by(user_id=friend.user_id, friend_id=user.user_id).first()) is None
        
        assert FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend.user_id).first() is None

        db.session.rollback()
        db.session.query(User).delete()
        db.session.query(FriendRequest).delete()
        db.session.query(Friendship).delete()
        db.session.commit()

def test_friend_not_exist(client, app):
    with app.app_context():
        #create user
        username1 = "user1"
        password1 = "root"
        email1 = "example1@gmail.com"
        user = User(username1, password1, email1)

        db.session.add(user)
        db.session.commit()

        #user logs in
        response_login = client.post("/api/login", json={"username": username1, "password": password1})
        assert response_login.status_code == 200

        data = json.loads(response_login.data)
        token = data["access_token"]

        #create friend request
        friend_id = uuid.uuid4()
        response_create_request = client.post(f"/create_friend_request/{friend_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_create_request.status_code == 400
        assert FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend_id).first() is None

        db.session.rollback()
        db.session.query(User).delete()
        db.session.query(FriendRequest).delete()
        db.session.query(Friendship).delete()
        db.session.commit()

def test_befriend_yourself(client, app):
    with app.app_context():
        #create user
        username1 = "user1"
        password1 = "root"
        email1 = "example1@gmail.com"
        user = User(username1, password1, email1)

        db.session.add(user)
        db.session.commit()

        #user logs in
        response_login = client.post("/api/login", json={"username": username1, "password": password1})
        assert response_login.status_code == 200

        data = json.loads(response_login.data)
        token = data["access_token"]

        #create friend request
        response_create_request = client.post(f"/create_friend_request/{user.user_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_create_request.status_code == 400
        assert FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=user.user_id).first() is None

        db.session.rollback()
        db.session.query(User).delete()
        db.session.query(FriendRequest).delete()
        db.session.query(Friendship).delete()
        db.session.commit()

def test_request_exists(client, app):
    with app.app_context():
        username1 = "user1"
        password1 = "root"
        email1 = "example1@gmail.com"
        user = User(username1, password1, email1)
        
        username2 = "user2"
        password2 = "toor"
        email2 = "example2@gmail.com"
        friend = User(username2, password2, email2)

        db.session.add(user)
        db.session.add(friend)
        db.session.commit()

        new_request = FriendRequest(sender_id=user.user_id, receiver_id=friend.user_id)
        db.session.add(new_request)
        db.session.commit()

        #user logs in
        response_login = client.post("/api/login", json={"username": username1, "password": password1})
        assert response_login.status_code == 200

        data = json.loads(response_login.data)
        token = data["access_token"]

        #create friend request
        response_create_request = client.post(f"/create_friend_request/{friend.user_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_create_request.status_code == 400
        assert response_create_request.get_json() == {
            "message": "Request already exists"
        }

        assert len(FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend.user_id).all()) == 1

        db.session.rollback()
        db.session.query(User).delete()
        db.session.query(FriendRequest).delete()
        db.session.query(Friendship).delete()
        db.session.commit()

def test_friendship_exists(client, app):
    with app.app_context():
        username1 = "user1"
        password1 = "root"
        email1 = "example1@gmail.com"
        user = User(username1, password1, email1)
        
        username2 = "user2"
        password2 = "toor"
        email2 = "example2@gmail.com"
        friend = User(username2, password2, email2)

        db.session.add(user)
        db.session.add(friend)
        db.session.commit()

        if user.user_id < friend.user_id:
            new_friendship = Friendship(user_id=user.user_id, friend_id=friend.user_id)
        else:
            new_friendship = Friendship(user_id=friend.user_id, friend_id=user.user_id)

        db.session.add(new_friendship)
        db.session.commit()

        #user logs in
        response_login = client.post("/api/login", json={"username": username1, "password": password1})
        assert response_login.status_code == 200

        data = json.loads(response_login.data)
        token = data["access_token"]

        #create friend request
        response_create_request = client.post(f"/create_friend_request/{friend.user_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_create_request.status_code == 400
        assert response_create_request.get_json() == {
            "message": "Friendship already exists"
        }

        assert FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend.user_id).first() is None

        db.session.rollback()
        db.session.query(User).delete()
        db.session.query(FriendRequest).delete()
        db.session.query(Friendship).delete()
        db.session.commit()

def test_accept_request_not_exist(client, app):
    with app.app_context():
        username1 = "user1"
        password1 = "root"
        email1 = "example1@gmail.com"
        user = User(username1, password1, email1)
        
        username2 = "user2"
        password2 = "toor"
        email2 = "example2@gmail.com"
        friend = User(username2, password2, email2)

        db.session.add(user)
        db.session.add(friend)
        db.session.commit()
        
        #friend logs in
        response_friend_login = client.post("/api/login", json={"username": username2, "password": password2})
        assert response_friend_login.status_code == 200

        friend_data = json.loads(response_friend_login.data)
        friend_token = friend_data["access_token"]

        #accept friend request
        response_accept_request = client.post(f"/accept_friend_request/{user.user_id}", headers={
            "Authorization": f"Bearer {friend_token}"
        })

        assert response_accept_request.status_code == 400
        assert response_accept_request.get_json() == {
            "message": "Such request doesn't exist"
        }

        assert (Friendship.query.filter_by(user_id=user.user_id, friend_id=friend.user_id).first() and
                Friendship.query.filter_by(user_id=friend.user_id, friend_id=user.user_id).first()) is None

        db.session.rollback()
        db.session.query(User).delete()
        db.session.query(FriendRequest).delete()
        db.session.query(Friendship).delete()
        db.session.commit()

def test_decline_request_not_exist(client, app):
    with app.app_context():
        username1 = "user1"
        password1 = "root"
        email1 = "example1@gmail.com"
        user = User(username1, password1, email1)
        
        username2 = "user2"
        password2 = "toor"
        email2 = "example2@gmail.com"
        friend = User(username2, password2, email2)

        db.session.add(user)
        db.session.add(friend)
        db.session.commit()
        
        #friend logs in
        response_friend_login = client.post("/api/login", json={"username": username2, "password": password2})
        assert response_friend_login.status_code == 200

        friend_data = json.loads(response_friend_login.data)
        friend_token = friend_data["access_token"]

        #decline friend request
        response_decline_request = client.post(f"/decline_friend_request/{user.user_id}", headers={
            "Authorization": f"Bearer {friend_token}"
        })

        assert response_decline_request.status_code == 400
        assert response_decline_request.get_json() == {
            "message": "Such request doesn't exist"
        }

        assert (Friendship.query.filter_by(user_id=user.user_id, friend_id=friend.user_id).first() and
                Friendship.query.filter_by(user_id=friend.user_id, friend_id=user.user_id).first()) is None

        db.session.rollback()
        db.session.query(User).delete()
        db.session.query(FriendRequest).delete()
        db.session.query(Friendship).delete()
        db.session.commit()

# =============================================================================
# Tests for handling events
# =============================================================================
def test_create_event(client, app):
    with app.app_context():
        username1 = "user1"
        password1 = "root"
        email1 = "example1@gmail.com"
        user = User(username1, password1, email1)

        db.session.add(user)
        db.session.commit()

        #user logs in
        response_login = client.post("/api/login", json={"username": username1, "password": password1})
        assert response_login.status_code == 200

        data = json.loads(response_login.data)
        token = data["access_token"]

        #create event
        payload = {
            "name": "event1",
            "description": "very cool event",
            "date": "01.01.2026",
            "time": "21:37",
            "location": "here"
        }

        response_create_event = client.post(f"/create_event", headers={
            "Authorization": f"Bearer {token}"
        }, json=payload)

        assert response_create_event.status_code == 200
        assert response_create_event.get_json() == {
            "message": "Event created successfully"
        }

        db.session.rollback()
        db.session.query(User).delete()
        db.session.query(Event).delete()
        db.session.commit()

def test_create_event_invalid_date(client, app):
    with app.app_context():
        username1 = "user1"
        password1 = "root"
        email1 = "example1@gmail.com"
        user = User(username1, password1, email1)

        db.session.add(user)
        db.session.commit()

        #user logs in
        response_login = client.post("/api/login", json={"username": username1, "password": password1})
        assert response_login.status_code == 200

        data = json.loads(response_login.data)
        token = data["access_token"]

        #create event
        payload = {
            "name": "event1",
            "description": "very cool event",
            "date": "01.01.1995",
            "time": "21:37",
            "location": "here"
        }

        response_create_event = client.post(f"/create_event", headers={
            "Authorization": f"Bearer {token}"
        }, json=payload)

        assert response_create_event.status_code == 400
        assert response_create_event.get_json() == {
            "message": "Event date must be in the future"
        }

        db.session.rollback()
        db.session.query(User).delete()
        db.session.query(Event).delete()
        db.session.commit()


def test_delete_event(client, app):
    with app.app_context():
        username1 = "user1"
        password1 = "root"
        email1 = "example1@gmail.com"
        user = User(username1, password1, email1)

        db.session.add(user)
        db.session.commit()

        #user logs in
        response_login = client.post("/api/login", json={"username": username1, "password": password1})
        assert response_login.status_code == 200

        data = json.loads(response_login.data)
        token = data["access_token"]

        #create event
        payload = {
            "name": "to delete",
            "description": "very cool event",
            "date": "01.01.2026",
            "time": "21:37",
            "location": "here"
        }

        response_create_event = client.post(f"/create_event", headers={
            "Authorization": f"Bearer {token}"
        }, json=payload)

        assert response_create_event.status_code == 200
        assert response_create_event.get_json() == {
            "message": "Event created successfully"
        }

        event = Event.query.filter_by(name="to delete").first()
        assert event is not None

        #delete event
        response_delete_event = client.delete(f"/delete_event/{event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_delete_event.status_code == 200
        assert response_delete_event.get_json() == {
            "message": "Event deleted successfully"
        }

        deleted = Event.query.filter_by(event_id=event.event_id).first()
        assert deleted is None

        db.session.rollback()
        db.session.query(User).delete()
        db.session.query(Event).delete()
        db.session.commit()

def test_delete_event_not_owner(client, app):
    with app.app_context():
        # user1 owns event
        user1 = User("user1", "root", "u1@example.com")
        user2 = User("user2", "root", "u2@example.com")
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        event = Event(
            name="event1",
            description="private",
            date_and_time=datetime(2026, 1, 1, 21, 37),
            location="here",
            creator_id=user1.user_id
        )
        db.session.add(event)
        db.session.commit()

    response = client.get("/api/events/feed", headers=get_auth_header(token))
    
    assert response.status_code == 200

    response_json = response.get_json()
    events = response_json.get("data", [])
    
    assert len(events) >= 1
    
    ghost_event = next(e for e in events if e["name"] == "Ghost Event")
    assert ghost_event["creator_username"] == "[deleted]"

        # attempt delete
        response_delete_event = client.delete(f"/delete_event/{event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_delete_event.status_code == 401
        assert response_delete_event.get_json() == {
            "message": "You can delete your own events only"
        }

def test_delete_invalid_event(client, app):
    with app.app_context():
        user1 = User("user1", "root", "u1@example.com")
        db.session.add(user1)
        db.session.commit()

        login_resp = client.post("/api/login", json={"username": "user1", "password": "root"})
        token = login_resp.get_json()["access_token"]

        # attempt delete
        response_delete_event = client.delete(f"/delete_event/{uuid.uuid4()}", headers={
            "Authorization": f"Bearer {token}"
        })

        deleted_user_comment = Comment(
            event_id=event.event_id,
            user_id=deleted_commenter.user_id,
            content="This is a comment from the past.",
        )
        db.session.add(deleted_user_comment)
        db.session.commit()
        
        event_id_to_test = event.event_id

    response = client.get(f"/api/comments/event/{event_id_to_test}", headers=get_auth_header(token))
    
    assert response.status_code == 200
    comments = response.get_json()["comments"]
    
    assert len(comments) == 1
    assert comments[0]["content"] == "This is a comment from the past."
    assert comments[0]["username"] == "[deleted]"

# =============================================================================
# Tests for profile pictures lifecycle
# =============================================================================

def test_get_profile_no_picture(client, logged_in_user, app):
    user, token = logged_in_user
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(f"/api/users/profile/{user.user_id}", headers=headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["profile_picture"] is None


def test_update_profile_add_picture(client, logged_in_user, app):
    user, token = logged_in_user
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "profile_picture": {"cloud_id": "profile_pic_123"}
    }
    
    response = client.put("/api/users/update_profile", json=payload, headers=headers)
    assert response.status_code == 200
    
    profile_res = client.get(f"/api/users/profile/{user.user_id}", headers=headers)
    pic_data = profile_res.get_json()["profile_picture"]
    
    assert pic_data is not None
    assert pic_data["cloud_id"] == "profile_pic_123"
    assert "url" in pic_data 


@patch('cloudinary.uploader.destroy')
def test_update_profile_replace_picture(mock_destroy, client, logged_in_user, app):
    user, token = logged_in_user
    headers = {"Authorization": f"Bearer {token}"}

    client.put("/api/users/update_profile", json={"profile_picture": {"cloud_id": "old_pic"}}, headers=headers)
    
    replace_payload = {
        "profile_picture": {"cloud_id": "new_pic"}
    }
    response = client.put("/api/users/update_profile", json=replace_payload, headers=headers)
    assert response.status_code == 200
    
    mock_destroy.assert_called_once_with("old_pic")
    
    with app.app_context():
        user = User.query.filter_by(user_id=user.user_id).first()
        assert user.profile_picture == "new_pic"


@patch('cloudinary.uploader.destroy')
def test_update_profile_delete_picture(mock_destroy, client, logged_in_user, app):
    user, token = logged_in_user
    headers = {"Authorization": f"Bearer {token}"}

    client.put("/api/users/update_profile", json={"profile_picture": {"cloud_id": "to_delete_pic"}}, headers=headers)

    delete_payload = {
        "profile_picture": None
    }
    response = client.put("/api/users/update_profile", json=delete_payload, headers=headers)
    assert response.status_code == 200

    mock_destroy.assert_called_once_with("to_delete_pic")
    
    with app.app_context():
        user = User.query.filter_by(user_id=user.user_id).first()
        assert user.profile_picture == None


@patch('cloudinary.uploader.destroy')
def test_delete_account_removes_picture(mock_destroy, client, logged_in_user, app):
    user, token = logged_in_user
    headers = {"Authorization": f"Bearer {token}"}
    
    client.put("/api/users/update_profile", json={"profile_picture": {"cloud_id": "account_del_pic"}}, headers=headers)
    
    delete_payload = {"password": "Secret123!"} 
    
    response = client.delete("/api/users/settings/delete_account", json=delete_payload, headers=headers)
    assert response.status_code == 200
    
    mock_destroy.assert_called_once_with("account_del_pic")
    
    with app.app_context():
        user = User.query.filter_by(user_id=user.user_id).first()
        assert user.profile_picture == None


def test_get_user_info_friend_count(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend = registered_friend[0]

        if user.user_id < friend.user_id:
            friendship = Friendship(user_id=user.user_id, friend_id=friend.user_id)
        else:
            friendship = Friendship(user_id=friend.user_id, friend_id=user.user_id)
            
        db.session.add(friendship)
        db.session.commit()
        
        response = client.get(f"/api/users/profile/{user.user_id}", headers=get_auth_header(token))
        assert response.status_code == 200
        
        data = response.get_json()
        assert "friend_count" in data
        assert data["friend_count"] == 1
