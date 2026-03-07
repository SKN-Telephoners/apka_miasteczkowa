import pytest
from backend.extensions import db
from backend.models import User

def test_edit_profile(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user
        new_user_data = {
            "username": "edited username",
        }
        #edit profile
        response_edit_profile = client.put("api/users/me/edit_profile", headers={
            "Authorization": f"Bearer {token}"
        }, json=new_user_data)
        assert response_edit_profile.status_code == 200
        assert response_edit_profile.get_json() == {
            "message": "Profile edited successfully"
        }
        
        edited_user = User.query.filter_by(user_id=user.user_id).first()
        assert edited_user.username == "edited username"

def test_edit_profile_invalid_payload(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user
        
        payload = {
            "username": "a" #too short
        }

        response = client.put("api/users/me/edit_profile", headers={"Authorization": f"Bearer {token}"}, json=payload)
        assert response.status_code == 400
        assert response.get_json()["message"] == "Username must be between 3 and 32 characters"