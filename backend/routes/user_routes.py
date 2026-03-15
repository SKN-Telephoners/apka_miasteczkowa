from flask import Blueprint
from flask_jwt_extended import jwt_required, get_current_user
from backend.responses import ResponseTypes, make_api_response
from datetime import datetime, timezone, timedelta
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required, set_access_cookies

users_bp = Blueprint("users", __name__, url_prefix="/api/users")

@users_bp.route("/me", methods=["GET"])
@jwt_required()
def get_user_info():
    user = get_current_user()

    if not user:
        return make_api_response(ResponseTypes.NOT_FOUND, message="User not found")

    return make_api_response(ResponseTypes.SUCCESS, data={
        "user": {
            "username": user.username,
            "email": user.email
        }})
