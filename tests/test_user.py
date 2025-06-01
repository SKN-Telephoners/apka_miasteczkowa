import pytest
from re import search
from backend.app import create_app
from backend.extensions import db, mail
from sqlalchemy.exc import IntegrityError
from backend.models import User, TokenBlocklist, FriendRequest, Friendship
import json
import uuid

@pytest.fixture
def app():
    """Create and configure a new Flask app instance for testing."""
    app = create_app(test_mode=True)

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

        assert (Friendship.query.filter_by(user_id=user.user_id, friend_id=friend.user_id).first() or
                Friendship.query.filter_by(user_id=friend.user_id, friend_id=user.user_id).first()) is not None
        
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