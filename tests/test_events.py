import pytest
from backend.extensions import db
from datetime import datetime, timezone, timedelta
import uuid
import base64
from backend.models import Event, User
from backend.models.event import Event_visibility, Pictures
from zoneinfo import ZoneInfo
from unittest.mock import patch

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

def test_edit_event_switch_private_to_public_clears_visibility(client, logged_in_user, registered_friend, app):
    user, token = logged_in_user
    friend, _ = registered_friend

    with app.app_context():
        ev = Event(event_name="Private Event", location="X", creator_id=user.user_id, is_private=True)
        db.session.add(ev)
        db.session.flush()
        
        vis = Event_visibility(event_id=ev.event_id, sharing=user.user_id, shared_with=friend.user_id)
        db.session.add(vis)
        db.session.commit()
        event_id = ev.event_id

    payload = {"is_private": False}
    response = client.put(f"/api/events/edit/{event_id}", headers={"Authorization": f"Bearer {token}"}, json=payload)
    
    assert response.status_code == 200
    
    with app.app_context():
        vis_count = Event_visibility.query.filter_by(event_id=event_id).count()
        assert vis_count == 0
        updated_ev = db.session.get(Event, event_id)
        assert updated_ev.is_private is False

def test_edit_event_manage_shared_list(client, logged_in_user, registered_friend, app):
    user, token = logged_in_user
    friend, _ = registered_friend
 
    with app.app_context():
        friend2 = User(username="friend2", email="f2@test.pl", password="Password123!")
        db.session.add(friend2)
        db.session.commit()
        f2_id = str(friend2.user_id)

    payload_create = {
        "name": "Secret Party",
        "description": "...",
        "date": "01.01.2050",
        "time": "20:00",
        "location": "Secret",
        "is_private": True,
        "shared_list": [str(friend.user_id)]
    }
    res_create = client.post("/api/events/create", headers={"Authorization": f"Bearer {token}"}, json=payload_create)
    event_id = res_create.get_json()["event_id"]

    payload_edit = {
        "shared_list": [f2_id]
    }
    res_edit = client.put(f"/api/events/edit/{event_id}", headers={"Authorization": f"Bearer {token}"}, json=payload_edit)
    assert res_edit.status_code == 200

    with app.app_context():
        visible_to = Event_visibility.query.filter_by(event_id=event_id).all()
        shared_ids = [str(v.shared_with) for v in visible_to]
        
        assert f2_id in shared_ids
        assert str(friend.user_id) not in shared_ids
        assert len(shared_ids) == 1

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


# =============================================================================
# Tests for handling events' pictures lifecycle
# =============================================================================
def test_create_event_with_pictures(client, logged_in_user, app):
    _, user_token = logged_in_user
    future_date = datetime.now() + timedelta(days=30)
    date_str = future_date.strftime("%d.%m.%Y")
    time_str = "18:00"

    payload = {
        "name": "event1",
        "description": "very cool event",
        "date": date_str,
        "time": time_str,
        "location": "here",
        "is_private": False, # <--- Add this line!
        "pictures": [
            {
                "cloud_id": "aplikacja_miasteczkowa/fest1"
            },
            {
                "cloud_id": "aplikacja_miasteczkowa/fest2"
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
        assert created_event.event_name == "event1"

        linked_pictures = Pictures.query.filter_by(event_id=event_id).all()
        assert len(linked_pictures) == 2
        
        cloud_ids = [pic.cloud_id for pic in linked_pictures]
        assert "aplikacja_miasteczkowa/fest1" in cloud_ids
        assert "aplikacja_miasteczkowa/fest2" in cloud_ids

@patch('cloudinary.uploader.destroy')
def test_edit_event_pictures(mock_destroy, client, logged_in_user, app):
    _, user_token = logged_in_user
    future_date = datetime.now() + timedelta(days=30)
    
    create_payload = {
        "name": "Image Edit Event",
        "description": "Testing image edits",
        "date": future_date.strftime("%d.%m.%Y"),
        "time": "18:00",
        "location": "here",
        "is_private": False,
        "pictures": [
            {"cloud_id": "pic_A"},
            {"cloud_id": "pic_B"}
        ]
    }
    headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}
    
    response = client.post("/api/events/create", json=create_payload, headers=headers)
    assert response.status_code == 201
    event_id = response.get_json()["event_id"]

    edit_payload = {
        "pictures": [
            {"cloud_id": "pic_B"}, 
            {"cloud_id": "pic_C"}
        ]
    }
    
    edit_response = client.put(f"/api/events/edit/{event_id}", json=edit_payload, headers=headers)
    assert edit_response.status_code == 200

    with app.app_context():
        linked_pictures = Pictures.query.filter_by(event_id=event_id).all()
        cloud_ids = [pic.cloud_id for pic in linked_pictures]

        assert len(cloud_ids) == 2
        assert "pic_B" in cloud_ids
        assert "pic_C" in cloud_ids
        assert "pic_A" not in cloud_ids
        
        # check if cloudinary was instructed to delete pic_A
        mock_destroy.assert_called_once_with("pic_A")


@patch('cloudinary.uploader.destroy')
def test_delete_event_with_pictures(mock_destroy, client, logged_in_user, app):
    _, user_token = logged_in_user
    future_date = datetime.now() + timedelta(days=30)
    
    create_payload = {
        "name": "Delete Event With Pics",
        "description": "Will be deleted",
        "date": future_date.strftime("%d.%m.%Y"),
        "time": "12:00",
        "location": "nowhere",
        "is_private": False,
        "pictures": [
            {"cloud_id": "pic_to_delete_1"},
            {"cloud_id": "pic_to_delete_2"}
        ]
    }
    headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}
    
    response = client.post("/api/events/create", json=create_payload, headers=headers)
    assert response.status_code == 201
    event_id = response.get_json()["event_id"]

    delete_response = client.delete(f"/api/events/delete/{event_id}", headers=headers)
    assert delete_response.status_code == 200

    assert mock_destroy.call_count == 2
    
    mock_destroy.assert_any_call("pic_to_delete_1")
    mock_destroy.assert_any_call("pic_to_delete_2")

    with app.app_context():
        event = Event.query.filter_by(event_id=event_id).first()
        assert event is None
        
        pictures = Pictures.query.filter_by(event_id=event_id).all()
        assert len(pictures) == 0


def test_feed_returns_pictures(client, logged_in_user, app):
    _, user_token = logged_in_user
    future_date = datetime.now() + timedelta(days=30)
    
    create_payload = {
        "name": "Feed Picture Event",
        "description": "Testing the feed",
        "date": future_date.strftime("%d.%m.%Y"),
        "time": "15:00",
        "location": "here",
        "is_private": False,
        "pictures": [
            {"cloud_id": "feed_pic_1"}
        ]
    }
    headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}
    
    response = client.post("/api/events/create", json=create_payload, headers=headers)
    assert response.status_code == 201

    feed_response = client.get("/api/events/feed", headers=headers)
    assert feed_response.status_code == 200
    
    data = feed_response.get_json()["data"]

    feed_event = next((e for e in data if e["name"] == "Feed Picture Event"), None)
    assert feed_event is not None

    assert "pictures" in feed_event
    assert len(feed_event["pictures"]) == 1
    assert feed_event["pictures"][0]["cloud_id"] == "feed_pic_1"
    assert "url" in feed_event["pictures"][0]

def test_edit_event_pictures_duplicates_in_payload(client, logged_in_user, app):
    user, token = logged_in_user
    
    with app.app_context():
        ev = Event(event_name="Duplicate Test", location="X", creator_id=user.user_id)
        db.session.add(ev)
        db.session.commit()
        event_id = str(ev.event_id)

    payload = {
        "pictures": [
            {"cloud_id": "pic1"},
            {"cloud_id": "pic1"}
        ]
    }
    res = client.put(f"/api/events/edit/{event_id}", headers={"Authorization": f"Bearer {token}"}, json=payload)
    assert res.status_code == 200
    
    with app.app_context():
        pics = Pictures.query.filter_by(event_id=event_id).all()
        assert len(pics) == 1

def test_edit_event_pictures_limit_logic(client, logged_in_user, app):
    user, token = logged_in_user
    
    with app.app_context():
        ev = Event(event_name="Pic Test", location="X", creator_id=user.user_id, is_private=False)
        db.session.add(ev)
        db.session.flush()
        p1 = Pictures(cloud_id="pic1", event_id=ev.event_id)
        p2 = Pictures(cloud_id="pic2", event_id=ev.event_id)
        p3 = Pictures(cloud_id="pic3", event_id=ev.event_id)
        db.session.add_all([p1, p2, p3])
        db.session.commit()
        event_id = str(ev.event_id)

    payload_ok = {
        "pictures": [
            {"cloud_id": "pic1"},
            {"cloud_id": "pic2"},
            {"cloud_id": "pic4"},
            {"cloud_id": "pic5"},
            {"cloud_id": "pic6"}
        ]
    }
    res_ok = client.put(f"/api/events/edit/{event_id}", headers={"Authorization": f"Bearer {token}"}, json=payload_ok)
    assert res_ok.status_code == 200

    payload_fail = {
        "pictures": [
            {"cloud_id": "pic1"},
            {"cloud_id": "pic2"},
            {"cloud_id": "pic7"},
            {"cloud_id": "pic8"},
            {"cloud_id": "pic9"},
            {"cloud_id": "pic10"}
        ]
    }
    res_fail = client.put(f"/api/events/edit/{event_id}", headers={"Authorization": f"Bearer {token}"}, json=payload_fail)
    assert res_fail.status_code == 400
    assert "Limit of pictures exceeded" in res_fail.get_json()["message"]

def test_create_event_with_coordinate_location(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

        payload = {
            "name": "event coords",
            "description": "very cool event",
            "date": "01.01.2050",
            "time": "21:37",
            "location": "[19.9061, 50.0686]",
            "is_private": False,
        }

        response_create_event = client.post(
            "/api/events/create",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )

        assert response_create_event.status_code == 201
        event = Event.query.filter_by(event_name="event coords").first()
        assert event is not None
        assert event.location == "[19.906100,50.068600]"
def test_edit_event_with_coordinate_location(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

        payload = {
            "name": "to edit coords",
            "description": "very cool event",
            "date": "01.01.2050",
            "time": "21:37",
            "location": "here",
            "is_private": False,
        }

        response_create_event = client.post(
            "/api/events/create",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
        assert response_create_event.status_code == 201

        event = Event.query.filter_by(event_name="to edit coords").first()
        assert event is not None

        response_edit_event = client.put(
            f"/api/events/edit/{event.event_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"location": [19.9061, 50.0686]},
        )

        assert response_edit_event.status_code == 200
        db.session.expire_all()
        edited_event = Event.query.filter_by(event_id=event.event_id).first()
        assert edited_event is not None
        assert edited_event.location == "[19.906100,50.068600]"
        
def test_map_events_returns_only_future_events(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

        past_event_id = uuid.uuid4()
        db.session.execute(
            db.insert(Event).values(
                event_id=past_event_id,
                event_name="past map event",
                description="old",
                date_and_time=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
                location="[19.900000,50.060000]",
                creator_id=user.user_id,
                is_private=False,
                comment_count=0,
                participant_count=0
            )
        )
        future_event = Event(
            event_name="future map event",
            description="new",
            date_and_time=datetime(2050, 1, 1, 12, 0, tzinfo=timezone.utc),
            location="[19.910000,50.070000]",
            creator_id=user.user_id,
            is_private=False,
        )
        db.session.add_all([future_event])
        db.session.commit()

        response = client.get(
            "/api/events/map",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()["data"]
        returned_names = {event["name"] for event in data}
        assert "future map event" in returned_names
        assert "past map event" not in returned_names
        assert all(event.get("location_coordinates") for event in data)