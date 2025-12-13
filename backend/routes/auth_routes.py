from flask import Blueprint, request, jsonify, url_for
from backend.models import User
from backend.extensions import db, mail, limiter
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt, get_jwt_identity, decode_token
from backend.helpers import add_token_to_db, revoke_token
import re
from flask_mail import Message

MAX_EMAIL_LEN = 320
MAX_USERNAME_LEN = 32
MIN_USERNAME_LEN = 3

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/register",methods=["POST"])
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

    #send auth email

    auth_token = create_access_token(identity=email)

    auth_url = url_for("email.verify", token=auth_token, _external=True)

    msg = Message(
            'Auth account',
            recipients=[email],
            body=f"Hello! Click the link to authorize your account: {auth_url}"
        )

    mail.send(msg)
    
    return {
        "message": "Registration successful",
    }, 200

@auth_bp.route("/login", methods=["POST"])
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
    
    if not user.is_confirmed:
        return jsonify({"message":"At first, verify your account"})
    
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

@auth_bp.route("/refresh", methods=["POST"])
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

@auth_bp.route("/logout", methods=["DELETE"])
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
            
    return jsonify(message="Logged out successfully"), 200

@auth_bp.route("/revoke_access", methods=["DELETE"])
@jwt_required()
def revoke_access_token():
    jti = get_jwt()["jti"]
    user_id = get_jwt_identity()
    revoke_token(jti, user_id)
    return jsonify(message="Access token revoked")

@auth_bp.route("/revoke_refresh", methods=["DELETE"])
@jwt_required(refresh=True)
def revoke_refresh_token():
    jti = get_jwt()["jti"]
    user_id = get_jwt_identity()
    revoke_token(jti, user_id)
    return jsonify(message="Refresh token revoked")