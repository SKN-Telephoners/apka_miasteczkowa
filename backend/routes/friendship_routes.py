from flask import Blueprint, current_app
from backend.models import User, FriendRequest, Friendship
from backend.models.friend import FriendRequestStatus 
from backend.extensions import db,limiter
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required, get_current_user
from backend.helpers import validate_uuid
import uuid
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import or_, and_
import backend.notifications as notifications

friends_bp = Blueprint("friends", __name__, url_prefix="/api/friends")

@friends_bp.route("/request/<friend_id>/create", methods=["POST"])
@jwt_required()
@limiter.limit("300 per minute") #change to 30 before deployment
def create_friend_request(friend_id):
    user = get_current_user()
    friend_id = validate_uuid(friend_id)
    if friend_id is None:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid friend ID format")
    
    if User.query.filter_by(user_id=friend_id).first() is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Friend does not exist")
    
    if user.user_id == friend_id:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="You can't befriend yourself")
    
    existing_friend_request = FriendRequest.query.filter(
        or_(
            and_(FriendRequest.sender_id == user.user_id, FriendRequest.receiver_id == friend_id),
            and_(FriendRequest.sender_id == friend_id, FriendRequest.receiver_id == user.user_id),
        )
    ).first()

    if existing_friend_request is not None:
        return make_api_response(ResponseTypes.CONFLICT, message="Request already exists")
    existing_friendship = Friendship.query.filter(
        or_(
            and_(Friendship.user_id == user.user_id, Friendship.friend_id == friend_id),
            and_(Friendship.user_id == friend_id, Friendship.friend_id == user.user_id),
        )
    ).first()

    if existing_friendship is not None:
        return make_api_response(ResponseTypes.CONFLICT, message="Friendship already exists")

    try:
        new_request = FriendRequest(sender_id=user.user_id, receiver_id=friend_id)
        db.session.add(new_request)
        db.session.flush()
        
        notifications.friend_request_created.send(
            current_app._get_current_object(),
            from_user = user.user_id, 
            to_user = friend_id, 
            request_id=new_request.request_id
        )

    except IntegrityError:
        db.session.rollback()
        return make_api_response(ResponseTypes.CONFLICT, message="Request already exists")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    
    return make_api_response(ResponseTypes.CREATED, message="Friend request created")

@friends_bp.route("/request/<friend_id>/cancel", methods=["POST"])
@jwt_required()
@limiter.limit("300 per minute")
def cancel_friend_request(friend_id):
    user = get_current_user()
    friend_id = validate_uuid(friend_id)
    if friend_id is None:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid friend ID format")

    request = FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend_id).first()

    if request is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Such request doesn't exist")

    try:
        db.session.delete(request)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    return make_api_response(ResponseTypes.SUCCESS, message="Friend request cancelled", data={"friend_id": str(friend_id)})

@friends_bp.route("/request/<friend_id>/accept", methods=["POST"])
@jwt_required()
@limiter.limit("300 per minute") #change before deployment to 30
def accept_friend_request(friend_id):
    user = get_current_user()
    friend_id = validate_uuid(friend_id)
    if friend_id is None:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid friend ID format")

    request = FriendRequest.query.filter_by(sender_id=friend_id, receiver_id=user.user_id).first()

    if request is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Such request doesn't exist")

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
        return make_api_response(ResponseTypes.CONFLICT, message="Friendship already exists")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    return make_api_response(ResponseTypes.SUCCESS, message="Friend request accepted", data={"friend_id": str(friend_id)})

@friends_bp.route("/request/<friend_id>/decline", methods=["POST"])
@jwt_required()
@limiter.limit("300 per minute") #change before deployment to 30
def decline_friend_request(friend_id):
    user = get_current_user()
    friend_id = validate_uuid(friend_id)
    if friend_id is None:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid friend ID format")
    request = FriendRequest.query.filter_by(sender_id=friend_id, receiver_id=user.user_id).first()

    if request is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Such request doesn't exist")
    
    try:
        db.session.delete(request)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    return make_api_response(ResponseTypes.SUCCESS, message="Friend request declined")


@friends_bp.route("/request/pending", methods=["GET"])
@jwt_required()
def get_pending_requests():
    user = get_current_user()
    
    incoming_pending_requests = FriendRequest.query.filter_by(
        receiver_id=user.user_id,
        status=FriendRequestStatus.pending
    ).all()
    
    outgoing_pending_requests = FriendRequest.query.filter_by(
        sender_id=user.user_id,
        status=FriendRequestStatus.pending
    ).all()

    incoming_requests_data = []
    for req in incoming_pending_requests:
        sender = User.query.filter_by(user_id=req.sender_id).first()
        if sender:
            incoming_requests_data.append({
                "request_id": str(req.request_id),
                "sender_id": str(sender.user_id),
                "sender_username": sender.display_name,
                "requested_at": req.requested_at.isoformat()
            })

    outgoing_requests_data = []
    for req in outgoing_pending_requests:
        receiver = User.query.filter_by(user_id=req.receiver_id).first()
        if receiver:
            outgoing_requests_data.append({
                "request_id": str(req.request_id),
                "receiver_id": str(receiver.user_id), 
                "receiver_username": receiver.display_name, 
                "requested_at": req.requested_at.isoformat()
            })

    return make_api_response(
        ResponseTypes.SUCCESS, 
        message="Pending requests retrieved", 
        data={
            "incoming_pending_requests": incoming_requests_data,
            "outgoing_pending_requests": outgoing_requests_data 
        }
    )


@friends_bp.route("/list", methods=["GET"])
@jwt_required()
def get_friends_list():
    user= get_current_user()
    
    try:
        friendships = Friendship.query.filter(
            or_(
                Friendship.user_id == user.user_id,
                Friendship.friend_id == user.user_id
            )
        ).all()
        if not friendships:
            return make_api_response(ResponseTypes.SUCCESS, message="Empty friends list", data={"friends": []})

        friends_id=[]
        for friendship in friendships:
            if user.user_id==friendship.user_id:
                friends_id.append(friendship.friend_id)
            else:
                friends_id.append(friendship.user_id)
        friends = User.query.filter(User.user_id.in_(friends_id)).all()

        friends_data = []
        for friend in friends:
            friends_data.append({
                "id": str(friend.user_id),
                "username": friend.display_name
            })
        return make_api_response(ResponseTypes.SUCCESS, message="Friends list", data={"friends": friends_data})
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)