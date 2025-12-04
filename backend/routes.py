from flask import Blueprint, request, jsonify, url_for
from backend.models import User, FriendRequest, Friendship, Event
from backend.extensions import db, jwt, mail, limiter
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt, get_jwt_identity, get_current_user, decode_token
from backend.helpers import add_token_to_db, revoke_token, is_token_revoked
import re
import uuid
from flask_mail import Message
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import IntegrityError

MAX_EMAIL_LEN = 320
MAX_USERNAME_LEN = 32
MIN_USERNAME_LEN = 3

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
        return jsonify({"message": "Bad request"}), 400
    
    username = user_data["username"]
    password = user_data["password"]
    email = user_data["email"]

    email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    username_pattern = r"^[A-Za-z0-9_.'-]+$"
    password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,72}$" #72 bytes is a max input for bcrypt hash function

    if (
        not re.match(email_pattern, email)
        or not re.match(username_pattern, username)
        or not len(email) < MAX_EMAIL_LEN
        or not MIN_USERNAME_LEN <= len(username) <= MAX_USERNAME_LEN
    ):
        return jsonify({"message": "Invalid username or email"}), 400
    
    if not re.match(password_pattern, password):
        return jsonify({"message": "Incorrect password format"}), 400
    
    new_user = User(username=username, password=password, email=email)
    if User.query.filter_by(username=username).first() is not None:
        return jsonify({"message": "Username already taken"}), 409
    if User.query.filter_by(email=email).first() is not None:
        return jsonify({"message": "Account with this email already exists"}), 409
    
    db.session.add(new_user)
    db.session.commit()
    print("Dodano użytkownika do bazy!")
    
    return {
        "message": "Registration successful",
    }, 200

@auth.route("/api/login", methods=["POST"])
@limiter.limit("500 per 15 minutes")   # for tests, 500 logins for IP per 15 minutes, change before deployment to 5
def login_user():
    user_data = request.get_json()
    required_keys = {"username", "password"}
    
    if not user_data or not required_keys.issubset(user_data.keys()):
        return jsonify({"message": "Bad request"}), 400
    
    username = user_data["username"]
    password = user_data["password"]

    if (
        not isinstance(username, str)
        or not isinstance(password, str) 
        or len(username) > MAX_USERNAME_LEN
        or len(password) > 128
    ):
        return jsonify({"message" : "Incorrect username or password"}), 401

    user = User.query.filter_by(username=username).first()
    if not user or not user.validate_password(password):
        return jsonify({"message": "Invalid username or password"}), 401
    
    limiter.reset()


    access_token = create_access_token(identity=user.user_id)
    refresh_token = create_refresh_token(identity=user.user_id)
    
    add_token_to_db(access_token)
    add_token_to_db(refresh_token)

    return {
        "message": "Login successful",
        "user": {
            "username": user.username,
        },
        "access_token": access_token,
        "refresh_token": refresh_token
    }, 200

@main.route("/user", methods=["GET"])
@jwt_required()
def get_user_info():
    user = get_current_user()

    if not user:
        return jsonify({"message": "User not found"}), 404

    return {
        "user": {
            "username": user.username,
            "email": user.email
        },
    }, 200

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
    
    return jsonify({
        "access_token": new_access_token,
        "refresh_token": new_refresh_token
    }), 200

@auth.route("/revoke_access", methods=["GET", "DELETE"])
@jwt_required()
def revoke_access_token():
    jti = get_jwt()["jti"]
    user_id = get_jwt_identity()
    revoke_token(jti, user_id)
    return jsonify(message="Access token revoked")

@auth.route("/revoke_refresh", methods=["DELETE"])
@jwt_required(refresh=True)
def revoke_refresh_token():
    jti = get_jwt()["jti"]
    user_id = get_jwt_identity()
    try:
        revoke_token(jti, user_id)
    except Exception:
        db.session.rollback()
    return jsonify(message="Refresh token revoked")

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
            db.session.rollback()
            
    return jsonify(message="Logged out successfully"), 200

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    try:
        return is_token_revoked(jwt_payload)
    except Exception:
        db.session.rollback()
        return True

@jwt.unauthorized_loader
def unauthorized_callback(error):
    return jsonify(message="Missing or invalid token"), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify(message="Incorrect token"), 401

@jwt.expired_token_loader
def expired_token_callback(expired_token):
    return jsonify(message="Token expired"), 401

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
        return jsonify({"message": "Bad request"}), 400

    email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if not re.match(email_pattern, email):
        return jsonify({"message": "Invalid email format"})
        
    user = User.query.filter_by(email=email).first()  
    
    #now there will be multiple active tokens for password resetting (we don't want that) - to be fixed
    if user:
        reset_token = create_access_token(
            identity=user.email,
            expires_delta=timedelta(minutes=15),
            additional_claims={"type": "password_reset"}                              
        )

        reset_url = url_for("main.reset_password", token=reset_token, _external=True) #this will have to be changed into deep link to app

        msg = Message(
            'Reset password',
            recipients=[email],
            body=f"Hello! Click the link to reset your password: {reset_url}"
        )
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Error sending email with password reset: {e}")

    return {
        "message": "If user with that email is present in the database the "
    }, 200

@main.route("/reset_password/<token>", methods=["POST"])
@limiter.limit("500 per hour")
def reset_password(token):
    decoded = None
    try:
        decoded = decode_token(token)
        is_revoked = False
        try:
            if is_token_revoked(decoded):
                is_revoked = True
        except Exception:
            db.session.rollback()
            is_revoked = False
            
        if is_revoked:
             return jsonify({"message": "Link has already been used or expired"}), 400
        
        if decoded.get("type") != "password_reset":
            return jsonify({"message": "Invalid token type"}), 400
        
        user_email = decoded["sub"]

    except Exception:
        db.session.rollback()
        return jsonify({"message": "Invalid or expired token"}), 400
    
    user = User.query.filter_by(email=user_email).first()

    if not user:
        return jsonify({"message": "User not found"}), 404
    
    data = request.get_json()
    if not data or "new_password" not in data:
        return jsonify({"message": "Missing new_password"}), 400
    
    password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,72}$"
    new_password = data["new_password"]
    if not re.match(password_pattern, new_password):
        return jsonify({"message": "Incorrect password format"}), 400
    
    user.update_password(new_password)
    db.session.commit()

    if decoded:
        try:
            add_token_to_db(token)
            revoke_token(decoded["jti"], decoded["sub"])
        except Exception:
            db.session.rollback()

    return jsonify({
        "message": "Password changed successfully"
    }), 200

@main.route("/create_friend_request/<friend_id>", methods=["POST"])
@jwt_required()
@limiter.limit("300 per minute") #chenge to 30 before deployment
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
    
    if (FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend_id).first() is not None
        or FriendRequest.query.filter_by(sender_id=friend_id, receiver_id=user.user_id).first()):
        return {
            "message": "Request already exists",
        }, 409
    
    if (Friendship.query.filter_by(user_id=user.user_id, friend_id=friend_id).first() is not None
        or Friendship.query.filter_by(user_id=friend_id, friend_id=user.user_id).first() is not None):
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

@main.route("/accept_friend_request/<friend_id>", methods=["POST"])
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

@main.route("/decline_friend_request/<friend_id>", methods=["POST"])
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

@main.route("/create_event", methods=["POST"])
@limiter.limit("100 per minute")
@jwt_required()
def create_event():
    user = get_current_user()

    event_data = request.get_json()
    required_keys = {"name", "description", "date", "time", "location"}

    if not event_data or not required_keys.issubset(event_data.keys()):
        return jsonify({"message": "Bad request"}), 400
    
    name = event_data.get("name", "").strip()
    description = event_data.get("description", "").strip()
    date_str = event_data.get("date")
    time_str = event_data.get("time")
    location = event_data.get("location", "").strip()

    if not (3 <= len(name) <= 32):
        return jsonify({"message": "Event name must be between 3 and 32 characters"}), 400
        
    if len(location) > 32:
        return jsonify({"message": "Location name is too long (max 32 chars)"}), 400
        
    if len(description) > 1000:
         return jsonify({"message": "Description is too long (max 1000 chars)"}), 400

    try:
        dt_string = f"{date_str} {time_str}"
        date_and_time = datetime.strptime(dt_string, "%d.%m.%Y %H:%M")
        date_and_time = date_and_time.replace(tzinfo=timezone.utc)
        
        if date_and_time <= datetime.now(timezone.utc):
             return jsonify({"message": "Event date must be in the future"}), 400
             
    except ValueError:
        return jsonify({"message": "Invalid date format. Use DD.MM.YYYY and HH:MM"}), 400

    try:
        new_event = Event(
            name=name,
            description=description,
            date_and_time=date_and_time,
            location=location,
            creator_id=user.user_id
        )
    
        db.session.add(new_event)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({"message": "Internal server error"}), 500
    
    return {
        "message": "Event created successfully",
        "event_id": new_event.event_id
    }, 200

@main.route("/delete_event/<event_id>", methods=["DELETE"])
@jwt_required()
def delete_event(event_id):
    user = get_current_user()
    try:
        event_id = uuid.UUID(event_id)
    except Exception:
        return jsonify({"message": "Invalid event ID format"}), 400
    
    event = Event.query.filter_by(event_id=event_id).first()

    if event is None:
        return {
            "message": "Event doesn't exist"
        }, 404

    if user.user_id != event.creator_id:
        return {
            "message": "You can delete your own events only"
        }, 403
    
    try:
        db.session.delete(event)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({"message": "Internal server error"}), 500

    return jsonify ({
        "message": "Event deleted successfully"
    }), 200


@main.route("/feed",methods=["GET"])
def feed():

    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=20, type=int)
    
    events=Event.query \
        .order_by(Event.date_and_time.asc())
    
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

    return jsonify({
        "data": event_list,
        "pagination": {
            "page": pagination.page,
            "limit": limit,
            "total": pagination.total,
            "pages": pagination.pages
        }
    }) ,200
