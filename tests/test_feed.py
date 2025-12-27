import pytest
from datetime import datetime, timezone, timedelta

# =============================================================================
# Tests for feed
# =============================================================================

@pytest.fixture
def create_events(client,logged_in_user):
    # cerate 21 events for tests
    headers = {"Authorization": f"Bearer {logged_in_user[1]}"}

    event_id=0
    while(event_id!=22):
        event_id+=1
        event_time = datetime.now(timezone.utc) + timedelta(days=event_id)
        payload = {"name": str(event_id)+"ssss", "description": "Lore ipsum", "date": event_time.strftime("%d.%m.%Y"), "time":event_time.strftime("%H:%M"), "location":"Poland"}
        response=client.post("api/events/create", json=payload,headers=headers)
        assert response.status_code == 200

def test_feed_returns_events(client, create_events, app):
    with app.app_context():
        response = client.get("api/events/feed")

        assert response.status_code == 200

        data = response.get_json()
        assert "data" in data
        assert "pagination" in data

        events = data["data"]
        pagination = data["pagination"]

        assert isinstance(events, list)

        assert pagination["page"] == 1
        assert pagination["limit"] == 20
        assert pagination["total"] == 22
        assert pagination["pages"] == 2  # bo wszystkich eventów > limit
        assert events[0]["name"] == "1ssss"

def test_feed_pagination(client, create_events, app):
    with app.app_context():
        response = client.get("api/events/feed?page=1&limit=2")
        assert response.status_code == 200

        data = response.get_json()
        assert "data" in data
        assert "pagination" in data

        events = data["data"]
        pagination = data["pagination"]

        assert len(events) == 2  # limit = 2
        assert pagination["page"] == 1
        assert pagination["limit"] == 2
        assert pagination["total"] == 22
        assert pagination["pages"] == 11

def test_feed_empty(client, app):
    with app.app_context():
        response = client.get("/api/events/feed")
        assert response.status_code == 200

        data = response.get_json()
        assert data["data"] == []
        assert data["pagination"]["total"] == 0
        assert data["pagination"]["pages"] == 0