from flask import Blueprint, request, jsonify
from backend.models import User
from backend.extensions import db
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity
import re

MAX_EMAIL_LEN = 320
MAX_USERNAME_LEN = 32
MIN_USERNAME_LEN = 3

main = Blueprint("main", __name__)
auth = Blueprint("auth", __name__)

@auth.route("/api/register",methods=["POST"])
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
    
    access_token = create_access_token(identity=user.user_id)
    refresh_token = create_refresh_token(identity=user.user_id)

    return {
        "message": "Login successful",
        "user": {
            "username": user.username,
        },
        "access_token": access_token,
        "refresh_token": refresh_token
    }, 200

@auth.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify(access_token=access_token)

@main.route("/user", methods=["GET"])
@jwt_required()
def get_user_info():
    user_id = get_jwt_identity()
    
    user = User.query.filter_by(user_id=user_id).first()

    return {
        "user": {
            "username": user.username,
            "email": user.email
        },
    }, 200