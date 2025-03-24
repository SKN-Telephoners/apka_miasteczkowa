from flask import Blueprint, request, jsonify
from backend.models import User
from backend.extensions import db
import re

MAX_EMAIL_LEN = 320
MAX_USERNAME_LEN = 32
MIN_USERNAME_LEN = 3

main = Blueprint("main", __name__)
auth = Blueprint("auth", __name__)


public_url = "example address"

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
    if db.session.query(User).filter_by(username=username).first() is not None:
        return jsonify({"message": "Username already taken"}), 409
    if db.session.query(User).filter_by(email=email).first() is not None:
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
    
    user = db.session.query(User).filter_by(username=username).first()
    if not user or not user.validate_password(password):
        return jsonify({"message": "Invalid username or password"}), 401
    
    return {
        "message": "Login successful",
        "user": {
            "username": user.username
        }
    }, 200

@main.route("/get-url", methods=["GET"])
def get_url():
    return jsonify({"url": public_url})

@main.route("/message", methods=["GET"])
def get_message():
    return jsonify({"message": "Welcome in Flask API!"})

@main.route("/send_data", methods=["POST"])
def receive_data():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Error: No data received."}), 400
    
    print(f"Received Data: {data}")
    return jsonify({"message": "Server has received data."}), 200