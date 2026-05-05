import pytest
from datetime import datetime, timezone, timedelta
from backend.models.event import Event_participants, Event_visibility
from backend.models import Event
from backend.extensions import db

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
#helper
def get_auth_header(token):
    return {"Authorization": f"Bearer {token}"}

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

        ev1 = Event(event_name="Mecz Wisły", location="X", creator_id=friend.user_id, 
                    is_private=False, 
                    date_and_time=datetime.now(timezone.utc) + timedelta(days=1),
                    participant_count=5)

        ev2 = Event(event_name="Czwartek w studio", location="X", creator_id=friend.user_id, 
                    is_private=False, 
                    date_and_time=datetime.now(timezone.utc) + timedelta(days=2),
                    participant_count=10)

        ev3 = Event(event_name="SUPER PRYWATNY EVENT", location="X", creator_id=friend.user_id, 
                    is_private=True, 
                    date_and_time=datetime.now(timezone.utc) + timedelta(days=1))
        
        db.session.add_all([ev1, ev2, ev3])
        db.session.commit()

        response = client.get("/api/events/feed", headers={"Authorization": f"Bearer {token}"})
        data = response.get_json()["data"]
        assert len(data) == 2
        assert data[0]["name"] == "Mecz Wisły" 

        response_desc = client.get("/api/events/feed?sort_mode=members_desc", headers={"Authorization": f"Bearer {token}"})
        data_desc = response_desc.get_json()["data"]

        assert data_desc[0]["name"] == "Czwartek w studio"
        assert data_desc[1]["name"] == "Mecz Wisły"

def test_private_event_visibility_denied(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user 
        friend, _ = registered_friend 

        ev = Event(event_name="SEKRETNY **UKRYTY** EVENT", location="X", creator_id=friend.user_id, is_private=True)
        db.session.add(ev)
        db.session.commit()

        response = client.get("/api/events/feed", headers={"Authorization": f"Bearer {token}"})
        data = response.get_json()["data"]
        ids = [e["id"] for e in data]
        assert str(ev.event_id) not in ids


def test_private_event_shared_access(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend, _ = registered_friend
        ev = Event(event_name="Ukryty ALE udostępniony", location="X", creator_id=friend.user_id, is_private=True)
        db.session.add(ev)
        db.session.flush()
        
        vis = Event_visibility(event_id=ev.event_id, sharing=friend.user_id, shared_with=user.user_id)
        db.session.add(vis)
        db.session.commit()

        response = client.get("/api/events/feed", headers={"Authorization": f"Bearer {token}"})
        names = [e["name"] for e in response.get_json()["data"]]
        assert "Ukryty ALE udostępniony" in names

def test_feed_search_query(client, logged_in_user, app):
    #test wyszukiwania po nazwie i opisie (parametr q)
    with app.app_context():
        user, token = logged_in_user

        e1 = Event(event_name="Mecz Wisły", description="Szykuj się na wpierdol", 
                   location="Stadion", creator_id=user.user_id, is_private=False)
        e2 = Event(event_name="grillowanie dziekana", description="będzie ogniście **fire emoji**", 
                   location="AGH", creator_id=user.user_id, is_private=False)
        db.session.add_all([e1, e2])
        db.session.commit()

        response = client.get("/api/events/feed?q=Mecz", headers=get_auth_header(token))
        data = response.get_json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "Mecz Wisły"

        response = client.get("/api/events/feed?q=fire", headers=get_auth_header(token))
        data = response.get_json()["data"]
        assert len(data) == 1
        assert "grill" in data[0]["name"]

def test_feed_visibility_logic(client, logged_in_user, registered_friend, app):
    #test czy użytkownik widzi tylko to, co powinien (Publiczne + Swoje Prywatne + Udostępnione)
    with app.app_context():
        user_a, token_a = logged_in_user
        user_b, _ = registered_friend 

        ev_public = Event(event_name="Public B", location="X", creator_id=user_b.user_id, is_private=False)
        ev_private_hidden = Event(event_name="Private Hidden", location="X", creator_id=user_b.user_id, is_private=True)
        ev_private_shared = Event(event_name="Private Shared", location="X", creator_id=user_b.user_id, is_private=True)
        
        db.session.add_all([ev_public, ev_private_hidden, ev_private_shared])
        db.session.flush()

        vis = Event_visibility(event_id=ev_private_shared.event_id, sharing=user_b.user_id, shared_with=user_a.user_id)
        db.session.add(vis)
        db.session.commit()

        response = client.get("/api/events/feed", headers=get_auth_header(token_a))
        events = response.get_json()["data"]
        names = [e["name"] for e in events]

        assert "Public B" in names
        assert "Private Shared" in names
        assert "Private Hidden" not in names
        assert len(events) == 2

def test_feed_participation_filter(client, logged_in_user, app):
    #test filtrowania po statusie dołączenia (participation=joined/not_joined)
    with app.app_context():
        user, token = logged_in_user
        
        e1 = Event(event_name="Joined Event", location="X", creator_id=user.user_id, is_private=False)
        e2 = Event(event_name="Not Joined Event", location="X", creator_id=user.user_id, is_private=False)
        db.session.add_all([e1, e2])
        db.session.flush()

        part = Event_participants(event_id=e1.event_id, user_id=user.user_id)
        db.session.add(part)
        db.session.commit()

        res_joined = client.get("/api/events/feed?participation=joined", headers=get_auth_header(token))
        data_joined = res_joined.get_json()["data"]
        assert len(data_joined) == 1
        assert data_joined[0]["name"] == "Joined Event"

        res_not = client.get("/api/events/feed?participation=not_joined", headers=get_auth_header(token))
        data_not = res_not.get_json()["data"]

        assert any(e["name"] == "Not Joined Event" for e in data_not)

def test_feed_sorting_members(client, logged_in_user, app):
    #Test sortowania po liczbie uczestników (members_desc)
    with app.app_context():
        user, token = logged_in_user

        e_popular = Event(event_name="Popular", location="X", creator_id=user.user_id, participant_count=10)
        e_niche = Event(event_name="Niche", location="X", creator_id=user.user_id, participant_count=2)
        
        db.session.add_all([e_popular, e_niche])
        db.session.commit()

        response = client.get("/api/events/feed?sort_mode=members_desc", headers=get_auth_header(token))
        data = response.get_json()["data"]
        
        assert data[0]["name"] == "Popular"
        assert data[1]["name"] == "Niche"

def test_feed_created_window(client, logged_in_user, app):
    #test filtrowania po dacie utworzenia (created_window)
    with app.app_context():
        user, token = logged_in_user
        
        e_new = Event(event_name="Today", location="X", creator_id=user.user_id)
        e_old = Event(event_name="Old", location="X", creator_id=user.user_id)
        e_old.created_at = datetime.now(timezone.utc) - timedelta(days=730)
        
        db.session.add_all([e_new, e_old])
        db.session.commit()

        res_today = client.get("/api/events/feed?created_window=today", headers=get_auth_header(token))
        assert len(res_today.get_json()["data"]) == 1
        assert res_today.get_json()["data"][0]["name"] == "Today"

        res_older = client.get("/api/events/feed?created_window=older", headers=get_auth_header(token))
        assert len(res_older.get_json()["data"]) == 1
        assert res_older.get_json()["data"][0]["name"] == "Old"

def test_feed_pagination_metadata(client, logged_in_user, app):
    #Test poprawności metadanych paginacji
    with app.app_context():
        user, token = logged_in_user

        for i in range(5):
            db.session.add(Event(event_name=f"E{i}", location="X", creator_id=user.user_id))
        db.session.commit()

        response = client.get("/api/events/feed?page=1&limit=2", headers=get_auth_header(token))
        pagination = response.get_json()["pagination"]
        
        assert pagination["page"] == 1
        assert pagination["limit"] == 2
        assert pagination["total"] == 5
        assert pagination["pages"] == 3
        assert pagination["has_next"] is True