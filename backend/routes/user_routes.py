from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_current_user

users_bp = Blueprint("users", __name__, url_prefix="/api/users")

@users_bp.route("/me", methods=["GET"])
@jwt_required()
def get_user_info():
    user = get_current_user()

    if not user:
        return jsonify({"message": "User not found"}), 404

    return {
        "user": {
            "username": user.username,
            "email": user.email
        },
    }, 200