import pytest
from backend.app import create_app
from backend.extensions import db, mail
from sqlalchemy.exc import IntegrityError
from backend.models import User
import json

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
        assert response.get_json() == {
            "message": "Login successful",
            "user": {
                "username": user.username
            }
        }
        
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

        db.session.rollback()
        db.session.query(User).delete()
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
            
            reset_token = outbox[0].body

            password_payload = {
                "new_password": "dupa123"
            }

            response = client.post(f"/reset_password/{reset_token}", json=password_payload)
            assert response.status_code == 200

        response = client.post("/api/login", json={"username": user.username, "password": "dupa123"})
        assert response.status_code == 200

        db.session.rollback()
        db.session.query(User).delete()
        db.session.commit()