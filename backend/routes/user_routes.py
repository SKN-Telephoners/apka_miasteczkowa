from flask import Blueprint
from flask_jwt_extended import jwt_required, get_current_user
from backend.responses import ResponseTypes, make_api_response
from datetime import datetime, timezone, timedelta
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required, set_access_cookies

users_bp = Blueprint("users", __name__, url_prefix="/api/users")

@users_bp.after_app_request
def refresh_expiring_jwts(response): #after every request
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(seconds=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original response
        return response


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
