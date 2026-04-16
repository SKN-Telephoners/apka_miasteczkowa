import pytest
from unittest.mock import patch
from backend.extensions import db
from backend.models import FriendRequest, Friendship, User, Event
from backend.models.event import Event_visibility, Invites
from datetime import datetime, timezone


@patch('backend.notifications.friend_request_created.send')
def test_create_friend_request_emits_signal(mock_signal, client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend = registered_friend[0]

        response = client.post(f"/api/friends/request/{friend.user_id}/create", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 201
        assert response.get_json()["message"] == "Friend request created"

        request_in_db = FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend.user_id).first()
        assert request_in_db is not None

        mock_signal.assert_called_once()
        args, kwargs = mock_signal.call_args
        assert kwargs['from_user'] == user.user_id
        assert kwargs['to_user'] == friend.user_id
        assert kwargs['request_id'] == request_in_db.request_id


@patch('backend.notifications.event_invite_sent.send')
def test_invite_to_event_success(mock_signal, client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend = registered_friend[0]

        if user.user_id < friend.user_id:
            new_friendship = Friendship(user_id=user.user_id, friend_id=friend.user_id)
        else:
            new_friendship = Friendship(user_id=friend.user_id, friend_id=user.user_id)
        db.session.add(new_friendship)

        new_event = Event(
            event_name="Public Test Event",
            description="public",
            date_and_time=datetime(2050, 1, 20, 21, 37, tzinfo=timezone.utc),
            location="here",
            creator_id=user.user_id, 
            is_private=False
        )
        db.session.add(new_event)
        db.session.commit()

        response = client.post(f"/api/events/invite/{new_event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        }, json={
            "invited": str(friend.user_id)
        })

        assert response.status_code == 201
        assert response.get_json()["message"] == "Invite created successfully"

        invite_in_db = Invites.query.filter_by(event_id=new_event.event_id, invited_id=friend.user_id).first()
        assert invite_in_db is not None

        mock_signal.assert_called_once()
        args, kwargs = mock_signal.call_args
        assert kwargs['from_user'] == user.user_id
        assert kwargs['to_user'] == friend.user_id
        assert kwargs['event_id'] == new_event.event_id

def test_invite_to_event_not_friends(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

        stranger = User(username="stranger", password="Password123!", email="stranger@test.com", is_confirmed=True)
        db.session.add(stranger)

        new_event = Event(
            event_name="Public Test Event",
            description="public",
            date_and_time=datetime(2050, 1, 20, 21, 37, tzinfo=timezone.utc),
            location="here",
            creator_id=user.user_id, 
            is_private=False
        )
        db.session.add(new_event)
        db.session.commit()

        response = client.post(f"/api/events/invite/{new_event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        }, json={
            "invited": str(stranger.user_id)
        })

        assert response.status_code == 403
        assert response.get_json()["message"] == "You can only invite your friends"

def test_invite_private_event_no_visibility(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend = registered_friend[0]

        if user.user_id < friend.user_id:
            new_friendship = Friendship(user_id=user.user_id, friend_id=friend.user_id)
        else:
            new_friendship = Friendship(user_id=friend.user_id, friend_id=user.user_id)
        db.session.add(new_friendship)

        private_event = Event(
            event_name="Secret Event",
            description="private",
            date_and_time=datetime(2050, 1, 20, 21, 37, tzinfo=timezone.utc),
            location="here",
            creator_id=user.user_id, 
            is_private=True
        )
        db.session.add(private_event)
        db.session.commit() 

        response = client.post(f"/api/events/invite/{private_event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        }, json={
            "invited": str(friend.user_id)
        })

        assert response.status_code == 403
        assert response.get_json()["message"] == "User does not have priviledges to view this event"

def test_invite_private_event_with_visibility(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend = registered_friend[0]

        if user.user_id < friend.user_id:
            new_friendship = Friendship(user_id=user.user_id, friend_id=friend.user_id)
        else:
            new_friendship = Friendship(user_id=friend.user_id, friend_id=user.user_id)
        db.session.add(new_friendship)

        private_event = Event(
            event_name="Secret Event",
            description="private",
            date_and_time=datetime(2050, 1, 20, 21, 37, tzinfo=timezone.utc),
            location="here",
            creator_id=user.user_id, 
            is_private=True
        )
        db.session.add(private_event)
        db.session.commit() 

        visibility = Event_visibility(
            event_id=private_event.event_id, 
            shared_with=friend.user_id,
            sharing=user.user_id 
        )
        db.session.add(visibility)
        db.session.commit()

        response = client.post(f"/api/events/invite/{private_event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        }, json={
            "invited": str(friend.user_id)
        })

        assert response.status_code == 201
        assert response.get_json()["message"] == "Invite created successfully"