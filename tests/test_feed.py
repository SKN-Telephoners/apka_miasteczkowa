import pytest
from re import search
from backend.extensions import mail ,db 
from backend.models import User

# =============================================================================
# Tests for feed
# =============================================================================

def test_feed_returns_events(client, create_events):
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
    assert pagination["pages"] == 2  
    assert events[0]["name"] == "1ssss"


def test_feed_pagination(client, create_events):

    response = client.get("/feed?page=1&limit=2")
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

def test_feed_empty(client):

    response = client.get("/feed")
    assert response.status_code == 200

    data = response.get_json()
    assert data["data"] == []
    assert data["pagination"]["total"] == 0
    assert data["pagination"]["pages"] == 0