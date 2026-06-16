import pytest
from backend.routes.event_helpers import calculate_distance, get_friend_ids
from backend.models import User, Friendship
from backend.extensions import db

def test_calculate_distance():
    rynek_lat, rynek_lng = 50.0614, 19.9365
    agh_lat, agh_lng = 50.0665, 19.9135
    
    distance = calculate_distance(rynek_lat, rynek_lng, agh_lat, agh_lng)
    
    assert 1600 < distance < 1900
    assert calculate_distance(rynek_lat, rynek_lng, rynek_lat, rynek_lng) == 0

def test_get_friend_ids_logic(app, registered_user, registered_friend):
    with app.app_context():
        user, _ = registered_user
        friend, _ = registered_friend

        u_id, f_id = sorted([user.user_id, friend.user_id])
        db.session.add(Friendship(user_id=u_id, friend_id=f_id))
        db.session.commit()
        
        ids = get_friend_ids(user.user_id)
        assert friend.user_id in ids
        assert len(ids) == 1