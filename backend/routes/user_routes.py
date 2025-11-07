from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_current_user

user_bp = Blueprint("user", __name__)

@user_bp.route("/user", methods=["GET"])
@jwt_required()
def get_user_info():
    user = get_current_user()
    return jsonify({
        "user": {
            "username": user.username,
            "email": user.email
        }
    }), 200
