import pytest
from re import search
from backend.extensions import mail ,db 
from backend.models import User

# =============================================================================
# Tests for feed
# =============================================================================




def test_feed_returns_events(client,create_events):
    response = client.get("/feed")

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
"""
    # sprawdzenie czy eventy są posortowane rosnąco po dacie
    dates = [
        datetime.strptime(e["date"] + " " + e["time"], "%d.%m.%Y %H:%M")
        for e in events
    ]
    assert dates == sorted(dates)
"""
"""

def test_feed_pagination(client, access_token, sample_events):
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.get("/feed?page=1&limit=2", headers=headers)
    assert response.status_code == 200

    data = response.get_json()
    assert "data" in data
    assert "pagination" in data

    events = data["data"]
    pagination = data["pagination"]

    assert len(events) == 2  # limit = 2
    assert pagination["page"] == 1
    assert pagination["limit"] == 2
    assert pagination["total"] == len(sample_events)
    assert pagination["pages"] == (len(sample_events) + 1) // 2  # zaokrąglenie w górę




def test_feed_empty(client, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.get("/feed", headers=headers)
    assert response.status_code == 200

    data = response.get_json()
    assert data["data"] == []
    assert data["pagination"]["total"] == 0
    assert data["pagination"]["pages"] == 0
"""
