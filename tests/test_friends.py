import pytest
from backend.extensions import db
from backend.models import FriendRequest, Friendship
import json
import uuid

# =============================================================================
# Tests for handling friend requests
# =============================================================================
def test_cancel_friend_request(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend = registered_friend[0]

        #create friend request
        response_create_request = client.post(f"/create_friend_request/{friend.user_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_create_request.status_code == 201
        assert response_create_request.get_json()["message"] == "Friend request created"

        assert FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend.user_id).first() is not None

        #cancel friend request
        response_cancel_request = client.post(f"/cancel_friend_request/{friend.user_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_cancel_request.status_code == 200
        assert response_cancel_request.get_json()["message"] == "Friend request cancelled"
        
        assert "friend_id" in response_cancel_request.get_json()

        assert (Friendship.query.filter_by(user_id=user.user_id, friend_id=friend.user_id).first() or
                Friendship.query.filter_by(user_id=friend.user_id, friend_id=user.user_id).first()) is None
        
        assert FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend.user_id).first() is None

def test_cancel_friend_request_not_exist(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user
        random_id = uuid.uuid4()

        #cancel friend request
        response_cancel_request = client.post(f"/cancel_friend_request/{uuid.uuid4()}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_cancel_request.status_code == 404
        assert response_cancel_request.get_json()["message"] == "Such request doesn't exist"

        assert (Friendship.query.filter_by(user_id=user.user_id, friend_id=random_id).first() or
                Friendship.query.filter_by(user_id=random_id, friend_id=user.user_id).first()) is None
        
        assert FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=random_id).first() is None

def test_accept_friend_request(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend, friend_password = registered_friend

        #create friend request
        response_create_request = client.post(f"/create_friend_request/{friend.user_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_create_request.status_code == 201

        assert FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend.user_id).first() is not None
        
        #friend logs in
        response_friend_login = client.post("/api/login", json={"username": friend.username, "password": friend_password})
        assert response_friend_login.status_code == 200

        friend_data = json.loads(response_friend_login.data)
        friend_token = friend_data["access_token"]

        #accept friend request
        response_accept_request = client.post(f"/accept_friend_request/{user.user_id}", headers={
            "Authorization": f"Bearer {friend_token}"
        })

        assert response_accept_request.status_code == 200
        
        assert "friend_id" in response_accept_request.get_json()

        assert (Friendship.query.filter_by(user_id=user.user_id, friend_id=friend.user_id).first() or
                Friendship.query.filter_by(user_id=friend.user_id, friend_id=user.user_id).first()) is not None
        
        assert FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend.user_id).first() is None

def test_decline_friend_request(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend, friend_password = registered_friend

        #create friend request
        response_create_request = client.post(f"/create_friend_request/{friend.user_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_create_request.status_code == 201

        assert FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend.user_id).first() is not None
        
        #friend logs in
        response_friend_login = client.post("/api/login", json={"username": friend.username, "password": friend_password})
        assert response_friend_login.status_code == 200

        friend_data = json.loads(response_friend_login.data)
        friend_token = friend_data["access_token"]

        #decline friend request
        response_decline_request = client.post(f"/decline_friend_request/{user.user_id}", headers={
            "Authorization": f"Bearer {friend_token}"
        })

        assert response_decline_request.status_code == 200
        assert response_decline_request.get_json()["message"] == "Friend request declined"

        assert (Friendship.query.filter_by(user_id=user.user_id, friend_id=friend.user_id).first() and
                Friendship.query.filter_by(user_id=friend.user_id, friend_id=user.user_id).first()) is None
        
        assert FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend.user_id).first() is None

def test_friend_not_exist(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

        #create friend request
        friend_id = uuid.uuid4()
        response_create_request = client.post(f"/create_friend_request/{friend_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_create_request.status_code == 404
        assert FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend_id).first() is None

def test_befriend_yourself(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user
        #create friend request
        response_create_request = client.post(f"/create_friend_request/{user.user_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_create_request.status_code == 400
        assert FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=user.user_id).first() is None

def test_request_exists(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend = registered_friend[0]

        new_request = FriendRequest(sender_id=user.user_id, receiver_id=friend.user_id)
        db.session.add(new_request)
        db.session.commit()

        #create friend request
        response_create_request = client.post(f"/create_friend_request/{friend.user_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_create_request.status_code == 409
        assert response_create_request.get_json()["message"] == "Request already exists"

        assert len(FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend.user_id).all()) == 1

def test_friendship_exists(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend= registered_friend[0]

        if user.user_id < friend.user_id:
            new_friendship = Friendship(user_id=user.user_id, friend_id=friend.user_id)
        else:
            new_friendship = Friendship(user_id=friend.user_id, friend_id=user.user_id)

        db.session.add(new_friendship)
        db.session.commit()

        #create friend request
        response_create_request = client.post(f"/create_friend_request/{friend.user_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_create_request.status_code == 409 
        assert response_create_request.get_json()["message"] == "Friendship already exists"

        assert FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend.user_id).first() is None

def test_accept_request_not_exist(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend = registered_friend[0]

        #accept friend request
        response_accept_request = client.post(f"/accept_friend_request/{friend.user_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_accept_request.status_code == 404
        assert response_accept_request.get_json()["message"] == "Such request doesn't exist"

        assert (Friendship.query.filter_by(user_id=user.user_id, friend_id=friend.user_id).first() and
                Friendship.query.filter_by(user_id=friend.user_id, friend_id=user.user_id).first()) is None

def test_decline_request_not_exist(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend = registered_friend[0]

        #decline friend request
        response_decline_request = client.post(f"/decline_friend_request/{friend.user_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_decline_request.status_code == 404
        assert response_decline_request.get_json()["message"] == "Such request doesn't exist"

        assert (Friendship.query.filter_by(user_id=user.user_id, friend_id=friend.user_id).first() and
                Friendship.query.filter_by(user_id=friend.user_id, friend_id=user.user_id).first()) is None

def test_get_not_empty_friends_list(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend = registered_friend[0]

        if user.user_id < friend.user_id:
            new_friendship = Friendship(user_id=user.user_id, friend_id=friend.user_id)
        else:
            new_friendship = Friendship(user_id=friend.user_id, friend_id=user.user_id)

        db.session.add(new_friendship)
        db.session.commit()

        response = client.get("/get_friends_list", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200

        data = response.get_json()

        assert "friends" in data
        assert len(data["friends"]) == 1
        assert data["message"] == "Friends list"
        
        assert uuid.UUID(data["friends"][0]["id"]) == friend.user_id
        assert data["friends"][0]["username"] == friend.username

def test_get_empty_friends_list(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

        response = client.get("/get_friends_list", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200

        data = response.get_json()

        assert data["message"] == "Empty friends list"
        assert data["friends"] == []