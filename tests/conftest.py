import pytest
from backend.app import create_app
from backend.extensions import db
from backend.models import User, TokenBlocklist, Friendship, FriendRequest, Event

@pytest.fixture
def app():
    """Create and configure a new Flask app instance for testing."""
    app = create_app(test_mode=True)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()  

@pytest.fixture(autouse=True)
def rollback_db(app):
    """Rollback any changes made to the database after each test."""
    yield  # run the test
    db.session.rollback()  # undo everything done not commited
    for model in [User, TokenBlocklist, Friendship, FriendRequest, Event]:
        db.session.query(model).delete() # delete everything commited
    db.session.commit()

@pytest.fixture
def client(app):
    """Create a test client for making requests."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Provide a test CLI runner."""
    return app.test_cli_runner()

@pytest.fixture
def registered_user(client):
    # Updated password to meet new complexity requirements
    payload = {"username": "user1", "password": "Secret123", "email": "user1@gmail.com"}
    client.post("/api/register", json=payload)
    user = User.query.filter_by(username="user1").first()
    return user, payload["password"]

@pytest.fixture
def logged_in_user(registered_user, client):
    user, password = registered_user
    payload = {"username": user.username, "password": password}
    response = client.post("/api/login", json=payload)
    data = response.get_json()
    token = data["access_token"]
    return user, token


@pytest.fixture
def registered_friend(client):
    # Updated password to meet new complexity requirements
    payload = {"username": "friend", "password": "FriendSecret123", "email": "friend@gmail.com"}
    client.post("/api/register", json=payload)
    friend = User.query.filter_by(username="friend").first()
    return friend, payload["password"]


@pytest.fixture
def create_event(client):
    # cerate 21 events for tests
    event_id=0
    while(event_id!=21):
        payload = {"name": event_id, "description": "Lore ipsum", "date":"1.1.2022", "time":"14:20", "location":"Poland"}
        client.post("/create_event", json=payload)
        event_id+=1


