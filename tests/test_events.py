import pytest
from backend.extensions import db
from backend.models import Event, Comment
from datetime import datetime
import uuid

# =============================================================================
# Tests for handling events
# =============================================================================
def test_create_event(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

        #create event
        payload = {
            "name": "event1",
            "description": "very cool event",
            "date": "01.01.2026",
            "time": "21:37",
            "location": "here"
        }

        response_create_event = client.post(f"/create_event", headers={
            "Authorization": f"Bearer {token}"
        }, json=payload)

        assert response_create_event.status_code == 200
        assert response_create_event.get_json() == {
            "message": "Event created successfully"
        }

def test_create_event_invalid_date(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

        #create event
        payload = {
            "name": "event1",
            "description": "very cool event",
            "date": "01.01.1995",
            "time": "21:37",
            "location": "here"
        }

        response_create_event = client.post(f"/create_event", headers={
            "Authorization": f"Bearer {token}"
        }, json=payload)

        assert response_create_event.status_code == 400
        assert response_create_event.get_json() == {
            "message": "Event date must be in the future"
        }

def test_delete_event(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

        #create event
        payload = {
            "name": "to delete",
            "description": "very cool event",
            "date": "01.01.2026",
            "time": "21:37",
            "location": "here"
        }

        response_create_event = client.post(f"/create_event", headers={
            "Authorization": f"Bearer {token}"
        }, json=payload)

        assert response_create_event.status_code == 200
        assert response_create_event.get_json() == {
            "message": "Event created successfully"
        }

        event = Event.query.filter_by(name="to delete").first()
        assert event is not None

        #delete event
        response_delete_event = client.delete(f"/delete_event/{event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_delete_event.status_code == 200
        assert response_delete_event.get_json() == {
            "message": "Event deleted successfully"
        }

        deleted = Event.query.filter_by(event_id=event.event_id).first()
        assert deleted is None

def test_delete_event_not_owner(client, logged_in_user, registered_friend, app):
    with app.app_context():
        user, token = logged_in_user
        friend = registered_friend[0]

        event = Event(
            name="event1",
            description="private",
            date_and_time=datetime(2026, 1, 1, 21, 37),
            location="here",
            creator_id=friend.user_id #other user
        )
        db.session.add(event)
        db.session.commit()

        # attempt delete
        response_delete_event = client.delete(f"/delete_event/{event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_delete_event.status_code == 401
        assert response_delete_event.get_json() == {
            "message": "You can delete your own events only"
        }

def test_delete_invalid_event(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user

        # attempt delete
        response_delete_event = client.delete(f"/delete_event/{uuid.uuid4()}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_delete_event.status_code == 400
        assert response_delete_event.get_json() == {
            "message": "Event doesn't exist"
        }

# =============================================================================
# Tests for handling comments on events
# =============================================================================

def test_create_comment(client, app, logged_in_user, event):
    with app.app_context():
        user, token = logged_in_user

        payload = {
            "content": "Jebać UJ!",
        }

        response_create_comment = client.post(f"/create_comment/{event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        }, json=payload)

        assert response_create_comment.status_code == 200
        assert response_create_comment.get_json() == {
            "message": "Comment created successfully"
        }

        assert len(Comment.query.filter_by(user_id=user.user_id).all()) == 1

def test_create_comment_no_content(client, app, logged_in_user, event):
    with app.app_context():
        user, token = logged_in_user

        response_create_comment = client.post(f"/create_comment/{event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        }, json = {"comment": ""})

        assert response_create_comment.status_code == 400
        assert response_create_comment.get_json() == {
            "message": "Bad request"
        }

        assert len(Comment.query.filter_by(user_id=user.user_id).all()) == 0

def test_delete_comment(client, app, logged_in_user, event):
    with app.app_context():
        user, token = logged_in_user

        payload = {
            "content": "jebać UJ!",
        }

        response_create_comment = client.post(f"/create_comment/{event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        }, json=payload)

        assert response_create_comment.status_code == 200
        assert response_create_comment.get_json() == {
            "message": "Comment created successfully"
        }

        assert len(Comment.query.filter_by(user_id=user.user_id).all()) == 1
        comment = Comment.query.filter_by(user_id=user.user_id).first()

        response_delete_comment = client.delete(f"/delete_comment/{comment.comment_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_delete_comment.status_code == 200
        assert response_delete_comment.get_json() == {
            "message": "Comment deleted successfully"
        }

def test_delete_comment_not_exist(client, app, logged_in_user, event):
    with app.app_context():
        token = logged_in_user[1]

        response_delete_comment = client.delete(f"/delete_comment/{uuid.uuid4()}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_delete_comment.status_code == 400
        assert response_delete_comment.get_json() == {
            "message": "Comment doesn't exist"
        }

def test_delete_comment_not_owner(client, logged_in_user, registered_friend, event, app):
    with app.app_context():
        token = logged_in_user[1]
        friend = registered_friend[0]

        comment = Comment(
            user_id = friend.user_id, #other user
            event_id = event.event_id,
            content = "jebać UJ!"
        )
        db.session.add(comment)
        db.session.commit()

        # attempt delete
        response_delete_comment = client.delete(f"/delete_comment/{comment.comment_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_delete_comment.status_code == 401
        assert response_delete_comment.get_json() == {
            "message": "You can delete your own comments only"
        }

def test_edit_comment(client, app, logged_in_user, event):
    with app.app_context():
        user, token = logged_in_user

        comment = Comment(
            user_id = user.user_id,
            event_id = event.event_id,
            content = "jebać UJ!"
        )
        db.session.add(comment)
        db.session.commit()

        response_edit_comment = client.post(f"/edit_comment/{comment.comment_id}", headers={
            "Authorization": f"Bearer {token}"
        }, json = {"new_content": "Jebać UKEN!"})

        assert response_edit_comment.status_code == 200
        assert response_edit_comment.get_json() == {
            "message": "Comment edited successfully"
        }

        assert len(Comment.query.all()) == 1
        edited_comment = Comment.query.filter_by(content="Jebać UKEN!").first()
        assert edited_comment is not None
        assert edited_comment.edited == True

def test_edit_comment_not_exist(client, app, logged_in_user, event):
    with app.app_context():
        token = logged_in_user[1]

        response_edit_comment = client.post(f"/edit_comment/{uuid.uuid4()}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_edit_comment.status_code == 400
        assert response_edit_comment.get_json() == {
            "message": "Comment doesn't exist"
        }

def test_edit_comment_not_owner(client, logged_in_user, registered_friend, event, app):
    with app.app_context():
        token = logged_in_user[1]
        friend = registered_friend[0]

        comment = Comment(
            user_id = friend.user_id, #other user
            event_id = event.event_id,
            content = "jebać UJ!"
        )
        db.session.add(comment)
        db.session.commit()

        # attempt edit
        response_edit_comment = client.post(f"/edit_comment/{comment.comment_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_edit_comment.status_code == 401
        assert response_edit_comment.get_json() == {
            "message": "You can edit your own comments only"
        }
