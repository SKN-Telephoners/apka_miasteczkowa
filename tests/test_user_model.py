import pytest
from backend.extensions import db
from backend.models import User
import json
import re
from sqlalchemy import or_

# =============================================================================
# Tests for user model working corectlly
# =============================================================================
def test_user_update(client, logged_in_user, app):
    with app.app_context():
        user, token = logged_in_user
        
        #create user info
        payload = {
            "course" : "Ceramika" , 
            "year" : "3",
            "academy" : "AGH", 
            "academic_circle" : "Koło Naukowe Inteligentnych Sterowników w Automatyce i Robotyce \"INTEGRA\"",
            }

        response = client.post("/user/user_update",
            headers={"Authorization": f"Bearer {token}"
         }, json=payload
        )

        assert response.status_code == 200
        assert response.get_json() == {
            "message": "User updated successfully" }

        