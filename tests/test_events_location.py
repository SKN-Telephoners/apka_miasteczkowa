import pytest
from backend.models.event import Location, Event
from backend.models import Friendship
from backend.extensions import db
from datetime import datetime, timezone, timedelta

@pytest.fixture
def sample_location(app):
    with app.app_context():
        loc = Location(
            location_name="Krakow_Rynek",
            coordinates="50.0614,19.9365"
        )
        db.session.add(loc)
        db.session.commit()

        return {"name": loc.location_name, "coords": loc.coordinates}
    
def test_get_coordinates_success(client, logged_in_user, sample_location, app):
    token = logged_in_user[1]
    loc_name = sample_location["name"] 
    
    response = client.get(
        f"/api/events/get_coordinates?location={loc_name}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert response.get_json()["coordinates"] == sample_location["coords"]

def test_get_coordinates_not_found(client, logged_in_user, app):
    """Test przypadku, gdy lokalizacja nie istnieje."""
    token = logged_in_user[1]
    response = client.get(
        "/api/events/get_coordinates?location=NieIstnieje",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
    assert "Location of that name not found" in response.get_json()["message"]

def test_get_coordinates_empty_input(client, logged_in_user):
    """Test błędu przy pustym parametrze."""
    token = logged_in_user[1]
    response = client.get(
        "/api/events/get_coordinates?location=",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "must not be empty" in response.get_json()["message"]

def test_get_coordinates_too_long(client, logged_in_user):
    """Test błędu przy zbyt długiej nazwie (przekroczenie MAX_LOCATION_LEN)."""
    token = logged_in_user[1]
    long_name = "a" * 33 # Zakładając MAX_LOCATION_LEN = 32
    response = client.get(
        f"/api/events/get_coordinates?location={long_name}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "too long" in response.get_json()["message"]

def test_map_radius_filtering(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user
        now = datetime.now(timezone.utc) + timedelta(hours=1)

        e_near = Event(
            event_name="Near Event", 
            location="[19.9370, 50.0615]", # [lng, lat]
            creator_id=user.user_id, 
            date_and_time=now
        )

        e_far = Event(
            event_name="Far Event", 
            location="[21.0122, 52.2297]", 
            creator_id=user.user_id, 
            date_and_time=now
        )
        db.session.add_all([e_near, e_far])
        db.session.commit()

        headers = {"Authorization": f"Bearer {token}"}

        url = "/api/events/map?lat=50.0614&lng=19.9365&radius=5000"
        response = client.get(url, headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()["data"]
        names = [e["name"] for e in data]
        
        assert "Near Event" in names
        assert "Far Event" not in names
        assert len(data) == 1

def test_map_radius_no_location_provided(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user
        future_date = datetime.now(timezone.utc) + timedelta(days=1)
        
        e = Event(
            event_name="Anywhere", 
            location="[0.0, 0.0]", 
            creator_id=user.user_id,
            date_and_time=future_date
        )
        db.session.add(e)
        db.session.commit()

        response = client.get("/api/events/map", headers={"Authorization": f"Bearer {token}"})
        
        assert response.status_code == 200
        assert len(response.get_json()["data"]) >= 1

def test_map_social_filters(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend, _ = registered_friend
        future_date = datetime.now(timezone.utc) + timedelta(days=1)

        u_id, f_id = sorted([user.user_id, friend.user_id])
        db.session.add(Friendship(user_id=u_id, friend_id=f_id))

        e_friend = Event(
            event_name="Friend Event", 
            location="[10,10]", 
            creator_id=friend.user_id,
            date_and_time=future_date
        )
        db.session.add(e_friend)
        db.session.commit()

        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/events/map?friends_only=true", headers=headers)
        
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "Friend Event"
        assert data[0]["creator_username"] == friend.username