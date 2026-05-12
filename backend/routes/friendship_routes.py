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

'''
Input: URL Parameter <uuid:friend_id>
Action: Creates a friend request record and triggers an asynchronous notification task
Data sent to the frontend: {"message": "Friend request created"}
Output: 201 Created (or 400/404/409/500 on error)
'''
@friends_bp.route("/request/<friend_id>/create", methods=["POST"])
@jwt_required()
@limiter.limit("300 per minute") #change to 30 before deployment
def create_friend_request(friend_id):
    user = get_current_user()
    friend_id = validate_uuid(friend_id)
    if friend_id is None:
        current_app.logger.warning(f"WARNING: /create_friend_request, user of ID {friend_id} does not exist")
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid friend ID format")
    
    if User.query.filter_by(user_id=friend_id).first() is None:
        current_app.logger.warning(f"WARNING: /create_friend_request, user of ID {friend_id} does not exist")
        return make_api_response(ResponseTypes.NOT_FOUND, message="Friend does not exist")
    
    if user.user_id == friend_id:
        current_app.logger.warning(f"WARNING: /create_friend_request, user of ID {friend_id} tried to befriend himself")
        return make_api_response(ResponseTypes.BAD_REQUEST, message="You can't befriend yourself")
    
    existing_friend_request = FriendRequest.query.filter(
        or_(
            and_(FriendRequest.sender_id == user.user_id, FriendRequest.receiver_id == friend_id),
            and_(FriendRequest.sender_id == friend_id, FriendRequest.receiver_id == user.user_id),
        )
    ).first()

    if existing_friend_request is not None:
        current_app.logger.warning(f"WARNING: /create_friend_request, user of ID {user.user_id} tried to sent friend request that already exists")
        return make_api_response(ResponseTypes.CONFLICT, message="Request already exists")
    existing_friendship = Friendship.query.filter(
        or_(
            and_(Friendship.user_id == user.user_id, Friendship.friend_id == friend_id),
            and_(Friendship.user_id == friend_id, Friendship.friend_id == user.user_id),
        )
    ).first()

    if existing_friendship is not None:
        current_app.logger.warning(f"WARNING: /create_friend_request, user of ID {user.user_id} tried to befriend a user that is his friend already")
        return make_api_response(ResponseTypes.CONFLICT, message="Friendship already exists")

    try:
        new_request = FriendRequest(sender_id=user.user_id, receiver_id=friend_id)
        db.session.add(new_request)
        db.session.commit()
        
        notifications.friend_request_created.send(
            current_app._get_current_object(),
            from_user = user.user_id, 
            to_user = friend_id, 
            request_id=new_request.request_id
        )

    except IntegrityError:
        db.session.rollback()
        current_app.logger.warning(f"WARNING: /create_friend_request, user of ID {user.user_id} tried to sent friend request that already exists")
        return make_api_response(ResponseTypes.CONFLICT, message="Request already exists")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /create_friend_request, DB exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    
    current_app.logger.info(f"INFO: /create_friend_request, user of ID {user.user_id} created friend request for user: {friend_id}")
    return make_api_response(ResponseTypes.CREATED, message="Friend request created")

'''
Input: URL Parameter <uuid:friend_id>, Header { "Authorization": "Bearer <Access_Token>" }
Action: Locates a friend request sent by the current user to the specified friend_id. If found, the request is deleted from the database, canceling it
Data sent to the frontend: {"message": "Friend request cancelled", "friend_id": <str>}
Output: 200 OK (or 404/400/500 on error)
'''
@friends_bp.route("/request/<friend_id>/cancel", methods=["POST"])
@jwt_required()
@limiter.limit("300 per minute")
def cancel_friend_request(friend_id):
    user = get_current_user()
    friend_id = validate_uuid(friend_id)
    if friend_id is None:
        current_app.logger.warning(f"WARNING: /cancel_friend_request, user of ID {user.user_id} tried to cancel request for non existant user: {friend_id}")
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid friend ID format")

    request = FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend_id).first()

    if request is None:
        current_app.logger.warning(f"WARNING: /cancel_friend_request, user of ID {user.user_id} tried to cancel request that does not exist")
        return make_api_response(ResponseTypes.NOT_FOUND, message="Such request doesn't exist")

    try:
        db.session.delete(request)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /cancel_friend_request, DB exception occured {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    current_app.logger.info(f"INFO: /cancel_friend_request, friend request {user.user_id} -> {friend_id} cancelled")
    return make_api_response(ResponseTypes.SUCCESS, message="Friend request cancelled", data={"friend_id": str(friend_id)})

'''
Input: URL Parameter <uuid:friend_id>, Header { "Authorization": "Bearer <Access_Token>" }
Action: Finds an incoming friend request from the specified friend_id. It deletes the request record and creates a new Friendship record. The user_id and friend_id are stored in a specific order (lesser ID first) to ensure uniqueness in the database
Data sent to the frontend: {"message": "Friend request accepted", "friend_id": <str>}
Output: 200 OK (or 404/400/409/500 on error)
'''
@friends_bp.route("/request/<friend_id>/accept", methods=["POST"])
@jwt_required()
@limiter.limit("300 per minute") #change before deployment to 30
def accept_friend_request(friend_id):
    user = get_current_user()
    friend_id = validate_uuid(friend_id)
    if friend_id is None:
        current_app.logger.warning(f"WARNING: /accept_friend_request, user of ID {user.user_id} tried to accept friend request from non existant user: {friend_id}")
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid friend ID format")

    request = FriendRequest.query.filter_by(sender_id=friend_id, receiver_id=user.user_id).first()

    if request is None:
        current_app.logger.warning(f"WARNING: /accept_friend_request, user of ID {user.user_id} tried to accept friend request that does not exist")
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
        current_app.logger.warning(f"WARNING: /accept_friend_request, user of ID {user.user_id} tried to accept friend request for friendship that already exist")
        return make_api_response(ResponseTypes.CONFLICT, message="Friendship already exists")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /accept_friend_request, DB exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    current_app.logger.info(f"INFO: /accept_friend_request, user {user.user_id} accepted friend request")
    return make_api_response(ResponseTypes.SUCCESS, message="Friend request accepted", data={"friend_id": str(friend_id)})

'''
Input: URL Parameter <uuid:friend_id>, Header { "Authorization": "Bearer <Access_Token>" }
Action: Identifies an incoming friend request from the specified friend_id and deletes the record from the database, effectively rejecting the request :((
Data sent to the frontend: {"message": "Friend request declined"}
Output: 200 OK (or 404/400/500 on error)
'''
@friends_bp.route("/request/<friend_id>/decline", methods=["POST"])
@jwt_required()
@limiter.limit("300 per minute") #change before deployment to 30
def decline_friend_request(friend_id):
    user = get_current_user()
    friend_id = validate_uuid(friend_id)
    if friend_id is None:
        current_app.logger.warning(f"WARNING: /decline_friend_request, user of ID {user.user_id} tried to decline friend request from non existant user: {friend_id}")
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid friend ID format")
    request = FriendRequest.query.filter_by(sender_id=friend_id, receiver_id=user.user_id).first()

    if request is None:
        current_app.logger.warning(f"WARNING: /decline_friend_request, user of ID {user.user_id} tried to decline friend request that does not exist")
        return make_api_response(ResponseTypes.NOT_FOUND, message="Such request doesn't exist")
    
    try:
        db.session.delete(request)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /decline_friend_request, DB exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    current_app.logger.info(f"INFO: /decline_friend_request, user {user.user_id} declined friend request")
    return make_api_response(ResponseTypes.SUCCESS, message="Friend request declined")


'''
Input: Header { "Authorization": "Bearer <Access_Token>" }
Action: Queries the database for all friend requests where the current user is either the sender (outgoing) or the receiver (incoming) that have a "pending" status
Data sent to the frontend: {
"incoming_pending_requests": [{
    "request_id": <str>, 
    "sender_id": <str>, 
    "sender_username": <str>,
    "requested_at": <iso_date>}], 
"outgoing_pending_requests": [{
    "request_id": <str>, 
    "receiver_id": <str>, 
    "receiver_username": <str>, 
    "requested_at": <iso_date>}], 
    "message": "Pending requests retrieved"}
Output: 200 OK (or 500 on error)
'''
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

    current_app.logger.info(f"INFO: /get_pending_friend_requests, success in retrieving pending friend requests")
    return make_api_response(
        ResponseTypes.SUCCESS, 
        message="Pending requests retrieved", 
        data={
            "incoming_pending_requests": incoming_requests_data,
            "outgoing_pending_requests": outgoing_requests_data 
        }
    )

'''
Input: Header { "Authorization": "Bearer <Access_Token>" }
Action: Fetches the list of all confirmed friends for the logged-in user
Data sent to the frontend: {"friends": [{"id": <uuid>, "username": <str>}], "message": "Friends list"}
Output: 200 OK (or 500 on error)
'''
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
            current_app.logger.info(f"INFO: /get_friends_list, success in retrieving friends list - no friends :( ")
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
        current_app.logger.info(f"INFO: /get_friends_list, success in retrieving friends list")
        return make_api_response(ResponseTypes.SUCCESS, message="Friends list", data={"friends": friends_data})
    except SQLAlchemyError as e:
        current_app.logger.error(f"ERROR: /get_friends_list, DB exception occured {e} ")
        return make_api_response(ResponseTypes.SERVER_ERROR)