import pytest
from datetime import datetime, timezone, timedelta
from backend.models import User, TokenBlocklist, Event, Comment, Friendship
from backend.extensions import mail, db
from re import search
from flask_jwt_extended import create_access_token
from backend.helpers import add_token_to_db
from backend.constants import Constants
from unittest.mock import patch

# =============================================================================
# Helper for Auth Headers
# =============================================================================
def get_auth_header(token):
    return {"Authorization": f"Bearer {token}"}

# =============================================================================
# Tests for GET /api/users/profile
# =============================================================================
def test_get_user_info_success(client, logged_in_user):
    user, token = logged_in_user
    
    user.academy = "AGH"
    user.course = "Computer Science"
    user.faculty = "Wydział Informatyki"
    user.year = 2
    db.session.commit()

    response = client.get(f"/api/users/profile/{user.user_id}", headers=get_auth_header(token))
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["username"] == user.username
    assert data["email"] == user.email
    assert data["academy"] == "AGH"
    assert data["course"] == "Computer Science"
    assert data["faculty"] == "Wydział Informatyki"
    assert data["year"] == 2
    
def test_get_user_info_deleted_account(client, logged_in_user):
    user, token = logged_in_user
    user.deleted = True
    db.session.commit()

    response = client.get(f"/api/users/profile/{user.user_id}", headers=get_auth_header(token))
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["username"] == "[deleted]"
    assert data["deleted"] is True

# =============================================================================
# Tests for PUT /api/users/update_profile
# =============================================================================
@pytest.fixture
def mock_app_config(app):
    """Fixture to inject required config data for update_profile."""
    app.config['ACADEMY_DATA'] = {"AGH": {}, "UW": {}}
    app.config['COURSES_DATA'] = ["Computer Science", "Physics"]
    app.config['FACULTIES_DATA'] = ["Faculty1", "Faculty2"]
    app.config['CLUBS_DATA'] = {"Bite": {}, "DataScience": {}}
    return app

def test_update_profile_success(client, logged_in_user, app):
    user, token = logged_in_user
    
    payload = {
        "username": "new_valid_name",
        "description": "This is my new bio.",
        "academy": "AGH"
    }
    
    response = client.put("/api/users/update_profile", json=payload, headers=get_auth_header(token))
    
    assert response.status_code == 200
    assert response.get_json()["message"] == "Profile updated successfully"
    
    with app.app_context():
        u = db.session.get(User, user.user_id)
        assert u.username == "new_valid_name"
        assert u.description == "This is my new bio."
        assert u.academy == "AGH"

def test_update_profile_username_taken(client, logged_in_user, registered_friend, app):
    user, token = logged_in_user
    friend = registered_friend[0] 

    payload = {
        "username": friend.username 
    }
    
    response = client.put("/api/users/update_profile", json=payload, headers=get_auth_header(token))
    
    assert response.status_code == 400
    assert "Username already taken" in response.get_json()["message"]

def test_update_profile_invalid_academy(client, logged_in_user, app):
    user, token = logged_in_user
    
    payload = {
        "academy": "Hogwarts"
    }
    
    response = client.put("/api/users/update_profile", json=payload, headers=get_auth_header(token))
    
    assert response.status_code == 400
    assert "Such academy doesn't exist" in response.get_json()["message"]

def test_update_profile_missing_data(client, logged_in_user):
    _, token = logged_in_user
    
    response = client.put("/api/users/update_profile", json={}, headers=get_auth_header(token))
    
    assert response.status_code == 400
    assert "Invalid JSON or missing data" in response.get_json()["message"]

def test_update_profile_invalid_username(client, logged_in_user, registered_friend, mock_app_config):
    _, token = logged_in_user
    friend, _ = registered_friend

    payload = {"username": friend.username}
    response = client.put("/api/users/update_profile", json=payload, headers=get_auth_header(token))
    
    assert response.status_code == 400
    assert response.get_json()["message"] == "Username already taken"

def test_update_academic_details_success(client, logged_in_user, mock_app_config, app):
    user, token = logged_in_user
    
    with app.app_context():
        user.academy = "AGH"
        db.session.commit()
        
    u = User.query.filter_by(user_id=user.user_id).first()
    assert u.academy == "AGH"
        
    payload = {
        "course": "Computer Science",
        "faculty": "Faculty1",
        "year": "3",
        "academic_clubs": "Bite, DataScience"
    }
    
    response = client.put("/api/users/update_academic_details", json=payload, headers=get_auth_header(token))
    assert response.status_code == 200
    
    with app.app_context():
        u = User.query.filter_by(user_id=user.user_id).first()
        assert u.course == "Computer Science"
        assert u.faculty == "Faculty1"
        assert u.year == 3
        assert "Bite" in u.academic_clubs
        assert "DataScience" in u.academic_clubs


def test_update_academic_details_fails_for_non_primary(client, logged_in_user, app):
    user, token = logged_in_user
    
    with app.app_context():
        user = User.query.filter_by(user_id=user.user_id).first()
        user.academy = "UW" 
        db.session.commit()
        
    payload = {"course": "Computer Science", "faculty": "Faculty1", "year": "2"}
    response = client.put("/api/users/update_academic_details", json=payload, headers=get_auth_header(token))
    
    assert response.status_code == 400

    assert "Only AGH students can add academic details" in response.get_json()["message"]


def test_update_academic_details_fails_missing_pair(client, logged_in_user, app):
    user, token = logged_in_user
    
    with app.app_context():
        user.academy = "AGH"
        db.session.commit()
        
    u = User.query.filter_by(user_id=user.user_id).first()
    assert u.academy == "AGH"

    payload = {"course": "Computer Science", "faculty": "Faculty1"}
    response = client.put("/api/users/update_academic_details", json=payload, headers=get_auth_header(token))
    
    assert response.status_code == 400
    assert response.get_json()["message"] == "Faculty, course and year must be provided together"


def test_update_academic_details_invalid_year(client, logged_in_user, app):
    user, token = logged_in_user
    
    with app.app_context():
        user.academy = "AGH"
        db.session.commit()
        
    u = User.query.filter_by(user_id=user.user_id).first()
    assert u.academy == "AGH"

    payload = {
        "faculty": "Faculty1",
        "course": "Computer Science",
        "year": "7" 
    }
    
    response = client.put("/api/users/update_academic_details", json=payload, headers=get_auth_header(token))
    
    assert response.status_code == 400
    assert response.get_json()["message"] == "Year must be between 1 and 6"

# =============================================================================
# Tests for PUT /api/users/settings/password
# =============================================================================
def test_change_password_success(client, logged_in_user):
    user, token = logged_in_user
    
    payload = {
        "old_password": "Secret123!", #from fixture
        "new_password": "NewStrongPassword!1"
    }

    response = client.put("/api/users/settings/password", json=payload, headers=get_auth_header(token))
    
    assert response.status_code == 200
    assert user.validate_password("NewStrongPassword!1") is True
    
    # Check if old tokens were revoked
    revoked_token = TokenBlocklist.query.filter_by(user_id=user.user_id).first()
    assert revoked_token is not None

def test_change_password_wrong_old_password(client, logged_in_user):
    _, token = logged_in_user
    payload = {
        "old_password": "WrongPassword123",
        "new_password": "NewStrongPassword!1"
    }
    response = client.put("/api/users/settings/password", json=payload, headers=get_auth_header(token))
    assert response.status_code == 401
    assert response.get_json()["message"] == "Old password incorrect"

# =============================================================================
# Tests for PUT /api/users/settings/change_email
# =============================================================================
def test_change_email_success(client, app, logged_in_user):
    user, token = logged_in_user
    new_email = "new_email@gmail.com"
    old_email = user.email

    with app.app_context():
        payload = {
            "new_email": new_email
        }

        with mail.record_messages() as outbox:
            response = client.put("/api/users/settings/change_email", json=payload, headers=get_auth_header(token))

            assert response.status_code == 200
            assert response.get_json()["message"] == "Verification link sent to new email"
            
            assert len(outbox) == 2
            
            confirm_msg = next((msg for msg in outbox if new_email in msg.recipients), None)
            alert_msg = next((msg for msg in outbox if old_email in msg.recipients), None)
            
            assert confirm_msg is not None, "Confirmation email was not sent to the new address"
            assert alert_msg is not None, "Security alert was not sent to the old address"

            assert confirm_msg.subject == 'Change email confirmation'
            assert alert_msg.subject == 'Security Alert: Email Change Requested'

            match = search(r'(https?://.+/confirm_change/\S+)', confirm_msg.body)
            assert match, "No confirm change URL found in confirmation email body"

            change_url = match.group()
            token_path = change_url.replace("http://localhost", "")
            token_path = token_path.replace("https://localhost", "")

            response = client.post(token_path)

            assert response.status_code == 200
            assert response.get_json()["message"] == "Email changed succesfully"

        user = db.session.get(User, user.user_id)
        assert user.email == new_email

def test_change_email_already_exists(client, app, logged_in_user, registered_friend):
    user, token = logged_in_user
    friend, _ = registered_friend
    
    with app.app_context():
        payload = {
            "new_email": friend.email
        }

        with mail.record_messages() as outbox:
            response = client.put("/api/users/settings/change_email", json=payload, headers=get_auth_header(token))
            
            assert response.status_code == 409 
            assert response.get_json()["message"] == "Account with this email already exists"
            assert len(outbox) == 0

def test_change_email_invalid_format(client, app, logged_in_user):
    user, token = logged_in_user
    
    with app.app_context():
        payload = {
            "new_email": "invalid-email-format"
        }

        with mail.record_messages() as outbox:
            response = client.put("/api/users/settings/change_email", json=payload, headers=get_auth_header(token))
            
            assert response.status_code == 400 
            assert response.get_json()["message"] == "Invalid email format"
            assert len(outbox) == 0

def test_change_email_missing_data(client, app, logged_in_user):
    user, token = logged_in_user
    
    with app.app_context():
        payload = {} # Empty payload

        with mail.record_messages() as outbox:
            response = client.put("/api/users/settings/change_email", json=payload, headers=get_auth_header(token))
            
            assert response.status_code == 400
            assert len(outbox) == 0

# =============================================================================
# Tests for DELETE /api/users/settings/logout_all
# =============================================================================
def test_logout_all(client, logged_in_user):
    user, token = logged_in_user
    response = client.delete("/api/users/settings/logout_all", headers=get_auth_header(token))
    
    assert response.status_code == 200
    assert response.get_json()["message"] == "Successfully logged out from all devices"
    revoked_token = TokenBlocklist.query.filter_by(user_id=user.user_id).first()
    assert revoked_token is not None

# =============================================================================
# Tests for DELETE /api/users/settings/delete_account
# =============================================================================
def test_delete_account_success(client, logged_in_user):
    user, token = logged_in_user
    payload = {"password": "Secret123!"} 

    response = client.delete("/api/users/settings/delete_account", json=payload, headers=get_auth_header(token))
    
    assert response.status_code == 200
    assert user.deleted is True
    assert user.username.startswith("del_")
    assert user.email.endswith("@del.local")
    assert user.description is None
    
    #check if token is revoked
    revoked_token = TokenBlocklist.query.filter_by(user_id=user.user_id).first()
    assert revoked_token is not None

def test_delete_account_wrong_password(client, logged_in_user):
    user, token = logged_in_user
    payload = {"password": "WrongPassword"} 

    response = client.delete("/api/users/settings/delete_account", json=payload, headers=get_auth_header(token))
    
    assert response.status_code == 401
    assert user.deleted is False

# =============================================================================
# Tests for POST /confirm_change/<token>
# =============================================================================
def test_confirm_email_change_success(client, app, logged_in_user):
    user, _ = logged_in_user
    user.pending_email = "new_email@gmail.com"
    db.session.commit()

    with app.app_context():
        # Generate a valid email_change token
        token = create_access_token(
            identity=str(user.user_id),
            expires_delta=timedelta(minutes=Constants.CHANGE_EMAIL_EXPIRES),
            additional_claims={"type": "email_change"}
        )
        
        add_token_to_db(token)

    response = client.post(f"/api/email/confirm_change/{token}")
    
    assert response.status_code == 200
    assert response.get_json()["message"] == "Email changed succesfully"
    assert user.email == "new_email@gmail.com"

def test_confirm_email_change_invalid_type(client, app, logged_in_user):
    from flask_jwt_extended import create_access_token
    
    user, _ = logged_in_user

    with app.app_context():
        # Generate token with wrong type
        token = create_access_token(
            identity=str(user.user_id),
            additional_claims={"type": "access"} 
        )

    response = client.post(f"/api/email/confirm_change/{token}")
    assert response.status_code == 401

# =============================================================================
# Test display_name property
# =============================================================================

#/api/users/profile
def test_profile_displays_deleted_username(client, logged_in_user):
    user, token = logged_in_user
    
    user.deleted = True
    user.username = "del_a1b2c3d4e5"
    db.session.commit()

    response = client.get(f"/api/users/profile/{user.user_id}", headers=get_auth_header(token))
    
    assert response.status_code == 200
    data = response.get_json()
    
    assert data["username"] == "[deleted]"
    assert data["deleted"] is True

#/api/friends/list
def test_friends_list_shows_deleted_user(client, app, logged_in_user):
    active_user, token = logged_in_user
    
    with app.app_context():
        deleted_friend = User(
            username="del_123456789", 
            email="del_123@del.local", 
            password="scrambled",
            deleted=True
        )
        db.session.add(deleted_friend)
        db.session.commit()

        id1, id2 = str(active_user.user_id), str(deleted_friend.user_id)
        u_id, f_id = (id1, id2) if id1 < id2 else (id2, id1)

        friendship = Friendship(user_id=u_id, friend_id=f_id)
        db.session.add(friendship)
        db.session.commit()

    response = client.get("/api/friends/list", headers=get_auth_header(token))
    
    assert response.status_code == 200
    data = response.get_json()["friends"]
    
    assert len(data) == 1
    assert data[0]["username"] == "[deleted]"


#/api/events/feed
def test_feed_shows_deleted_creator(client, app, logged_in_user):
    active_user, token = logged_in_user
    
    with app.app_context():
        deleted_creator = User(
            username="del_987654321", 
            email="del_987@del.local", 
            password="scrambled",
            deleted=True
        )
        db.session.add(deleted_creator)
        db.session.commit()

        future_date = datetime.now(timezone.utc) + timedelta(days=1)
        
        event = Event(
            event_name="Ghost Event",
            description="Created by someone who left",
            date_and_time=future_date,
            location="Krakow",
            creator_id=deleted_creator.user_id,
            is_private=False
        )
        db.session.add(event)
        db.session.commit()

    response = client.get("/api/events/feed", headers=get_auth_header(token))
    
    assert response.status_code == 200

    response_json = response.get_json()
    events = response_json.get("data", [])
    
    assert len(events) >= 1
    
    ghost_event = next(e for e in events if e["name"] == "Ghost Event")
    assert ghost_event["creator_username"] == "[deleted]"

# /api/comments/event/<event_id>
def test_comments_show_deleted_author(client, app, logged_in_user):
    active_user, token = logged_in_user
    
    with app.app_context():
        deleted_commenter = User(
            username="del_abcdefgh", 
            email="del_abc@del.local", 
            password="scrambled",
            deleted=True
        )
        db.session.add(deleted_commenter)
        db.session.commit()

        future_date = datetime.now(timezone.utc) + timedelta(days=1)

        event = Event(
            event_name="Discussion Event",
            date_and_time=future_date,
            location="Krakow",
            creator_id=active_user.user_id,
            is_private=False
        )
        db.session.add(event)
        db.session.commit()

        deleted_user_comment = Comment(
            event_id=event.event_id,
            user_id=deleted_commenter.user_id,
            content="This is a comment from the past.",
        )
        db.session.add(deleted_user_comment)
        db.session.commit()
        
        event_id_to_test = event.event_id

    response = client.get(f"/api/comments/event/{event_id_to_test}", headers=get_auth_header(token))
    
    assert response.status_code == 200
    comments = response.get_json()["comments"]
    
    assert len(comments) == 1
    assert comments[0]["content"] == "This is a comment from the past."
    assert comments[0]["username"] == "[deleted]"

# =============================================================================
# Tests for profile pictures lifecycle
# =============================================================================

def test_get_profile_no_picture(client, logged_in_user, app):
    user, token = logged_in_user
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(f"/api/users/profile/{user.user_id}", headers=headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["profile_picture"] is None


def test_update_profile_add_picture(client, logged_in_user, app):
    user, token = logged_in_user
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "profile_picture": {"cloud_id": "profile_pic_123"}
    }
    
    response = client.put("/api/users/update_profile", json=payload, headers=headers)
    assert response.status_code == 200
    
    profile_res = client.get(f"/api/users/profile/{user.user_id}", headers=headers)
    pic_data = profile_res.get_json()["profile_picture"]
    
    assert pic_data is not None
    assert pic_data["cloud_id"] == "profile_pic_123"
    assert "url" in pic_data 


@patch('cloudinary.uploader.destroy')
def test_update_profile_replace_picture(mock_destroy, client, logged_in_user, app):
    user, token = logged_in_user
    headers = {"Authorization": f"Bearer {token}"}

    client.put("/api/users/update_profile", json={"profile_picture": {"cloud_id": "old_pic"}}, headers=headers)
    
    replace_payload = {
        "profile_picture": {"cloud_id": "new_pic"}
    }
    response = client.put("/api/users/update_profile", json=replace_payload, headers=headers)
    assert response.status_code == 200
    
    mock_destroy.assert_called_once_with("old_pic")
    
    with app.app_context():
        user = User.query.filter_by(user_id=user.user_id).first()
        assert user.profile_picture == "new_pic"


@patch('cloudinary.uploader.destroy')
def test_update_profile_delete_picture(mock_destroy, client, logged_in_user, app):
    user, token = logged_in_user
    headers = {"Authorization": f"Bearer {token}"}

    client.put("/api/users/update_profile", json={"profile_picture": {"cloud_id": "to_delete_pic"}}, headers=headers)

    delete_payload = {
        "profile_picture": None
    }
    response = client.put("/api/users/update_profile", json=delete_payload, headers=headers)
    assert response.status_code == 200

    mock_destroy.assert_called_once_with("to_delete_pic")
    
    with app.app_context():
        user = User.query.filter_by(user_id=user.user_id).first()
        assert user.profile_picture == None


@patch('cloudinary.uploader.destroy')
def test_delete_account_removes_picture(mock_destroy, client, logged_in_user, app):
    user, token = logged_in_user
    headers = {"Authorization": f"Bearer {token}"}
    
    client.put("/api/users/update_profile", json={"profile_picture": {"cloud_id": "account_del_pic"}}, headers=headers)
    
    delete_payload = {"password": "Secret123!"} 
    
    response = client.delete("/api/users/settings/delete_account", json=delete_payload, headers=headers)
    assert response.status_code == 200
    
    mock_destroy.assert_called_once_with("account_del_pic")
    
    with app.app_context():
        user = User.query.filter_by(user_id=user.user_id).first()
        assert user.profile_picture == None


def test_get_user_info_friend_count(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend = registered_friend[0]

        if user.user_id < friend.user_id:
            friendship = Friendship(user_id=user.user_id, friend_id=friend.user_id)
        else:
            friendship = Friendship(user_id=friend.user_id, friend_id=user.user_id)
            
        db.session.add(friendship)
        db.session.commit()
        
        response = client.get(f"/api/users/profile/{user.user_id}", headers=get_auth_header(token))
        assert response.status_code == 200
        
        data = response.get_json()
        assert "friend_count" in data
        assert data["friend_count"] == 1
# =============================================================================
# Tests for users list 
# =============================================================================


def test_get_users_list_success(client, logged_in_user, registered_friend, app):
    """Test podstawowy: pobieranie listy, wykluczenie siebie i usuniętych użytkowników."""
    with app.app_context():
        user, token = logged_in_user
        friend, _ = registered_friend

        deleted_user = User(username="ghost_user", email="ghost@del.local", password="password123")
        deleted_user.deleted = True
        db.session.add(deleted_user)
        db.session.commit()

        response = client.get("/api/users/users_list", headers=get_auth_header(token))

        assert response.status_code == 200
        res_json = response.get_json()

        users = res_json["users"]
        user_ids = [u["user_id"] for u in users]

        assert str(friend.user_id) in user_ids
        assert str(user.user_id) not in user_ids
        assert str(deleted_user.user_id) not in user_ids

def test_get_users_list_search(client, logged_in_user, app):
    """Test wyszukiwania po parametrze ?search=."""
    with app.app_context():
        _, token = logged_in_user
        
        u1 = User(username="Alexander", email="alex@test.com", password="password123", is_confirmed=True)
        u2 = User(username="Barnaba", email="barney@test.com", password="password123", is_confirmed=True)
        db.session.add_all([u1, u2])
        db.session.commit()

        response = client.get("/api/users/users_list?search=Alex", headers=get_auth_header(token))

        assert response.status_code == 200
        res_json = response.get_json()
        users = res_json["users"]
        
        assert any(u["username"] == "Alexander" for u in users)
        assert not any(u["username"] == "Barnaba" for u in users)

def test_get_users_list_friend_priority(client, logged_in_user, app):
    """Test czy znajomi pojawiają się na początku listy."""
    with app.app_context():
        user, token = logged_in_user
        
        u_stranger = User(username="A_stranger", email="stranger@test.com", password="password123", is_confirmed=True)
        u_friend = User(username="Z_friend", email="friend@test.com", password="password123", is_confirmed=True)
        db.session.add_all([u_stranger, u_friend])
        db.session.commit()

        uid1, uid2 = sorted([user.user_id, u_friend.user_id])
        friendship = Friendship(user_id=uid1, friend_id=uid2)
        db.session.add(friendship)
        db.session.commit()

        response = client.get("/api/users/users_list", headers=get_auth_header(token))

        assert response.status_code == 200
        users = response.get_json()["users"]

        idx_friend = next(i for i, u in enumerate(users) if u["username"] == "Z_friend")
        idx_stranger = next(i for i, u in enumerate(users) if u["username"] == "A_stranger")
        
        assert idx_friend < idx_stranger

def test_get_users_list_pagination(client, logged_in_user, app):
    """Test paginacji i limitów."""
    with app.app_context():
        _, token = logged_in_user
        
        for i in range(5):
            db.session.add(User(username=f"PaginationUser_{i}", email=f"page{i}@test.com", password="password123", is_confirmed=True))
        db.session.commit()

        response = client.get("/api/users/users_list?page=1&limit=2", headers=get_auth_header(token))
        
        assert response.status_code == 200
        res_json = response.get_json()
        
        assert len(res_json["users"]) == 2
        assert res_json["pagination"]["current_page"] == 1
        assert res_json["pagination"]["total"] >= 5

def test_get_users_list_invalid_pagination(client, logged_in_user):
    """Test obsługi błędnych danych paginacji (np. tekst zamiast liczb)."""
    _, token = logged_in_user

    response = client.get("/api/users/users_list?page=abc&limit=xyz", headers=get_auth_header(token))

    assert response.status_code == 200
    assert "Operation successful" in response.get_json()["message"]
