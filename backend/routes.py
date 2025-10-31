from flask import Blueprint, request, jsonify, url_for
from backend.models import User, TokenBlocklist
from backend.extensions import db, jwt, mail, limiter
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt, get_jwt_identity, get_current_user, decode_token
from backend.helpers import add_token_to_db, revoke_token, is_token_revoked
from datetime import timedelta
import re
from flask_mail import Message

MAX_EMAIL_LEN = 320
MAX_USERNAME_LEN = 32
MIN_USERNAME_LEN = 3

main = Blueprint("main", __name__)
auth = Blueprint("auth", __name__)

@auth.route("/api/register",methods=["POST"])
@limiter.limit("50 per hour")   # maks. 5 rejestracji na IP na godzinę
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
@limiter.limit("5 per 15 minutes")  # maks. 5 prób logowania na IP w ciągu 15 minut
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

    db.session.add(TokenBlocklist(access_token))
    db.session.commit()
    
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
    return User.query.get(user_id)
    return jsonify(access_token=access_token)
  
@main.route("/reset_password_request", methods=["POST"])
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