from flask import Blueprint, request, url_for, current_app
from backend.models import User, FriendRequest, Friendship, Event, Comment
from backend.extensions import db, jwt, mail, limiter
from backend.constants import Constants
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt, get_jwt_identity, get_current_user, decode_token
from backend.helpers import add_token_to_db, revoke_token, is_token_revoked, revoke_all_user_tokens
from backend.tasks import send_email_async
import re
import uuid
from flask_mail import Message
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, and_

main = Blueprint("main", __name__)
auth = Blueprint("auth", __name__)

public_url = "example address"
@auth.route("/api/register",methods=["POST"])
@limiter.limit("500 per hour")   # for tests, 500 registers for IP per hour, change before deployment to 5
def register_user():    
    user_data = request.get_json()
    required_keys = {"username", "password", "email"}
    print(user_data)

    if not user_data or not required_keys.issubset(user_data.keys()):
        return make_api_response(ResponseTypes.BAD_REQUEST)
    
    username = user_data["username"]
    password = user_data["password"]
    email = user_data["email"]

    if (
        not re.match(Constants.EMAIL_PATTERN, email)
        or not re.match(Constants.USERNAME_PATTERN, username)
        or not len(email) < Constants.MAX_EMAIL_LEN
        or not Constants.MIN_USERNAME_LEN <= len(username) <= Constants.MAX_USERNAME_LEN
    ):
        return make_api_response(ResponseTypes.INVALID_DATA, message="Incorrect username or email")
    
    if not re.match(Constants.PASSWORD_PATTERN, password):
        return make_api_response(ResponseTypes.INVALID_DATA, message="Incorrect password format")
    
    
    new_user = User(username=username, password=password, email=email)
    if User.query.filter_by(username=username).first() is not None:
        return make_api_response(ResponseTypes.CONFLICT, message="Username already taken")
    if User.query.filter_by(email=email).first() is not None:
        return make_api_response(ResponseTypes.CONFLICT, message="Account with this email already exists")
    
    db.session.add(new_user)

    #send auth email
    auth_token = create_access_token(identity=email)
    auth_url=url_for("main.mail_auth", token=auth_token, _external=True)

    msg = Message(
            'Auth account',
            recipients=[email],
            body=f"Hello! Click the link to authorize your account: {auth_url}"
        )

    try:
        db.session.add(new_user)
        db.session.commit()
        mail.send(msg)
    except Exception as e:
        db.session.rollback()
        db.session.delete(new_user)
        db.session.commit()
        return make_api_response(ResponseTypes.SERVER_ERROR, message="Registration failed (mail eror)")
    
    return make_api_response(ResponseTypes.CREATED, message="Registration successful")

@auth.route("/api/login", methods=["POST"])
@limiter.limit("500 per 15 minutes")   # for tests, 500 logins for IP per 15 minutes, change before deployment to 5
def login_user():
    user_data = request.get_json()
    required_keys = {"username", "password"}
    
    if not user_data or not required_keys.issubset(user_data.keys()):
        return make_api_response(ResponseTypes.BAD_REQUEST)
    
    username = user_data["username"]
    password = user_data["password"]

    if (
        not isinstance(username, str)
        or not isinstance(password, str) 
        or len(username) > Constants.MAX_USERNAME_LEN
        or len(password) > Constants.MAX_PASSWORD_LEN
    ):

        return make_api_response(ResponseTypes.INVALID_CREDENTIALS)

    user = User.query.filter_by(username=username).first()
    if not user or not user.validate_password(password):
        return make_api_response(ResponseTypes.INVALID_CREDENTIALS)
    if not user.is_confirmed:
       return make_api_response(ResponseTypes.ACCOUNT_NOT_VERIFIED)
    
    limiter.reset()


    access_token = create_access_token(identity=user.user_id)
    refresh_token = create_refresh_token(identity=user.user_id)
    
    add_token_to_db(access_token)
    add_token_to_db(refresh_token)

    return make_api_response(ResponseTypes.LOGIN_SUCCESS, data={
        "user": {"username": user.username},
        "access_token": access_token,
        "refresh_token": refresh_token
    })

@main.route("/user", methods=["GET"])
@jwt_required()
def get_user_info():
    user = get_current_user()

    if not user:
        return make_api_response(ResponseTypes.NOT_FOUND, message="User not found")

    return make_api_response(ResponseTypes.SUCCESS, data={
        "user": {
            "username": user.username,
            "email": user.email
        }})

@auth.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    jti = get_jwt()["jti"]

    revoke_token(jti, identity)

    new_access_token = create_access_token(identity=identity)
    new_refresh_token = create_refresh_token(identity=identity)

    add_token_to_db(new_access_token)
    add_token_to_db(new_refresh_token)

    return make_api_response(ResponseTypes.SUCCESS, data={
        "access_token": new_access_token,
        "refresh_token": new_refresh_token
        })

@auth.route("/revoke_access", methods=["GET", "DELETE"])
@jwt_required()
def revoke_access_token():
    jti = get_jwt()["jti"]
    user_id = get_jwt_identity()
    revoked = revoke_token(jti, user_id)
    if not revoked:
        pass
    return make_api_response(ResponseTypes.TOKEN_REVOKED, message="Access token revoked")

@auth.route("/revoke_refresh", methods=["DELETE"])
@jwt_required(refresh=True)
def revoke_refresh_token():
    jti = get_jwt()["jti"]
    user_id = get_jwt_identity()
    revoke_token(jti, user_id)
    return make_api_response(ResponseTypes.TOKEN_REVOKED, message="Refresh token revoked")

@auth.route("/api/logout", methods=["DELETE"])
@jwt_required(refresh=True)
def logout():
    user_id = get_jwt_identity()
    refresh_jti = get_jwt()["jti"]
    revoke_token(refresh_jti, user_id)  

    data = request.get_json(silent=True)
    access_token = data.get("access_token") if data else None

    if access_token:
        try:
            access_payload = decode_token(access_token, allow_expired=True)
            if access_payload["sub"] == user_id:
                access_jti = access_payload["jti"]
                revoke_token(access_jti, user_id)
        except Exception:
            pass

    return make_api_response(ResponseTypes.LOGOUT_SUCCESS)

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return is_token_revoked(jwt_payload)

@jwt.unauthorized_loader
def unauthorized_callback(error):
    return make_api_response(ResponseTypes.UNAUTHORIZED)

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return make_api_response(ResponseTypes.INCORRECT_TOKEN)

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return make_api_response(ResponseTypes.INCORRECT_TOKEN, message="Expired token")

@jwt.user_lookup_loader
def load_user(jwt_header, jwt_payload):
    user_id = jwt_payload["sub"]
    return db.session.get(User, user_id)
  
@main.route("/reset_password_request", methods=["POST"])
@limiter.limit("500 per hour")   # for tests, 500 password resets for IP per hour, change before deployment to 5
def reset_password_request():
    user_data = request.get_json()
    email = user_data.get("email")
    
    if not email:
        return make_api_response(ResponseTypes.BAD_REQUEST)

    if not re.match(Constants.EMAIL_PATTERN, email):
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid email format")
    
    user = User.query.filter_by(email=email).first()  
    
    #now there will be multiple active tokens for password resetting (we don't want that) - to be fixed
    if user:
        reset_token = create_access_token(
            identity=user.user_id,
            expires_delta=timedelta(minutes=Constants.RESET_PASSWORD_EXPIRES),
            additional_claims={"type": "password_reset"}                              
        )
        try:
            add_token_to_db(reset_token)
        except Exception as e:
            current_app.logger.error(f"Failed to log reset token for user {user.user_id}: {e}")

        reset_url = url_for("main.reset_password", token=reset_token, _external=True) #this will have to be changed into deep link for app
        email_body = f"Hello! Click the link to reset your password: {reset_url}"
        
        try:
            send_email_async.delay('Reset password', email, email_body)
        except Exception as e:
            current_app.logger.error(f"Error sending email with password reset: {e}")

    return make_api_response(ResponseTypes.SUCCESS, message="If user with that email is present in the database the mail with password reset will be sent")

@main.route("/reset_password/<token>", methods=["POST"])
@limiter.limit("500 per hour")
def reset_password(token):
    decoded = None
    try:
        decoded = decode_token(token)
        is_revoked = is_token_revoked(decoded) 

        if is_revoked:
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Link has already been used or expired")
        
        if decoded.get("type") != "password_reset":
            return make_api_response(ResponseTypes.INCORRECT_TOKEN)
        
        user_id = decoded["sub"]

    except Exception:
        return make_api_response(ResponseTypes.UNAUTHORIZED)
    
    user = User.query.filter_by(user_id=user_id).first()

    if not user:
        return make_api_response(ResponseTypes.NOT_FOUND, message="User not found")
    
    data = request.get_json()
    if not data or "new_password" not in data:
        return make_api_response(ResponseTypes.INVALID_CREDENTIALS, message="Missing new_password")
    
    new_password = data["new_password"]
    if not re.match(Constants.PASSWORD_PATTERN, new_password):
        return make_api_response(ResponseTypes.INVALID_CREDENTIALS, message="Incorrect password format")
    
    user.update_password(new_password)
    db.session.commit()

    try:
        revoke_token(decoded["jti"], decoded["sub"])
        revoke_all_user_tokens(user.user_id)
    except Exception as e:
        current_app.logger.error(f"Failed to revoke all tokens after password reset: {e}")

    return make_api_response(ResponseTypes.SUCCESS, message="Password changed successfully")

@main.route("/create_friend_request/<friend_id>", methods=["POST"])
@jwt_required()
@limiter.limit("300 per minute") #chenge to 30 before deployment
def create_friend_request(friend_id):
    user = get_current_user()
    try:
        friend_id = uuid.UUID(friend_id)
    except ValueError:
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
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return make_api_response(ResponseTypes.CONFLICT, message="Request already exists")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    
    return make_api_response(ResponseTypes.CREATED, message="Friend request created")

@main.route("/cancel_friend_request/<friend_id>", methods=["POST"])
@jwt_required()
@limiter.limit("300 per minute")
def cancel_friend_request(friend_id):
    user = get_current_user()

    try:
        friend_id = uuid.UUID(friend_id)
    except ValueError:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid friend ID format")

    request = FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend_id).first()

    if request is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Such request doesn't exist")

    try:
        db.session.delete(request)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Friend request cancelled", data={"friend_id": str(friend_id)})

@main.route("/accept_friend_request/<friend_id>", methods=["POST"])
@jwt_required()
@limiter.limit("300 per minute") #change before deployment to 30
def accept_friend_request(friend_id):
    user = get_current_user()
    try:
        friend_id = uuid.UUID(friend_id)
    except ValueError:
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
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Friend request accepted", data={"friend_id": str(friend_id)})

@main.route("/decline_friend_request/<friend_id>", methods=["POST"])
@jwt_required()
@limiter.limit("300 per minute") #change before deployment to 30
def decline_friend_request(friend_id):
    user = get_current_user()
    try:
        friend_id = uuid.UUID(friend_id)
    except Exception:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid friend ID format")
    request = FriendRequest.query.filter_by(sender_id=friend_id, receiver_id=user.user_id).first()

    if request is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Such request doesn't exist")
    
    try:
        db.session.delete(request)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    
    return make_api_response(ResponseTypes.SUCCESS, message="Friend request declined")

@main.route("/get_friends_list", methods=["GET"])
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
            "id": friend.user_id,
            "username": friend.username
        })
    return make_api_response(ResponseTypes.SUCCESS, message="Friends list", data={"friends": friends_data})
    
@main.route("/create_event", methods=["POST"])
@limiter.limit("100 per minute")
@jwt_required()
def create_event():
    user = get_current_user()

    event_data = request.get_json()
    required_keys = {"name", "description", "date", "time", "location"}

    if not event_data or not required_keys.issubset(event_data.keys()):
        current_app.logger.error("dupa")
        return make_api_response(ResponseTypes.BAD_REQUEST)
    
    name = event_data.get("name", "").strip()
    description = event_data.get("description", "").strip()
    date_str = event_data.get("date")
    time_str = event_data.get("time")
    location = event_data.get("location", "").strip()

    if not (Constants.MIN_EVENT_NAME <= len(name) <= Constants.MAX_EVENT_NAME):
        return make_api_response(ResponseTypes.INVALID_DATA, message="Event name must be between 3 and 32 characters")
        
    if len(location) > Constants.MAX_LOCATION_LEN:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Location name is too long")
        
    if len(description) > Constants.MAX_DESCRIPTION_LEN:
         return make_api_response(ResponseTypes.INVALID_DATA, message="Description is too long")

    try:
        dt_string = f"{date_str} {time_str}"
        date_and_time = datetime.strptime(dt_string, "%d.%m.%Y %H:%M")
        date_and_time = date_and_time.replace(tzinfo=timezone.utc)
        
        if date_and_time <= datetime.now(timezone.utc):
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Event date must be in the future")
             
    except ValueError:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid date format. Use DD.MM.YYYY and HH:MM")

    
    new_event = Event(
        name=name,
        description=description,
        date_and_time=date_and_time,
        location=location,
        creator_id=user.user_id
    )
    try:
        db.session.add(new_event)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.CREATED, message="Event created successfully", data={"event_id": new_event.event_id})

@main.route("/delete_event/<event_id>", methods=["DELETE"])
@jwt_required()
def delete_event(event_id):
    user = get_current_user()
    try:
        event_id = uuid.UUID(event_id)
    except Exception:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid event ID format")
    
    event = Event.query.filter_by(event_id=event_id).first()

    if event is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Event doesn't exist")

    if user.user_id != event.creator_id:
        return make_api_response(ResponseTypes.FORBIDDEN, message="You can delete your own events only")
    try:
        db.session.delete(event)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Event deleted successfully")


@main.route("/feed",methods=["GET"])
def feed():

    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=20, type=int)
    sort=request.args.get("sort",default=1,type=int)
    
    if sort==1:
        events=Event.query \
            .order_by(Event.date_and_time.asc())
    elif sort==2:
        events=Event.query \
            .order_by(Event.date_and_time.desc())
    
    pagination = events.paginate(page=page, per_page=limit, error_out=False)
    
    event_list=[
        {
            "id": event.event_id,
            "name": event.name,
            "description": event.description,
            "date": event.date_and_time.strftime("%d.%m.%Y"),
            "time": event.date_and_time.strftime("%H:%M"),
            "location": event.location,
            "creator_id": event.creator_id
        }
        for event in pagination.items
    ]

    return make_api_response(ResponseTypes.SUCCESS, data={
        "data": event_list,
        "pagination": {
            "page": pagination.page,
            "limit": limit,
            "total": pagination.total,
            "pages": pagination.pages
        }
    })

@main.route("/mail_auth_request",methods=["POST"])
def mail_auth_request():
    user_data = request.get_json()
    
    if not user_data or not "email" in user_data.keys():
        return make_api_response(ResponseTypes.BAD_REQUEST)
    
    email=user_data["email"]

    user = User.query.filter_by(email=email).first()

    if not user:
        return make_api_response(ResponseTypes.NOT_FOUND, message="There is no user with such email")

    if user.is_confirmed:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="User already confirmed")
    
    auth_token = create_access_token(identity=user.email)

    auth_url=url_for("main.mail_auth", token=auth_token, _external=True)
        
    msg = Message(
            'Auth account',
            recipients=[email],
            body=f"Hello! Click the link to authorize your account: {auth_url}"
        )

    mail.send(msg)
    return make_api_response(ResponseTypes.SUCCESS, message="Email sent successfully")

@main.route("/mail_auth/<token>",methods=["POST"])
def mail_auth(token):
    decoded = decode_token(token)
    user_email = decoded["sub"]

    user = User.query.filter_by(email=user_email).first()

    if not user:
        return make_api_response(ResponseTypes.NOT_FOUND, message="User not found")

    if user.is_confirmed:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="User already confirmed")
    
    user.is_confirmed=True
    db.session.commit()

    return make_api_response(ResponseTypes.SUCCESS, message="Verification succesful")

@main.route("/create_comment/<event_id>", methods=["POST"])
@jwt_required()
def create_comment(event_id):
    user = get_current_user()
    event_id = uuid.UUID(event_id)

    event = Event.query.filter_by(event_id=event_id)

    if event is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Event doesn't exist")
    
    comment_data = request.get_json()
    required_keys = {"content"}
    
    if not comment_data or not required_keys.issubset(comment_data.keys()):
        return make_api_response(ResponseTypes.BAD_REQUEST)
    new_comment = Comment(user_id=user.user_id, event_id=event_id, content=comment_data["content"])

    db.session.add(new_comment)
    db.session.commit()

    return make_api_response(ResponseTypes.CREATED, message="Comment created successfully")

@main.route("/delete_comment/<comment_id>", methods=["DELETE"])
@jwt_required()
def delete_comment(comment_id):
    user = get_current_user()
    try:
        comment_id = uuid.UUID(comment_id)
    except ValueError:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid UUID format")
    
    comment = Comment.query.filter_by(comment_id=comment_id).first()
    if comment is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Comment doesn't exist")

    if user.user_id != comment.user_id:
        return make_api_response(ResponseTypes.FORBIDDEN, message="You can delete your own comments only")
        
    comment.soft_delete()
    db.session.commit()

    return make_api_response(ResponseTypes.SUCCESS, message="Comment deleted successfully")

@main.route("/edit_comment/<comment_id>", methods=["POST", "GET"])
@jwt_required()
def edit_comment(comment_id):
    user = get_current_user()
    comment_id = uuid.UUID(comment_id)
    comment = Comment.query.filter_by(comment_id=comment_id).first()

    if comment is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Comment doesn't exist")

    if user.user_id != comment.user_id:
        return make_api_response(ResponseTypes.FORBIDDEN, message="You can edit your own comments only")
        
    data = request.get_json()
    new_content = data["new_content"]
    comment.content = new_content
    comment.edited = True
    db.session.commit()

    return make_api_response(ResponseTypes.SUCCESS, message="Comment edited successfully")

@main.route("/reply_to_comment/<parent_comment_id>", methods=["POST"])
@jwt_required()
def reply_to_comment(parent_comment_id):
    user = get_current_user()
    parent_comment_id = uuid.UUID(parent_comment_id)
    parent_comment = Comment.query.filter_by(comment_id=parent_comment_id).first()

    if parent_comment is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Parent comment doesn't exist")
    
    comment_data = request.get_json()
    required_keys = {"content"}
    
    if not comment_data or not required_keys.issubset(comment_data.keys()):
        return make_api_response(ResponseTypes.BAD_REQUEST)
    
    new_comment = Comment(
        user_id=user.user_id,
        event_id=parent_comment.event_id,
        content=comment_data["content"],
        parent_comment_id=parent_comment_id
        )

    db.session.add(new_comment)
    db.session.commit()

    return make_api_response(ResponseTypes.CREATED, message="Comment created successfully")

@main.route("/get_comments_list/<event_id>", methods=["GET"])
@jwt_required()
def get_comments_list(event_id):

    comments = Comment.query.filter_by(event_id=event_id).order_by(Comment.created_at.asc()).all()

    if not comments:
        return make_api_response(ResponseTypes.SUCCESS, message="Empty comments list", data={"comments": []})
    top_level_comments = [c for c in comments if c.parent_comment_id is None]
    comments_tree = [c.to_dict() for c in top_level_comments]

    return make_api_response(ResponseTypes.SUCCESS, message="Comments list", data={"comments": comments_tree})