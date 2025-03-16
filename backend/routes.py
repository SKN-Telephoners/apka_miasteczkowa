from flask import Blueprint, request, jsonify
from backend.models import User
from backend.extensions import db

main = Blueprint("main", __name__)
auth = Blueprint("auth", __name__)

public_url = "example address"

@auth.route("/api/login", methods=["POST"])
def login_user():
    user_data = request.get_json()
    required_keys = {"username", "password"}
    
    if not user_data or not required_keys.issubset(user_data.keys()):
        return jsonify({"message": "Bad request"}), 401
    
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