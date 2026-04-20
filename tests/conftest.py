import pytest
from backend import create_app
from backend.extensions import db, mail
from backend.models import User, TokenBlocklist, Friendship, FriendRequest, Event
from backend.helpers import add_token_to_db
from flask_jwt_extended import create_access_token
from datetime import datetime, timezone, timedelta
from re import search

@pytest.fixture(scope="session")
def app():
    """Create and configure a new Flask app instance for testing."""
    app = create_app(test_mode=True)

    with app.app_context():
        migrator_engine = db.create_engine(app.config['MIGRATOR_URI'])
        db.metadata.create_all(bind=migrator_engine)

        yield app
        db.metadata.drop_all(bind=migrator_engine)
        db.session.remove()

@pytest.fixture
def client(app):
    """Create a test client for making requests."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Provide a test CLI runner."""
    return app.test_cli_runner()

@pytest.fixture(autouse=True)
def rollback_db(app):
    """Clean database rows after each test."""
    yield  
    db.session.rollback()  
    for model in [User, TokenBlocklist, Friendship, FriendRequest, Event]:
        db.session.query(model).delete() 
    db.session.commit()

@pytest.fixture
def registered_user(app):
    password = "Secret123!"

    user = User(
        username="user_fixture", 
        password=password, 
        email="user_fixture@gmail.com",
        is_confirmed=True
    )
    db.session.add(user)
    db.session.commit()
    
    return user, password

@pytest.fixture
def registered_friend(app):
    password = "FriendSecret123!"

    friend = User(
        username="friend", 
        password=password, 
        email="friend@gmail.com",
        is_confirmed=True
    )
    db.session.add(friend)
    db.session.commit()
    
    return friend, password

@pytest.fixture
def logged_in_user(app, registered_user):
    user, _ = registered_user

    access_token = create_access_token(identity=user.user_id)
    add_token_to_db(access_token)
    
    return user, access_token

@pytest.fixture
def create_events(app, logged_in_user):
    headers = {"Authorization": f"Bearer {logged_in_user[1]}"}
    user, _ = logged_in_user 
    
    events_to_insert = []
    
    for event_id in range(1, 23):
        event_time = datetime.now(timezone.utc) + timedelta(days=event_id)
        payload = {"name": str(event_id)+"ssss", "description": "Lore ipsum", "date": event_time.strftime("%d.%m.%Y"), "time":event_time.strftime("%H:%M"), "location":"Poland", "is_private": False}
        response=client.post("/create_event", json=payload, headers=headers)
        assert response.status_code == 201

@pytest.fixture
def event(client, logged_in_user):
    token = logged_in_user[1]

    future_date = (datetime.now(timezone.utc) + timedelta(days=1))

    payload = {
        "name": "event1",
        "description": "very cool event",
        "date": future_date.strftime("%d.%m.%Y"),
        "time": "21:37",
        "location": "here",
        "is_private": False
    }

    client.post("/api/events/create", headers={"Authorization": f"Bearer {token}"}, json=payload)
    event = Event.query.filter_by(event_name="event1").first()
    return event
