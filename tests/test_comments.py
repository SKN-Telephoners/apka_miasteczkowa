import pytest
from backend.extensions import db
from backend.models import Comment
import uuid

# =============================================================================
# Tests for handling comments on events
# =============================================================================
@pytest.fixture
def comment(client, logged_in_user, event):
    user, token = logged_in_user

    payload = {"content": "Jebać UJ!"}

    client.post(f"/api/comments/create/{event.event_id}", headers={"Authorization": f"Bearer {token}"}, json=payload)
    comment = Comment.query.filter_by(user_id=user.user_id).first()
    return comment

def test_create_comment(client, app, logged_in_user, event):
    with app.app_context():
        user, token = logged_in_user

        payload = {
            "content": "Jebać UJ!",
        }

        response_create_comment = client.post(f"/api/comments/create/{event.event_id}", headers={
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

        response_create_comment = client.post(f"/api/comments/create/{event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        }, json = {"comment": ""})

        assert response_create_comment.status_code == 400
        assert response_create_comment.get_json() == {
            "message": "Bad request"
        }

        assert len(Comment.query.filter_by(user_id=user.user_id).all()) == 0

def test_delete_comment(client, app, logged_in_user, comment):
    with app.app_context():
        user, token = logged_in_user

        assert len(Comment.query.filter_by(user_id=user.user_id).all()) == 1
        comment = Comment.query.filter_by(user_id=user.user_id).first()

        response_delete_comment = client.delete(f"/api/comments/delete/{comment.comment_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_delete_comment.status_code == 200
        assert response_delete_comment.get_json() == {
            "message": "Comment deleted successfully"
        }

        assert len(Comment.query.filter_by(user_id=user.user_id).all()) == 1
        assert comment.deleted == True
        assert comment.content == ""
        assert comment.edited == True

def test_delete_comment_not_exist(client, app, logged_in_user):
    with app.app_context():
        token = logged_in_user[1]

        response_delete_comment = client.delete(f"/api/comments/delete/{uuid.uuid4()}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_delete_comment.status_code == 400
        assert response_delete_comment.get_json() == {
            "message": "Comment doesn't exist"
        }

def test_delete_comment_not_owner(client, logged_in_user, registered_friend, event, app):
    with app.app_context():
        user, token = logged_in_user
        friend = registered_friend[0]

        comment = Comment(
            user_id = friend.user_id, #other user
            event_id = event.event_id,
            content = "jebać UJ!"
        )
        db.session.add(comment)
        db.session.commit()

        # attempt delete
        response_delete_comment = client.delete(f"/api/comments/delete/{comment.comment_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_delete_comment.status_code == 401
        assert response_delete_comment.get_json() == {
            "message": "You can delete your own comments only"
        }

        assert len(Comment.query.filter_by(user_id=friend.user_id).all()) == 1
        assert comment.deleted != True
        assert comment.content != ""
        assert comment.edited != True

def test_edit_comment(client, app, logged_in_user, comment):
    with app.app_context():
        token = logged_in_user[1]

        response_edit_comment = client.put(f"/api/comments/edit/{comment.comment_id}", headers={
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

def test_edit_comment_not_exist(client, app, logged_in_user):
    with app.app_context():
        token = logged_in_user[1]
        response_edit_comment = client.put(f"/api/comments/edit/{uuid.uuid4()}", headers={
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
        response_edit_comment = client.put(f"/api/comments/edit/{comment.comment_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_edit_comment.status_code == 401
        assert response_edit_comment.get_json() == {
            "message": "You can edit your own comments only"
        }

def test_reply_to_comment(client, logged_in_user, comment, app):
    with app.app_context():
        token = logged_in_user[1]

        payload = {
            "content": "rel",
        }

        response_reply_to_comment = client.post(f"/api/comments/reply/{comment.comment_id}", headers={
            "Authorization": f"Bearer {token}"
        }, json=payload)

        assert response_reply_to_comment.status_code == 200
        assert response_reply_to_comment.get_json() == {
            "message": "Comment created successfully"
        }

        assert len(Comment.query.all()) == 2
        assert len(comment.replies) == 1
        assert comment.replies[0].content == 'rel'

def test_reply_to_comment_not_exist(client, app, logged_in_user):
    with app.app_context():
        token = logged_in_user[1]
        response_reply_to_comment = client.post(f"/api/comments/reply/{uuid.uuid4()}", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response_reply_to_comment.status_code == 400
        assert response_reply_to_comment.get_json() == {
            "message": "Parent comment doesn't exist"
        }

def test_get_comments_empty(client, logged_in_user, event, app):
    with app.app_context():
        token = logged_in_user[1]

        response = client.get(f"/api/comments/event/{event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        })

        data = response.get_json()

        assert response.status_code == 200
        assert data["comments"] == []
        assert data["message"] == "Empty comments list"

def test_get_comments_parent_only(client, logged_in_user, event, app):
    with app.app_context():
        user, token = logged_in_user
        c1 = Comment(user_id=user.user_id, event_id=event.event_id, content="First!")
        c2 = Comment(user_id=user.user_id, event_id=event.event_id, content="Second!")

        db.session.add_all([c1, c2])
        db.session.commit()

        response = client.get(f"/api/comments/event/{event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        })
        data = response.get_json()

        assert response.status_code == 200
        assert len(data["comments"]) == 2
        assert data["comments"][0]["replies"] == []

def test_get_comments_thread_structure(client, logged_in_user, event, app):
    with app.app_context():
        user, token = logged_in_user

        parent = Comment(user_id=user.user_id, event_id=event.event_id, content="Parent")
        db.session.add(parent)
        db.session.commit()

        reply = Comment(user_id=user.user_id, event_id=event.event_id, content="Child", parent_comment_id=parent.comment_id)
        db.session.add(reply)
        db.session.commit()

        assert parent.parent_comment_id == None
        assert reply.parent_comment_id == parent.comment_id

        response = client.get(f"/api/comments/event/{event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        })
        data = response.get_json()

        assert response.status_code == 200

        comments = data["comments"]
        assert len(comments) == 1

        root = comments[0]
        assert root["content"] == "Parent"
        assert len(root["replies"]) == 1
        assert root["replies"][0]["content"] == "Child"

def test_get_comments_deleted(client, logged_in_user, event, app):
    with app.app_context():
        user, token = logged_in_user

        comment = Comment(user_id=user.user_id, event_id=event.event_id, content="Original text")
        db.session.add(comment)
        db.session.commit()

        comment.soft_delete()
        db.session.commit()

        response = client.get(f"/api/comments/event/{event.event_id}", headers={
            "Authorization": f"Bearer {token}"
        })
        data = response.get_json()

        assert response.status_code == 200
        c = data["comments"][0]

        assert c["deleted"] is True
        assert c["content"] == "[deleted]"