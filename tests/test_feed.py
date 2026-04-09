import pytest
from datetime import datetime, timezone, timedelta

from backend.helpers import add_token_to_db
from flask_jwt_extended import create_access_token

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
        payload = {"name": str(event_id)+"ssss", "description": "Lore ipsum", "date": event_time.strftime("%d.%m.%Y"), "time":event_time.strftime("%H:%M"), "location":"Poland", "is_private": False}
        response=client.post("api/events/create", json=payload,headers=headers)
        assert response.status_code == 201

def test_feed_returns_events(client, create_events, app, logged_in_user):
    with app.app_context():
        token = logged_in_user[1]
        response = client.get("api/events/feed", headers={
            "Authorization": f"Bearer {token}"
        })

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

def test_feed_pagination(client, logged_in_user, create_events, app):
    with app.app_context():
        token = logged_in_user[1]
        response = client.get("api/events/feed?page=1&limit=2", headers={
            "Authorization": f"Bearer {token}"
        })
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

def test_feed_empty(client, logged_in_user, app):
    with app.app_context():
        token = logged_in_user[1]
        response = client.get("/api/events/feed", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200

        data = response.get_json()
        assert data["data"] == []
        assert data["pagination"]["total"] == 0
        assert data["pagination"]["pages"] == 0


def test_feed_participation_filter(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend = registered_friend[0]

        joined_time = datetime.now(timezone.utc) + timedelta(days=1)
        joined_payload = {
            "name": "joined-event",
            "description": "joined",
            "date": joined_time.strftime("%d.%m.%Y"),
            "time": joined_time.strftime("%H:%M"),
            "location": "Campus",
            "is_private": False,
        }
        response = client.post("/api/events/create", json=joined_payload, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 201

        friend_access_token = create_access_token(identity=friend.user_id)
        add_token_to_db(friend_access_token)

        not_joined_time = datetime.now(timezone.utc) + timedelta(days=2)
        not_joined_payload = {
            "name": "not-joined-event",
            "description": "not joined",
            "date": not_joined_time.strftime("%d.%m.%Y"),
            "time": not_joined_time.strftime("%H:%M"),
            "location": "Campus",
            "is_private": False,
        }
        response = client.post(
            "/api/events/create",
            json=not_joined_payload,
            headers={"Authorization": f"Bearer {friend_access_token}"},
        )
        assert response.status_code == 201

        joined_response = client.get(
            "/api/events/feed?participation=joined",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert joined_response.status_code == 200
        joined_events = joined_response.get_json()["data"]
        assert any(event["name"] == "joined-event" for event in joined_events)
        assert all(event["is_participating"] is True for event in joined_events)

        not_joined_response = client.get(
            "/api/events/feed?participation=not_joined",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert not_joined_response.status_code == 200
        not_joined_events = not_joined_response.get_json()["data"]
        assert any(event["name"] == "not-joined-event" for event in not_joined_events)
        assert all(event["is_participating"] is False for event in not_joined_events)
