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
            "date": "01.01.2050",
            "time": "21:37",
            "location": "here"
        }

        response_create_event = client.post(f"/api/events/create", headers={
            "Authorization": f"Bearer {token}"
        }, json=payload)

        assert response_create_event.status_code == 200
        data = response_create_event.get_json()
        assert data["message"] == "Event created successfully"
        assert "event_id" in data # New requirement: return ID

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

        response_create_event = client.post(f"/api/events/create", headers={
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
            "date": "01.01.2050",
            "time": "21:37",
            "location": "here"
        }

        response_create_event = client.post(f"/api/events/create", headers={
            "Authorization": f"Bearer {token}"
        }, json=payload)

        assert response_create_event.status_code == 200

        event = Event.query.filter_by(name="to delete").first()
        assert event is not None

        #delete event
        response_delete_event = client.delete(f"/api/events/delete/{event.event_id}", headers={
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
            date_and_time=datetime(2050, 1, 1, 21, 37),
            location="here",
            creator_id=friend.user_id #other user
        )
        db.session.add(event)
        db.session.commit()

        # attempt delete
        response_delete_event = client.delete(f"/api/events/delete/{event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        # Changed to 403 Forbidden (more appropriate for permission errors)
        assert response_delete_event.status_code == 403 
        assert response_delete_event.get_json() == {
            "message": "You can delete your own events only"
        }

def test_delete_invalid_event(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

        # attempt delete
        response_delete_event = client.delete(f"/api/events/delete/{uuid.uuid4()}", headers={
            "Authorization": f"Bearer {token}"
        })

        # Changed to 404 Not Found
        assert response_delete_event.status_code == 404
        assert response_delete_event.get_json() == {
            "message": "Event doesn't exist"
        }

def test_create_event_invalid_payload(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user
        
        payload = {
            "name": "e", 
            "description": "valid desc",
            "date": "01.01.2050",
            "time": "21:37",
            "location": "valid loc"
        }

        response = client.post("/api/events/create", headers={"Authorization": f"Bearer {token}"}, json=payload)
        assert response.status_code == 400
        assert response.get_json() == {"message": "Event name must be between 3 and 32 characters"}