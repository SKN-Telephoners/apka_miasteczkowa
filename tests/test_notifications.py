import pytest
from unittest.mock import patch
from backend.extensions import db
from backend.models import FriendRequest, Friendship, User, Event, Notification
from backend.models.notification import NotificationTag
from backend.models.event import Event_visibility, Invites
from datetime import datetime, timezone, timedelta

def get_auth_header(token):
    return {"Authorization": f"Bearer {token}"}


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
        assert kwargs['from_user_id'] == user.user_id
        assert kwargs['to_user_id'] == friend.user_id
        assert kwargs['request_id'] == request_in_db.request_id


@patch('backend.notifications.invite_created.send')
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
        assert kwargs['from_user_id'] == user.user_id
        assert kwargs['to_user_id'] == friend.user_id
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

""" notifications screen """
def test_notifications_flow(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend, friend_password = registered_friend

        response = client.post(f"/api/friends/request/{friend.user_id}/create", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 201
        assert response.get_json()["message"] == "Friend request created"

        request_in_db = FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend.user_id).first()
        assert request_in_db is not None

        assert len(Notification.query.filter_by(user_id=friend.user_id).all()) == 1

        response_friend_login = client.post("/api/auth/login", json={"username": friend.username, "password": friend_password})
        assert response_friend_login.status_code == 200

        friend_data = response_friend_login.get_json()
        friend_token = friend_data["access_token"]

        response = client.get("/api/notifications/", headers=get_auth_header(friend_token))
        
        assert response.status_code == 200
        data = response.get_json()["data"]
        
        assert len(data) == 1
        assert data[0]["payload"]["message"] == f"{user.username} sent you a friend request."


def test_get_notifications_empty(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user
        response = client.get("/api/notifications/", headers=get_auth_header(token))
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert "data" in data
        assert "pagination" in data
        assert data["data"] == []
        assert data["pagination"]["total"] == 0
        assert data["pagination"]["pages"] == 0


def test_get_notifications_basic_and_sorting(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user
        
        notif_tag = list(NotificationTag)[0] 
        
        n_old = Notification(
            user_id=user.user_id, 
            tag=notif_tag, 
            is_read=True, 
            payload={"message": "Oldest message"},
            created_at=datetime.now(timezone.utc) - timedelta(days=2)
        )
        n_new = Notification(
            user_id=user.user_id, 
            tag=notif_tag, 
            is_read=False, 
            payload={"message": "Newest message"},
            created_at=datetime.now(timezone.utc)
        )
        
        db.session.add_all([n_old, n_new])
        db.session.commit()

        #default sort should be newest
        response = client.get("/api/notifications/", headers=get_auth_header(token))
        assert response.status_code == 200
        data = response.get_json()["data"]
        
        assert len(data) == 2
        assert data[0]["payload"]["message"] == "Newest message"
        
        #test oldest sort_mode
        response_asc = client.get("/api/notifications/?sort_mode=oldest", headers=get_auth_header(token))
        data_asc = response_asc.get_json()["data"]
        
        assert data_asc[0]["payload"]["message"] == "Oldest message"


def test_notifications_pagination_and_unread_count(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user
        notif_tag = list(NotificationTag)[0]
        
        #create 5 notifications, 3 unread, 2 read
        for i in range(5):
            n = Notification(
                user_id=user.user_id, 
                tag=notif_tag, 
                is_read=(i >= 3),
                payload={"message": f"Message {i}"}
            )
            db.session.add(n)
        db.session.commit()

        #first page
        response_p1 = client.get("/api/notifications/?page=1&limit=2", headers=get_auth_header(token))
        data_p1 = response_p1.get_json()
        
        assert len(data_p1["data"]) == 2
        assert data_p1["pagination"]["total"] == 5
        assert data_p1["pagination"]["pages"] == 3
        #unread_count is ONLY present on page 1
        assert data_p1["pagination"]["unread_count"] == 3 

        #second page
        response_p2 = client.get("/api/notifications/?page=2&limit=2", headers=get_auth_header(token))
        data_p2 = response_p2.get_json()
        
        assert len(data_p2["data"]) == 2
        assert data_p2["pagination"]["page"] == 2
        assert data_p2["pagination"]["unread_count"] is None


def test_notifications_search_query(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user
        notif_tag = list(NotificationTag)[0]

        n1 = Notification(user_id=user.user_id, tag=notif_tag, is_read=False, payload={"message": "Random message"})
        n2 = Notification(user_id=user.user_id, tag=notif_tag, is_read=False, payload={"message": "Another random message (but different)"})
        db.session.add_all([n1, n2])
        db.session.commit()

        response = client.get("/api/notifications/?q=different", headers=get_auth_header(token))
        data = response.get_json()["data"]
        
        assert len(data) == 1
        assert "different" in data[0]["payload"]["message"]


def test_notifications_status_filter(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user
        notif_tag = list(NotificationTag)[0]

        n_unread = Notification(user_id=user.user_id, tag=notif_tag, is_read=False, payload={"message": "Unread msg"})
        n_read = Notification(user_id=user.user_id, tag=notif_tag, is_read=True, payload={"message": "Read msg"})
        db.session.add_all([n_unread, n_read])
        db.session.commit()

        # Test unread filter
        res_unread = client.get("/api/notifications/?status=unread", headers=get_auth_header(token))
        data_unread = res_unread.get_json()["data"]
        assert len(data_unread) == 1
        assert data_unread[0]["is_read"] is False

        # Test read filter
        res_read = client.get("/api/notifications/?status=read", headers=get_auth_header(token))
        data_read = res_read.get_json()["data"]
        assert len(data_read) == 1
        assert data_read[0]["is_read"] is True


def test_notifications_tag_filter(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user
            
        tag_a = list(NotificationTag)[0]
        tag_b = list(NotificationTag)[1]

        n1 = Notification(user_id=user.user_id, tag=tag_a, is_read=False, payload={"message": "Type A"})
        n2 = Notification(user_id=user.user_id, tag=tag_b, is_read=False, payload={"message": "Type B"})
        db.session.add_all([n1, n2])
        db.session.commit()

        response = client.get(f"/api/notifications/?tag={tag_a.value}", headers=get_auth_header(token))
        data = response.get_json()["data"]
        
        assert len(data) == 1
        assert data[0]["tag"] == tag_a.value


def test_notifications_created_window(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user
        notif_tag = list(NotificationTag)[0]
        now = datetime.now(timezone.utc)

        n_today = Notification(
            user_id=user.user_id, tag=notif_tag, is_read=False, 
            payload={"message": "Today msg"}, created_at=now
        )
        n_old = Notification(
            user_id=user.user_id, tag=notif_tag, is_read=False, 
            payload={"message": "Old msg"}, created_at=now - timedelta(days=400)
        )
        db.session.add_all([n_today, n_old])
        db.session.commit()

        # Test today
        res_today = client.get("/api/notifications/?created_window=today", headers=get_auth_header(token))
        assert len(res_today.get_json()["data"]) == 1
        assert res_today.get_json()["data"][0]["payload"]["message"] == "Today msg"

        # Test older
        res_older = client.get("/api/notifications/?created_window=older", headers=get_auth_header(token))
        assert len(res_older.get_json()["data"]) == 1
        assert res_older.get_json()["data"][0]["payload"]["message"] == "Old msg"