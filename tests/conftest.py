import pytest
from backend.app import create_app
from backend.extensions import db, mail
from backend.models import User, TokenBlocklist, Friendship, FriendRequest, Event
from datetime import datetime, timezone, timedelta
from re import search

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
    #confirm email
    with mail.record_messages() as outbox:
        response = client.post("/mail_auth_request", json={"email": user.email})
        match = search(r'(http://.+/mail_auth/\S+)', outbox[0].body)
        auth_url = match.group()
        token_path = auth_url.replace("http://localhost", "")
        client.post(token_path)

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
    #confirm email
    with mail.record_messages() as outbox:
        response = client.post("/mail_auth_request", json={"email": friend.email})
        match = search(r'(http://.+/mail_auth/\S+)', outbox[0].body)
        auth_url = match.group()
        token_path = auth_url.replace("http://localhost", "")
        client.post(token_path)
    return friend, payload["password"]


@pytest.fixture
def create_events(client,logged_in_user):
    # cerate 21 events for tests
    headers = {"Authorization": f"Bearer {logged_in_user[1]}"}

    event_id=0
    while(event_id!=22):
        event_id+=1
        event_time = datetime.now(timezone.utc) + timedelta(days=event_id)
        payload = {"name": str(event_id)+"ssss", "description": "Lore ipsum", "date": event_time.strftime("%d.%m.%Y"), "time":event_time.strftime("%H:%M"), "location":"Poland"}
        response=client.post("/create_event", json=payload,headers=headers)
        assert response.status_code == 200

@pytest.fixture
def event(client, logged_in_user):
    token = logged_in_user[1]

    payload = {
        "name": "event1",
        "description": "very cool event",
        "date": "01.01.2026",
        "time": "21:37",
        "location": "here"
    }

    client.post(f"/create_event", headers={"Authorization": f"Bearer {token}"}, json=payload)
    event = Event.query.filter_by(name="event1").first()
    return event
