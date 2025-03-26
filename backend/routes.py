from flask import Blueprint, request, jsonify
from backend.models import User
from backend.extensions import db
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity

main = Blueprint("main", __name__)
auth = Blueprint("auth", __name__)

public_url = "example address"

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
    
    access_token = create_access_token(identity=user.username)
    refresh_token = create_refresh_token(identity=user.username)

    return {
        "message": "Login successful",
        "user": {
            "username": user.username,
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    }, 200

# if an expired token attempts to access a protected endpoint, you will get a JSON response back like
# {"msg": "Token has expired"} and a 401 status code
# Then use the refresh token to generate a new access token and redo the request with the new token.
@auth.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify(access_token=access_token)

@main.route("/user", methods=["GET"])
@jwt_required
def get_user_info():
    user = get_jwt_identity()
    print(user)
    return {
        "user": {
            "username": user.username,
            "email": user.email
        },
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

#revoking tokens??
#logout endpoint, revoke both access_token and refresh_token