import pytest
from backend.extensions import db
from backend.models import Event
from backend.models.event import Event_visibility
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import uuid
from datetime import datetime, timedelta, timezone

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
            "location": "here",
            "is_private": False
        }

        response_create_event = client.post(f"/api/events/create", headers={
            "Authorization": f"Bearer {token}"
        }, json=payload)

        assert response_create_event.status_code == 201
        data = response_create_event.get_json()
        assert data["message"] == "Event created successfully"
        assert "event_id" in data 

def test_create_event_invalid_date(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

        #create event
        payload = {
            "name": "event1",
            "description": "very cool event",
            "date": "01.01.1995",
            "time": "21:37",
            "location": "here",
            "is_private": False
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
            "location": "here",
            "is_private": False
        }

        response_create_event = client.post(f"/api/events/create", headers={
            "Authorization": f"Bearer {token}"
        }, json=payload)

        assert response_create_event.status_code == 201

        event = Event.query.filter_by(event_name="to delete").first()
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
            event_name="event1",
            description="private",
            date_and_time=datetime(2027, 1, 1, 21, 37),
            location="here",
            creator_id=friend.user_id, #other user
            is_private=False
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
            "location": "valid loc",
            "is_private": False
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
            "location": "here",
            "is_private": False
        }

        response_create_event = client.post(f"/api/events/create", headers={
            "Authorization": f"Bearer {token}"
        }, json=payload)

        assert response_create_event.status_code == 201

        event = Event.query.filter_by(event_name="to edit").first()
        assert event is not None
        assert event.is_edited == False

        new_payload = {
            "name": "edited",
            "description": None,
            "date": "20.01.2050",
            "time": "22:37",
            "location": None,
            "is_private": False
        }

        #edit event
        response_edit_event = client.put(f"/api/events/edit/{event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        }, json=new_payload)

        assert response_edit_event.status_code == 200
        assert response_edit_event.get_json() == {
            "message": "Event edited successfully"
        }

        db.session.expire_all()

        edited_event = Event.query.filter_by(event_id=event.event_id).first()
        assert edited_event.event_name == "edited"
        assert edited_event.description == "very cool event"
        assert edited_event.date_and_time == datetime(2050, 1, 20, 22, 37, tzinfo=local_tz)
        assert edited_event.location == "here"
        assert edited_event.is_edited == True

def test_edit_event_not_exist(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

        new_payload = {
            "name": "edited",
            "description": None,
            "date": "20.01.2050",
            "time": "22:37",
            "location": None,
            "is_private": False
        }

        response_edit_event = client.put(f"/api/events/edit/{uuid.uuid4()}", headers={
            "Authorization": f"Bearer {token}"
        }, json=new_payload)

        assert response_edit_event.status_code == 404
        assert response_edit_event.get_json() == {
            "message": "This event does not exist"
        }

def test_edit_event_not_owner(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend = registered_friend[0]

        event = Event(
            event_name="event1",
            description="private",
            date_and_time=datetime(2050, 1, 20, 21, 37, tzinfo=timezone.utc),
            location="here",
            creator_id=friend.user_id, #other user
            is_private=False
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

def test_feed_pagination(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user
        # Tworzymy 25 eventów
        for i in range(25):
            ev = Event(event_name=f"E{i}", location="X", creator_id=user.user_id, is_private=False)
            db.session.add(ev)
        db.session.commit()

        # Pierwsza strona, limit 10
        response = client.get("/api/events/feed?page=1&limit=10", headers={"Authorization": f"Bearer {token}"})
        data = response.get_json()
        assert len(data["data"]) == 10
        assert data["pagination"]["total"] == 25
        assert data["pagination"]["pages"] == 3

def test_feed_sorting_and_visibility(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend, _ = registered_friend
        
        # 1. Event publiczny - jutro
        ev1 = Event(event_name="Public Future", location="X", creator_id=friend.user_id, 
                    is_private=False, date_and_time=datetime.now(timezone.utc) + timedelta(days=1))
        # 2. Event publiczny - pojutrze
        ev2 = Event(event_name="Public Later", location="X", creator_id=friend.user_id, 
                    is_private=False, date_and_time=datetime.now(timezone.utc) + timedelta(days=2))
        # 3. Event prywatny (nieudostępniony)
        ev3 = Event(event_name="Private Hidden", location="X", creator_id=friend.user_id, 
                    is_private=True, date_and_time=datetime.now(timezone.utc) + timedelta(days=1))
        
        db.session.add_all([ev1, ev2, ev3])
        db.session.commit()

        response = client.get("/api/events/feed", headers={"Authorization": f"Bearer {token}"})
        data = response.get_json()["data"]
        assert len(data) == 2

        assert data[0]["name"] == "Public Future"

        response_desc = client.get("/api/events/feed?sort=2", headers={"Authorization": f"Bearer {token}"})
        data_desc = response_desc.get_json()["data"]
        assert data_desc[0]["name"] == "Public Later"

def test_private_event_visibility_denied(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user # Użytkownik A
        friend, _ = registered_friend # Użytkownik B

        ev = Event(event_name="Secret", location="X", creator_id=friend.user_id, is_private=True)
        db.session.add(ev)
        db.session.commit()

        # Użytkownik A nie powinien go widzieć w feedzie
        response = client.get("/api/events/feed", headers={"Authorization": f"Bearer {token}"})
        data = response.get_json()["data"]
        ids = [e["id"] for e in data]
        assert str(ev.event_id) not in ids

def test_private_event_shared_access(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend, _ = registered_friend
        ev = Event(event_name="Shared Secret", location="X", creator_id=friend.user_id, is_private=True)
        db.session.add(ev)
        db.session.flush()
        
        vis = Event_visibility(event_id=ev.event_id, sharing=friend.user_id, shared_with=user.user_id)
        db.session.add(vis)
        db.session.commit()

        # Teraz Użytkownik A powinien go widzieć
        response = client.get("/api/events/feed", headers={"Authorization": f"Bearer {token}"})
        names = [e["name"] for e in response.get_json()["data"]]
        assert "Shared Secret" in names
