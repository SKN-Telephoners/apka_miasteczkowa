from flask import Blueprint, jsonify
from backend.models import User, FriendRequest, Friendship
from backend.extensions import db, limiter
from flask_jwt_extended import jwt_required, get_current_user
import uuid
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, and_

friends_bp = Blueprint("friends", __name__, url_prefix="/api/friends")

@friends_bp.route("/request/<friend_id>/create", methods=["POST"])
@jwt_required()
@limiter.limit("300 per minute") #change to 30 before deployment
def create_friend_request(friend_id):
    user = get_current_user()
    try:
        friend_id = uuid.UUID(friend_id)
    except ValueError:
        return jsonify({"message": "Invalid friend ID format"}), 400
    
    if User.query.filter_by(user_id=friend_id).first() is None:
        return {
            "message": "Friend does not exist",
        }, 404
    
    if user.user_id == friend_id:
        return {
            "message": "You can't befriend yourself",
        }, 400
    
    existing_friend_request = FriendRequest.query.filter(
        or_(
            and_(FriendRequest.sender_id == user.user_id, FriendRequest.receiver_id == friend_id),
            and_(FriendRequest.sender_id == friend_id, FriendRequest.receiver_id == user.user_id),
        )
    ).first()

    if existing_friend_request is not None:
        return {
            "message": "Request already exists",
        }, 409
    
    existing_friendship = Friendship.query.filter(
        or_(
            and_(Friendship.user_id == user.user_id, Friendship.friend_id == friend_id),
            and_(Friendship.user_id == friend_id, Friendship.friend_id == user.user_id),
        )
    ).first()

    if existing_friendship is not None:
        return {
            "message": "Friendship already exists",
        }, 409

    try:
        new_request = FriendRequest(sender_id=user.user_id, receiver_id=friend_id)
        db.session.add(new_request)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Request already exists"}), 409
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({"message": "Internal server error"}), 500
    
    return {
        "message": "Friend request created",
    }, 200

@friends_bp.route("/request/<friend_id>/cancel", methods=["POST"])
@jwt_required()
@limiter.limit("300 per minute")
def cancel_friend_request(friend_id):
    user = get_current_user()

    try:
        friend_id = uuid.UUID(friend_id)
    except ValueError:
        return jsonify({"message": "Invalid friend ID format"}), 400

    request = FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend_id).first()

    if request is None:
        return {
            "message": "Such request doesn't exist",
        }, 404

    try:
        db.session.delete(request)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({"message": "Internal server error"}), 500
    
    return jsonify({
        "message": "Friend request cancelled",
        "friend_id": str(friend_id)
    }), 200

@friends_bp.route("/request/<friend_id>/accept", methods=["POST"])
@jwt_required()
@limiter.limit("300 per minute") #change before deployment to 30
def accept_friend_request(friend_id):
    user = get_current_user()
    try:
        friend_id = uuid.UUID(friend_id)
    except ValueError:
        return jsonify({"message": "Invalid friend ID format"}), 400

    request = FriendRequest.query.filter_by(sender_id=friend_id, receiver_id=user.user_id).first()

    if request is None:
        return {
            "message": "Such request doesn't exist",
        }, 400

    if user.user_id < friend_id:
        new_friendship = Friendship(user_id=user.user_id, friend_id=friend_id)
    else:
        new_friendship = Friendship(user_id=friend_id, friend_id=user.user_id)

    try:
        db.session.delete(request)
        db.session.add(new_friendship)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Friendship already exists"}), 409
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({"message": "Internal server error"}), 500
    
    return jsonify({
        "message": "Friend request accepted",
        "friend_id": str(friend_id)
    }), 200

@friends_bp.route("/request/<friend_id>/decline", methods=["POST"])
@jwt_required()
@limiter.limit("300 per minute") #change before deployment to 30
def decline_friend_request(friend_id):
    user = get_current_user()
    try:
        friend_id = uuid.UUID(friend_id)
    except Exception:
        return jsonify({"message": "Invalid friend ID format"}), 400
    request = FriendRequest.query.filter_by(sender_id=friend_id, receiver_id=user.user_id).first()

    if request is None:
        return {
            "message": "Such request doesn't exist",
        }, 404
    
    try:
        db.session.delete(request)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({"message": "Internal server error"}), 500
        
    return {
        "message": "Friend request declined",
    }, 200

@friends_bp.route("/list", methods=["GET"])
@jwt_required()
def get_friends_list():
    user= get_current_user()
    
    friendships = Friendship.query.filter(
        or_(
            Friendship.user_id == user.user_id,
            Friendship.friend_id == user.user_id
        )
    ).all()
    if not friendships:
        return jsonify({
            "message": "Empty friends list",
            "friends": []
        }), 200
    friends_id=[]
    for friendship  in friendships:
        if user.user_id==friendship.user_id :
            friends_id.append(friendship.friend_id)
        else:
            friends_id.append(friendship.user_id)

    friends = User.query.filter(User.user_id.in_(friends_id)).all()

    friends_data = []
    for friend in friends:
        friends_data.append({
            "id": friend.user_id,
            "username": friend.username
        })
    return jsonify({
        "message": "Friends list",
        "friends": friends_data
    }), 200