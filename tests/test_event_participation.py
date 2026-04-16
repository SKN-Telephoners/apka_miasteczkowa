import pytest
from backend.extensions import db
from backend.models import Friendship, Event
from backend.models.event import Event_participants, InviteRequestStatus, Invites
from datetime import datetime, timezone

def test_participation_status(client, logged_in_user, event, app):
    with app.app_context():
        user, token = logged_in_user

        response = client.get(f"/api/events/participation/{event.event_id}", 
                              headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.get_json()["is_participating"] is True

def test_join_public_event(client, logged_in_user, registered_friend, app):
    with app.app_context():
        friend, password = registered_friend
        login_res = client.post("/api/auth/login", json={"username": friend.username, "password": password})
        token = login_res.get_json()["access_token"]

        creator = logged_in_user[0]
        ev = Event(event_name="Publiczny", location="X", creator_id=creator.user_id, is_private=False)
        db.session.add(ev)
        db.session.commit()

        response = client.post(f"/api/events/join/{ev.event_id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.get_json()["participant_count"] == 1
        
        participant = Event_participants.query.filter_by(event_id=ev.event_id, user_id=friend.user_id).first()
        assert participant is not None

def test_join_private_event_denied(client, registered_friend, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user # Creator
        friend, f_pass = registered_friend
        
        ev = Event(event_name="Prywatny", location="X", creator_id=user.user_id, is_private=True)
        db.session.add(ev)
        db.session.commit()

        # Login jako friend
        login_res = client.post("/api/auth/login", json={"username": friend.username, "password": f_pass})
        f_token = login_res.get_json()["access_token"]

        response = client.post(f"/api/events/join/{ev.event_id}", headers={"Authorization": f"Bearer {f_token}"})
        assert response.status_code == 403
        assert "private" in response.get_json()["message"]

def test_leave_event(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend, f_pass = registered_friend
        
        ev = Event(event_name="Event", location="X", creator_id=user.user_id, is_private=False)
        db.session.add(ev)
        db.session.flush()
        
        part = Event_participants(event_id=ev.event_id, user_id=friend.user_id)
        ev.participant_count = 1
        db.session.add(part)
        db.session.commit()

        login_res = client.post("/api/auth/login", json={"username": friend.username, "password": f_pass})
        f_token = login_res.get_json()["access_token"]

        response = client.delete(f"/api/events/leave/{ev.event_id}", headers={"Authorization": f"Bearer {f_token}"})
        assert response.status_code == 200
        assert response.get_json()["participant_count"] == 0

def test_leave_private_event(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend, f_pass = registered_friend

        ev = Event(event_name="Private Event", location="X", creator_id=user.user_id, is_private=True)
        db.session.add(ev)
        db.session.flush()

        share = Event_visibility(event_id=ev.event_id, sharing=user.user_id, shared_with=friend.user_id)
        part = Event_participants(event_id=ev.event_id, user_id=friend.user_id)
        ev.participant_count = 1
        db.session.add_all([share, part])
        db.session.commit()

        login_res = client.post("/api/auth/login", json={"username": friend.username, "password": f_pass})
        f_token = login_res.get_json()["access_token"]

        response = client.delete(f"/api/events/leave/{ev.event_id}", headers={"Authorization": f"Bearer {f_token}"})
        assert response.status_code == 200
        assert response.get_json()["participant_count"] == 0
        assert Event_participants.query.filter_by(event_id=ev.event_id, user_id=friend.user_id).first() is None

def test_invite_friend_to_event(client, logged_in_user, registered_friend, event, app):
    with app.app_context():
        user, token = logged_in_user
        friend, _ = registered_friend

        f1 = Friendship(user_id=min(user.user_id, friend.user_id), 
                        friend_id=max(user.user_id, friend.user_id))
        db.session.add(f1)
        db.session.commit()

        payload = {"invited": str(friend.user_id)}
        response = client.post(f"/api/events/invite/{event.event_id}", 
                               headers={"Authorization": f"Bearer {token}"}, 
                               json=payload)
        
        assert response.status_code == 201
        invite = Invites.query.filter_by(event_id=event.event_id, invited_id=friend.user_id).first()
        assert invite is not None
        assert invite.status == InviteRequestStatus.pending

def test_accept_invite_updates_participation(client, logged_in_user, registered_friend, event, app):
    with app.app_context():
        user, token = logged_in_user
        friend, f_pass = registered_friend

        inv = Invites(event_id=event.event_id, inviter_id=user.user_id, 
                      invited_id=friend.user_id, status=InviteRequestStatus.pending)
        db.session.add(inv)
        db.session.commit()

        login_res = client.post("/api/auth/login", json={"username": friend.username, "password": f_pass})
        f_token = login_res.get_json()["access_token"]

        response = client.post(f"/api/events/change_invite_status/{inv.invite_id}", 
                               headers={"Authorization": f"Bearer {f_token}"}, 
                               json={"status": "accepted"})
        
        assert response.status_code == 200

        part = Event_participants.query.filter_by(event_id=event.event_id, user_id=friend.user_id).first()
        assert part is not None

        event = db.session.get(Event, event.event_id)
        assert event.participant_count == 2

def test_invite_non_friend_denied(client, logged_in_user, registered_friend, event, app):
    with app.app_context():
        # Próba zaproszenia kogoś, kto nie jest znajomym
        token = logged_in_user[1]
        friend = registered_friend[0]
        
        payload = {"invited": str(friend.user_id)}
        response = client.post(f"/api/events/invite/{event.event_id}", 
                               headers={"Authorization": f"Bearer {token}"}, json=payload)
        assert response.status_code == 403
        assert "only invite your friends" in response.get_json()["message"]

def test_accept_invite_flow(client, logged_in_user, registered_friend, event, app):
    with app.app_context():
        user, token = logged_in_user
        friend, f_pass = registered_friend
        f = Friendship(user_id=min(user.user_id, friend.user_id), 
                       friend_id=max(user.user_id, friend.user_id))
        db.session.add(f)
        db.session.commit()

        # 2. Zaproś znajomego
        client.post(f"/api/events/invite/{event.event_id}", 
                    headers={"Authorization": f"Bearer {token}"}, 
                    json={"invited": str(friend.user_id)})
        
        invite = Invites.query.filter_by(invited_id=friend.user_id).first()

        login_res = client.post("/api/auth/login", json={"username": friend.username, "password": f_pass})
        f_token = login_res.get_json()["access_token"]
        
        response = client.post(f"/api/events/change_invite_status/{invite.invite_id}", 
                               headers={"Authorization": f"Bearer {f_token}"}, 
                               json={"status": "accepted"})
        
        assert response.status_code == 200
        event = db.session.get(Event, event.event_id)
        assert event.participant_count == 2

def test_invite_already_sent(client, logged_in_user, registered_friend, event, app):
    with app.app_context():
        user, token = logged_in_user
        friend, _ = registered_friend
        f = Friendship(user_id=min(user.user_id, friend.user_id), friend_id=max(user.user_id, friend.user_id))
        db.session.add(f)
        db.session.commit()

        payload = {"invited": str(friend.user_id)}
        
        # Pierwsze zaproszenie
        client.post(f"/api/events/invite/{event.event_id}", headers={"Authorization": f"Bearer {token}"}, json=payload)
        
        # Drugie zaproszenie 
        response = client.post(f"/api/events/invite/{event.event_id}", headers={"Authorization": f"Bearer {token}"}, json=payload)
        
        assert response.status_code == 409
        assert "Invite already sent" in response.get_json()["message"]

def test_delete_invite_success(client, logged_in_user, registered_friend, event, app):
    with app.app_context():
        user, token = logged_in_user
        friend, _ = registered_friend

        f = Friendship(user_id=min(user.user_id, friend.user_id), friend_id=max(user.user_id, friend.user_id))
        db.session.add(f)
        db.session.commit()

        client.post(f"/api/events/invite/{event.event_id}", 
                    headers={"Authorization": f"Bearer {token}"}, 
                    json={"invited": str(friend.user_id)})

        response = client.delete(f"/api/events/delete_invite/{event.event_id}",
                                 headers={"Authorization": f"Bearer {token}"},
                                 json={"invited": str(friend.user_id)})

        assert response.status_code == 200
        assert Invites.query.filter_by(invited_id=friend.user_id).first() is None

def test_invite_already_participant(client, logged_in_user, registered_friend, event, app):
    with app.app_context():
        user, token = logged_in_user
        friend, _ = registered_friend

        p = Event_participants(event_id=event.event_id, user_id=friend.user_id)
        f = Friendship(user_id=min(user.user_id, friend.user_id), friend_id=max(user.user_id, friend.user_id))
        db.session.add_all([p, f])
        db.session.commit()

        payload = {"invited": str(friend.user_id)}
        response = client.post(f"/api/events/invite/{event.event_id}", 
                               headers={"Authorization": f"Bearer {token}"}, 
                               json=payload)
        
        assert response.status_code == 409
        assert "already participating" in response.get_json()["message"]

def test_change_invite_status_not_authorized(client, logged_in_user, registered_friend, event, app):
    with app.app_context():

        user, _ = logged_in_user
        friend, _ = registered_friend

        inv = Invites(event_id=event.event_id, inviter_id=user.user_id, invited_id=friend.user_id)
        db.session.add(inv)
        db.session.commit()

        token = logged_in_user[1]
        response = client.post(f"/api/events/change_invite_status/{inv.invite_id}", 
                               headers={"Authorization": f"Bearer {token}"}, 
                               json={"status": "accepted"})
        
        assert response.status_code == 403
        assert "only change status of the invites meant to you" in response.get_json()["message"]

def test_get_user_events_creator(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

        event_created = Event(
            event_name="My Event",
            creator_id=user.user_id,
            date_and_time=datetime(2050, 4, 22, tzinfo=timezone.utc),
            location="Krakow"
        )
        db.session.add(event_created)
        db.session.commit()

        response = client.get(f"/api/events/{user.user_id}/creator", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.get_json()["data"]
        
        assert len(data) == 1
        assert data[0]["name"] == "My Event"


def test_get_user_events_participant(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend = registered_friend[0]

        event_participating = Event(
            event_name="Event I am Attending",
            creator_id=friend.user_id,
            date_and_time=datetime(2050, 4, 22, tzinfo=timezone.utc),
            location="Warsaw"
        )
        db.session.add(event_participating)
        db.session.commit()

        response = client.post(f"/api/events/join/{event_participating.event_id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.get_json()["participant_count"] == 1
        
        response = client.get(f"/api/events/{user.user_id}/participant", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.get_json()["data"]
        
        assert len(data) == 1
        assert data[0]["name"] == "Event I am Attending"


def test_get_user_events_creator_empty(client, logged_in_user, app):
    user, token = logged_in_user
    
    response = client.get(f"/api/events/{user.user_id}/creator", headers={
        "Authorization": f"Bearer {token}"
    })
    
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) == 0

def test_get_user_events_participant_empty(client, logged_in_user, app):
    user, token = logged_in_user
    
    response = client.get(f"/api/events/{user.user_id}/participant", headers={
        "Authorization": f"Bearer {token}"
    })
    
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) == 0
