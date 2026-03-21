import pytest
from backend.extensions import db
from backend.models import Event, EventImage
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import uuid
import base64

local_tz = ZoneInfo("Europe/Warsaw")
TINY_JPG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxISEhUTEhIVFRUVFRUVFRUVFRUVFRUWFxUVFRUYHSggGBolHRUVITEhJSkrLi4uFx8zODMtNygtLisBCgoKDg0OFRAQFS0dHR0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLf/AABEIAAEAAQMBIgACEQEDEQH/xAAV"
    "AAEBAAAAAAAAAAAAAAAAAAAABf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAMAwEAAhADEAAAAJ8f/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABBQL/xAAVEQEBAAAAAAAAAAAAAAAAAAABAP/aAAgBAwEBPwF//8QAFBEBAAAAAAAAAAAAAAAAAAAAEP/aAAgBAgEBPwF//8QAFBABAAAAAAAA"
    "AAAAAAAAAAAAAP/aAAgBAQAGPwJ//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPyF//9k="
)

local_tz = ZoneInfo("Europe/Warsaw")

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

        assert response_create_event.status_code == 201
        data = response_create_event.get_json()
        assert data["message"] == "Event created successfully"
        assert "event_id" in data 

def test_create_event_with_images(client, logged_in_user, app):
    user, user_token = logged_in_user
    future_date = datetime.now() + timedelta(days=30)
    date_str = future_date.strftime("%d.%m.%Y")
    time_str = "18:00"

    payload = {
        "name": "event1",
        "description": "very cool event",
        "date": date_str,
        "time": time_str,
        "location": "here",
        "images": [
            {
                "image_url": "https://res.cloudinary.com/demo/image/upload/v1234/fest1.jpg",
                "public_id": "aplikacja_miasteczkowa/fest1"
            },
            {
                "image_url": "https://res.cloudinary.com/demo/image/upload/v1234/fest2.jpg",
                "public_id": "aplikacja_miasteczkowa/fest2"
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json"
    }
    
    response = client.post("/api/events/create", json=payload, headers=headers)

    assert response.status_code == 201
    response_data = response.get_json()
    assert "event_id" in response_data

    event_id = response_data["event_id"]

    with app.app_context():
        created_event = Event.query.filter_by(event_id=event_id).first()
        assert created_event is not None
        assert created_event.name == "event1"

        linked_images = EventImage.query.filter_by(event_id=event_id).all()
        assert len(linked_images) == 2
        
        public_ids = [img.public_id for img in linked_images]
        assert "aplikacja_miasteczkowa/fest1" in public_ids
        assert "aplikacja_miasteczkowa/fest2" in public_ids

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
        assert response_create_event.get_json()["message"] == "Event date must be in the future"

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

        assert response_create_event.status_code == 201

        event = Event.query.filter_by(name="to delete").first()
        assert event is not None

        #delete event
        response_delete_event = client.delete(f"/api/events/delete/{event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_delete_event.status_code == 200
        assert response_delete_event.get_json()["message"] == "Event deleted successfully"

        deleted = Event.query.filter_by(event_id=event.event_id).first()
        assert deleted is None

def test_delete_event_not_owner(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend = registered_friend[0]

        event = Event(
            name="event1",
            description="private",
            date_and_time=datetime(2027, 1, 1, 21, 37),
            location="here",
            creator_id=friend.user_id #other user
        )
        db.session.add(event)
        db.session.commit()

        # attempt delete
        response_delete_event = client.delete(f"/api/events/delete/{event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_delete_event.status_code == 403 
        assert response_delete_event.get_json()["message"] == "You can delete your own events only"

def test_delete_invalid_event(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

        # attempt delete
        response_delete_event = client.delete(f"/api/events/delete/{uuid.uuid4()}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_delete_event.status_code == 404
        assert response_delete_event.get_json()["message"] == "Event doesn't exist"

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
        assert response.get_json()["message"] == "Event name must be between 3 and 32 characters"
        

def test_edit_event(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

        #create event
        payload = {
            "name": "to edit",
            "description": "very cool event",
            "date": "01.01.2050",
            "time": "21:37",
            "location": "here"
        }

        response_create_event = client.post(f"/api/events/create", headers={
            "Authorization": f"Bearer {token}"
        }, json=payload)

        assert response_create_event.status_code == 201

        event = Event.query.filter_by(name="to edit").first()
        assert event is not None
        assert event.edited == False

        new_payload = {
            "name": "edited",
            "description": None,
            "date": "20.01.2050",
            "time": "22:37",
            "location": None
        }

        #edit event
        response_edit_event = client.put(f"/api/events/edit/{event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        }, json=new_payload)

        assert response_edit_event.status_code == 200
        assert response_edit_event.get_json() == {
            "message": "Event edited successfully"
        }
        
        edited_event = Event.query.filter_by(event_id=event.event_id).first()
        assert edited_event.name == "edited"
        assert edited_event.description == "very cool event"
        assert edited_event.date_and_time == datetime(2050, 1, 20, 22, 37, tzinfo=local_tz)
        assert edited_event.location == "here"
        assert edited_event.edited == True

def test_edit_event_not_exist(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

        new_payload = {
            "name": "edited",
            "description": None,
            "date": "20.01.2050",
            "time": "22:37",
            "location": None
        }

        response_edit_event = client.put(f"/api/events/edit/{uuid.uuid4()}", headers={
            "Authorization": f"Bearer {token}"
        }, json=new_payload)

        assert response_edit_event.status_code == 404
        assert response_edit_event.get_json() == {
            "message": "Event doesn't exist"
        }

def test_edit_event_not_owner(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend = registered_friend[0]

        event = Event(
            name="event1",
            description="private",
            date_and_time=datetime(2050, 1, 20, 21, 37, tzinfo=timezone.utc),
            location="here",
            creator_id=friend.user_id #other user
        )
        db.session.add(event)
        db.session.commit()

        # attempt edit
        response_delete_event = client.put(f"/api/events/edit/{event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_delete_event.status_code == 403 
        assert response_delete_event.get_json() == {
            "message": "You can edit your own events only"
        }
