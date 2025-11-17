from flask import Blueprint, request, jsonify, url_for
from backend.models import User, TokenBlocklist, FriendRequest, Friendship, Event, Comment
from backend.extensions import db, jwt, mail, limiter
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt, get_jwt_identity, get_current_user, decode_token
from backend.helpers import add_token_to_db, revoke_token, is_token_revoked
from datetime import timedelta, datetime
import re
import uuid
from flask_mail import Message
from datetime import datetime, timezone

MAX_EMAIL_LEN = 320
MAX_USERNAME_LEN = 32
MIN_USERNAME_LEN = 3

main = Blueprint("main", __name__)
auth = Blueprint("auth", __name__)
events = Blueprint("events", __name__)

@events.route("/events", methods=["GET"])
def get_events():
    """
    Zwraca listę wszystkich eventów w bazie.
    """

    events = Event.query.order_by(Event.date).all()
    result =  [event.to_dict() for event in events]
    return jsonify(result), 200

@events.route("/events", methods=["POST"])
def create_event():
    """
    Tworzy nowy event. Oczekujemy JSON w ciele żądania:
    {
        "title": "Tytuł wydarzenia",
        "description": "Opis (opcjonalnie)",
        "date": "YYYY-MM-DDTHH:MM:SS"  # ISO 8601
    }
    """
    data = request.get_json()
    if not data or 'title' not in data or 'date' not in data:
        return jsonify({'error': 'Please fill in the required fields: Title and Date.'}), 400

    title = data['title']
    description = data.get('description')

    try:
        date = datetime.fromisoformat(data['date'])
    except ValueError:
        return jsonify({'error': 'Invalid date format. Please use ISO 8601. (YYYY-MM-DDTHH:MM:SS).'}), 400

    new_event = Event(title=title, description=description, date=date)
    db.session.add(new_event)
    db.session.commit()

    return jsonify(new_event.to_dict()), 201

@events.route('/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    """
    Usuwa event o podanym ID.
    """
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': f'Event with ID {event_id} does not exist.'}), 404

    db.session.delete(event)
    db.session.commit()
    return jsonify({'message': f'Event with ID {event_id} has been deleted.'}), 200

@events.route('/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'Event does not exist.'}), 404

    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    date_str = data.get('date')

    if title:
        event.title = title
    if description is not None:
        event.description = description
    if date_str:
        try:
            event.date = datetime.fromisoformat(date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format.'}), 400

    db.session.commit()
    return jsonify(event.to_dict()), 200

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

    # this check has been moved to frontend
    email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if (
        not re.match(email_pattern, email)
        or not len(email) < MAX_EMAIL_LEN
        or not MIN_USERNAME_LEN <= len(username) <= MAX_USERNAME_LEN
    ):
        return jsonify({"message": "Invalid username or email"}), 400
    
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
    access_token = create_access_token(identity=identity)
    add_token_to_db(access_token)
    return jsonify(access_token=access_token)

@auth.route("/revoke_access", methods=["GET", "DELETE"])
@jwt_required()
def revoke_access_token():
    jti = get_jwt()["jti"]
    user_id = get_jwt_identity()
    revoke_token(jti, user_id)
    return jsonify(message="access token revoked")

@auth.route("/revoke_refresh", methods=["GET", "DELETE"])
@jwt_required(refresh=True)
def revoke_refresh_token():
    jti = get_jwt()["jti"]
    user_id = get_jwt_identity()
    revoke_token(jti, user_id)
    return jsonify(message="refresh token revoked")

@auth.route("/api/logout", methods=["DELETE"])
@jwt_required(refresh=True)
def logout():
    user_id = get_jwt_identity()
    refresh_jti = get_jwt()["jti"]
    revoke_token(refresh_jti, user_id)  

    data = request.get_json()
    access_token = data.get("access_token") if data else None

    if not access_token:
        return jsonify(message="Refresh token revoked. Logged out.")

    try:
        access_payload = decode_token(access_token, allow_expired=True)
    
        if access_payload["sub"] != user_id:
            return jsonify(message="Token mismatch"), 401
            
        access_jti = access_payload["jti"]
        revoke_token(access_jti, user_id) 
        
        return jsonify(message="Access and refresh tokens revoked. Logged out.")

    except:
        return jsonify(message="Refresh token revoked, but provided access token was invalid."), 400

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    try:
        return is_token_revoked(jwt_payload)
    except Exception:
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
    
    if not user_data or not "email" in user_data.keys():
        return jsonify({"message": "Bad request"}), 400
    
    email = user_data["email"]
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "There is no user with such email"}), 401

    reset_token = create_access_token(identity=user.email)
    reset_url = url_for("main.reset_password", token=reset_token, _external=True)

    msg = Message(
        'Reset password',
        recipients=[email],
        body=f"Hello! Click the link to reset your password: {reset_url}"
    )
    
    mail.send(msg)

    return {
        "message": "Email sent successfully"
    }, 200

@main.route("/reset_password/<token>", methods=["POST"])
@limiter.limit("500 per hour")   # for tests, 500 password resets for IP per hour, change before deployment to 5
def reset_password(token):
    decoded = decode_token(token)
    user_email = decoded["sub"]

    user = User.query.filter_by(email=user_email).first()
    data = request.get_json()
    new_password = data["new_password"]
    user.update_password(new_password)
    db.session.commit()

    return {
        "message": "Password changed successfully"
    }, 200

@main.route("/create_friend_request/<friend_id>", methods=["POST"])
@jwt_required()
def create_friend_request(friend_id):
    user = get_current_user()

    friend_id = uuid.UUID(friend_id)

    if User.query.filter_by(user_id=friend_id).first() is None:
        return {
            "message": "Friend does not exist",
        }, 400
    
    if user.user_id == friend_id:
        return {
            "message": "You can't befriend yourself",
        }, 400
    
    if (FriendRequest.query.filter_by(sender_id=user.user_id, receiver_id=friend_id).first() is not None
        or FriendRequest.query.filter_by(sender_id=friend_id, receiver_id=user.user_id).first()):
        return {
            "message": "Request already exists",
        }, 400
    
    if (Friendship.query.filter_by(user_id=user.user_id, friend_id=friend_id).first() is not None
        or Friendship.query.filter_by(user_id=friend_id, friend_id=user.user_id).first() is not None):
        return {
            "message": "Friendship already exists",
        }, 400

    new_request = FriendRequest(sender_id=user.user_id, receiver_id=friend_id)

    db.session.add(new_request)
    db.session.commit()
    
    return {
        "message": "Friend request created",
    }, 200

@main.route("/accept_friend_request/<friend_id>", methods=["POST"])
@jwt_required()
def accept_friend_request(friend_id):
    user = get_current_user()
    friend_id = uuid.UUID(friend_id)

    request = FriendRequest.query.filter_by(sender_id=friend_id, receiver_id=user.user_id).first()

    if request is None:
        return {
            "message": "Such request doesn't exist",
        }, 400
    
    db.session.delete(request)

    if user.user_id < friend_id:
        new_friendship = Friendship(user_id=user.user_id, friend_id=friend_id)
    else:
        new_friendship = Friendship(user_id=friend_id, friend_id=user.user_id)

    db.session.add(new_friendship)
    db.session.commit()
        
    return {
        "message": "Friend request accepted",
    }, 200

@main.route("/decline_friend_request/<friend_id>", methods=["POST"])
@jwt_required()
def decline_friend_request(friend_id):
    user = get_current_user()
    friend_id = uuid.UUID(friend_id)
    request = FriendRequest.query.filter_by(sender_id=friend_id, receiver_id=user.user_id).first()

    if request is None:
        return {
            "message": "Such request doesn't exist",
        }, 400
    
    db.session.delete(request)
    db.session.commit()
        
    return {
        "message": "Friend request declined",
    }, 200

@main.route("/create_event", methods=["POST"])
@limiter.limit("500 per minute")   # for tests, 500 events creations for IP per hour, change before deployment to 1
@jwt_required()
def create_event():
    user = get_current_user()

    event_data = request.get_json()
    required_keys = {"name", "description", "date", "time", "location"}

    if not event_data or not required_keys.issubset(event_data.keys()):
        return jsonify({"message": "Bad request"}), 400
    
    name = event_data["name"]
    description = event_data["description"]
    date_and_time = datetime.strptime(event_data["date"] + " " + event_data["time"], "%d.%m.%Y %H:%M")
    date_and_time = date_and_time.replace(tzinfo=timezone.utc)
    location = event_data["location"]

    if date_and_time <= datetime.now(timezone.utc):
            return {"message": "Event date must be in the future"}, 400
    
    new_event = Event(name=name, description=description, date_and_time=date_and_time, location=location, creator_id=user.user_id)
    
    db.session.add(new_event)
    db.session.commit()
    
    return {
        "message": "Event created successfully",
    }, 200

@main.route("/delete_event/<event_id>", methods=["DELETE"])
@jwt_required()
def delete_event(event_id):
    user = get_current_user()
    event_id = uuid.UUID(event_id)
    event = Event.query.filter_by(event_id=event_id).first()

    if event is None:
        return {
            "message": "Event doesn't exist"
        }, 400

    if user.user_id != event.creator_id:
        return {
            "message": "You can delete your own events only"
        }, 401
        
    db.session.delete(event)
    db.session.commit()

    return {
        "message": "Event deleted successfully"
    }, 200

@main.route("/create_comment/<event_id>", methods=["POST", "GET"])
@jwt_required()
def create_comment(event_id):
    user = get_current_user()
    event_id = uuid.UUID(event_id)

    event = Event.query.filter_by(id=event_id) #may change!

    if event is None:
        return {
            "message": "Event doesn't exist"
        }, 400
    
    comment_data = request.get_json()
    required_keys = {"content"}
    
    if not comment_data or not required_keys.issubset(comment_data.keys()):
        return jsonify({"message": "Bad request"}), 400
    
    new_comment = Comment(user_id=user.user_id, event_id=event_id, content=comment_data["content"])

    db.session.add(new_comment)
    db.session.commit()

    return {
        "message": "Comment created successfully"
    }, 200

@main.route("/delete_comment/<comment_id>", methods=["DELETE"])
@jwt_required()
def delete_comment(comment_id):
    user = get_current_user()
    comment_id = uuid.UUID(comment_id)
    comment = Comment.query.filter_by(comment_id=comment_id)

    if comment is None:
        return {
            "message": "Comment doesn't exist"
        }, 400

    if user.user_id != comment.user_id:
        return {
            "message": "You can delete your own comments only"
        }, 401
        
    db.session.delete(comment)
    db.session.commit()

    return {
        "message": "Comment deleted successfully"
    }, 200

@main.route("/edit_comment/<comment_id>", methods=["POST", "GET"])
@jwt_required()
def edit_comment(comment_id):
    user = get_current_user()
    comment_id = uuid.UUID(comment_id)
    comment = Comment.query.filter_by(comment_id=comment_id)

    if comment is None:
        return {
            "message": "Comment doesn't exist"
        }, 400

    if user.user_id != comment.user_id:
        return {
            "message": "You can edit your own comments only"
        }, 401
        
    data = request.get_json()
    new_content = data["new_content"]
    comment.content = new_content
    db.session.commit()

    return {
        "message": "Comment edited successfully"
    }, 200