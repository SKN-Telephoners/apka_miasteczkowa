from flask import Blueprint, request, jsonify
from backend.models import User
from backend.extensions import db, jwt

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
    
    access_token = jwt.create_access_token(identity=user.user_id)

    return {
        "message": "Login successful",
        "user": {
            "username": user.username
        },
        "access_token": access_token
    }, 200

@main.route('/user', methods=['GET'])
@jwt.jwt_required()
def get_user_data():

    current_user_id = jwt.get_jwt_identity()

    user = db.get(current_user_id)
    if user:
        return jsonify({
            "user": {
                "username": user.username,
                "email": user.email
            }
        }), 200
    else:
        return jsonify({"message": "User not found"}), 404

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