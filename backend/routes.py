from flask import Blueprint, request, jsonify, url_for
from backend.models import User, FriendRequest, Friendship, Event
from backend.extensions import db, jwt, mail, limiter
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt, get_jwt_identity, get_current_user, decode_token
from backend.helpers import add_token_to_db, revoke_token, is_token_revoked
import re
import uuid
from flask_mail import Message
from datetime import datetime, timezone
from sqlalchemy import or_
from datetime import date
import os
import json

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

@auth.route("/user/user_update", methods=["POST"]) #Ogólny pomysł jak to ma działać to użytkownik ma memu swojego profilu i może edytować w nim
@jwt_required()                                    #swoje dane które są w nim wyświetlane cały czas
def update_user_course_or_academy():

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # To daje ścieżke do plików z bazą kierunków akademii itd
    DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, "keys")) # tu jest ważne żeby zmienić w razie włżenia tych plików to innych folderów pozmieniać

    
    with open(os.path.join(DATA_DIR, "academy.json"), encoding="utf-8") as f:
        academy_data = json.load(f)
    with open(os.path.join(DATA_DIR, "courses.json"), encoding="utf-8") as r:
        courses_data = json.load(r)
    with open(os.path.join(DATA_DIR, "academic_circle.json") , encoding="utf-8") as a:
        academic_circle_data = json.load(a)
      
    user_data = request.get_json() #To ma wyświetlać co jest w menu zmiany użytkownika

    academy = user_data.get("academy")
    course = user_data.get("course")
    academic_circle = user_data.get("academic_circle")
    year = user_data.get("year")
 

    if (academy != "AGH" and course) or (academy != "AGH" and academic_circle): #Ta część ma sprawdzać zgodność tego co jest w menu z plikami
        return jsonify ({"message": "Only AGH members can change course and academic circle"}), 404

    if academy not in academy_data and academy != None:
        return jsonify({"message": "Such academy doesn't exist"}), 404

    if course not in courses_data and course != None:
        return jsonify({"message": "Such course doesn't exist"}), 404

    if academic_circle not in academic_circle_data and academic_circle != None:
        return jsonify({"message": "Such circle dosen't exist"}), 404

    if academy:                    #Ta część podmienia wartości w tym menu
        academy = (academy)

    if academy is None:
        academy = (None)
   
    if academy == "AGH" and course:
        course = (course)

    if course is None:
        course = (None)
            
    if academy == "AGH" and academic_circle:   
        academic_circle = (academic_circle)      
    
    if academic_circle is None:
        academic_circle = (None)

    if year: 
        year_pattern = r"^[1-6]$"
        if not re.match(year_pattern, year):
            return jsonify({"message": "Invalid year"}), 404
        year = (year)

    if year is None:
        year = (None)
    
    db.session.commit()
    return jsonify({"message": "User updated successfully"}), 200

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
    
    #now there will be multiple active tokens for password resetting (we don't want that) - to be fixed
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