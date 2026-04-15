import pytest
from backend.models.event import Location
from backend.extensions import db

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
