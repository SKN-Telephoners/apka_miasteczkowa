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
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()  

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
    password = "Secret123"

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
    password = "FriendSecret123"

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
    user, _ = logged_in_user 
    
    events_to_insert = []
    
    for event_id in range(1, 23):
        event_time = datetime.now(timezone.utc) + timedelta(days=event_id)
        
        new_event = Event(
            name=f"{event_id}ssss",
            description="Lore ipsum",
            date_and_time=event_time,
            location="Poland",
            creator_id=user.user_id
        )
        events_to_insert.append(new_event)
    
    db.session.add_all(events_to_insert)
    db.session.commit()
    
    return events_to_insert

@pytest.fixture
def event(client, logged_in_user):
    user, _ = logged_in_user
    
    future_date = datetime.now(timezone.utc) + timedelta(days=1)
    
    new_event = Event(
        name="event1",
        description="very cool event",
        date_and_time=future_date,
        location="here",
        creator_id=user.user_id
    )
    
    db.session.add(new_event)
    db.session.commit()
    
    return new_event