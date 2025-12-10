import pytest
from backend.extensions import db
from backend.models import Event
from datetime import datetime
import uuid

# =============================================================================
# Tests for handling events
# =============================================================================
def test_create_event(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

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

def test_create_event_invalid_date(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

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

def test_delete_event(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

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

def test_delete_event_not_owner(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend = registered_friend[0]

        event = Event(
            name="event1",
            description="private",
            date_and_time=datetime(2026, 1, 1, 21, 37),
            location="here",
            creator_id=friend.user_id #other user
        )
        db.session.add(event)
        db.session.commit()

        # attempt delete
        response_delete_event = client.delete(f"/delete_event/{event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_delete_event.status_code == 401
        assert response_delete_event.get_json() == {
            "message": "You can delete your own events only"
        }

def test_delete_invalid_event(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

        # attempt delete
        response_delete_event = client.delete(f"/delete_event/{uuid.uuid4()}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_delete_event.status_code == 400
        assert response_delete_event.get_json() == {
            "message": "Event doesn't exist"
        }


def test_get_publicevent(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

      
        past_date = "12:11:20250" 
        
        public_event = Event(
            name="Publiczny Koncert",
            typeof_event="public",
            date_and_time=past_date,
            user_id=user.id 
            
        )
        
        private_event = Event(
            name="Prywatne Spotkanie",
            typeof_event="private",
            date_and_time=past_date,
            user_id=user.id
        )

        db.session.add(public_event)
        db.session.add(private_event)
        db.session.commit()

        # 2. Wywołanie endpointu (ACT)
        response = client.get('/get_public_events', headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 200
        data = response.get_json()
        
        assert isinstance(data, list)
        
        assert len(data) == 1
        assert data[0]["name"] == "Publiczny Koncert"
        assert data[0]["typeof_event"] == "public"