import pytest
from backend.app import create_app
from backend.extensions import db
from sqlalchemy.exc import IntegrityError
from backend.models import User

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