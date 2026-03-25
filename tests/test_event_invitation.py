import pytest
from backend.app import create_app
from backend.extensions import db
from backend.models import User, Event, Invite
import uuid


def test_invite_user(client, logged_in_user, registered_friend, event):
    user, token = logged_in_user
    friend, _ = registered_friend

    response = client.post(
        f"/api/events/{event.event_id}/invite/new",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": [str(friend.user_id)]}
    )

    assert response.status_code == 201
    assert response.get_json()["message"] == "Invite successfully"

    invite = Invite.query.filter_by(
        event_id=event.event_id,
        user_id=friend.user_id
    ).first()

    assert invite is not None

def test_invite_bad_request(client, logged_in_user, event):
    user, token = logged_in_user

    response = client.post(
        f"/api/events/{event.event_id}/invite/new",
        headers={"Authorization": f"Bearer {token}"},
        json={}
    )

    assert response.status_code == 400

def test_list_invites_empty(client, logged_in_user, event):
    user, token = logged_in_user

    response = client.get(
        f"/api/events/{event.event_id}/invite/list",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["data"] == []

def test_list_invites(client, logged_in_user, registered_friend, event):
    user, token = logged_in_user
    friend, _ = registered_friend

    # add invite manual
    db.session.add(Invite(
        event_id=event.event_id,
        user_id=friend.user_id
    ))
    db.session.commit()

    response = client.get(
        f"/api/events/{event.event_id}/invite/list",
        headers={"Authorization": f"Bearer {token}"}
    )


    assert response.status_code == 200
    data = response.get_json()
    assert len(data["data"]) == 1
    assert data["data"][0]["username"] == friend.username

def test_delete_invite(client, logged_in_user, registered_friend, event):
    user, token = logged_in_user
    friend, _ = registered_friend

    invite = Invite(
        event_id=event.event_id,
        user_id=friend.user_id
    )
    db.session.add(invite)
    db.session.commit()

    response = client.delete(
        f"/api/events/{event.event_id}/invite/delete",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": [str(friend.user_id)]}
    )

    assert response.status_code == 204

    deleted = Invite.query.filter_by(
        event_id=event.event_id,
        user_id=friend.user_id
    ).first()

    assert deleted is None

def test_invite_unauthorized_user(client, registered_friend, event):
    friend, password = registered_friend

    login = client.post(
        "/api/auth/login",
        json={"username": friend.username, "password": password}
    )

    token = login.get_json()["access_token"]

    response = client.post(
        f"/api/events/{event.event_id}/invite/new",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": []}
    )

    assert response.status_code == 403


def test_invite_multiple_users_with_existing(client, logged_in_user, registered_friend, event):
    user, token = logged_in_user
    friend1, _= registered_friend

    friend2 = User(
        username="friend2",
        password="test123",
        email="friend2@test.com"
    )
    db.session.add(friend2)

    db.session.add(Invite(
        event_id=event.event_id,
        user_id=friend1.user_id
    ))

    db.session.commit()

    response = client.post(
        f"/api/events/{event.event_id}/invite/new",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": [str(friend1.user_id), str(friend2.user_id)]}
    )

    assert response.status_code == 201

    invites = Invite.query.filter_by(event_id=event.event_id).all()

    invited_ids = {invite.user_id for invite in invites}

    assert len(invites) == 2  # nie 3!
    assert friend1.user_id in invited_ids
    assert friend2.user_id in invited_ids