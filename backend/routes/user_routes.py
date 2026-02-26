from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_current_user
// Blueprint for user-related routes
// Po polsku: Blueprint dla tras związanych z użytkownikami
user_bp = Blueprint("user", __name__)
// Route for getting the current user's information
// Po polsku: Trasa do pobierania informacji o aktualnym użytkowniku
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
