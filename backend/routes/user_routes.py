from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_current_user
from backend.responses import ResponseTypes, make_api_response
from backend.helpers import sanitize_input
from backend.extensions import db, limiter
from backend.constants import Constants
from sqlalchemy.exc import SQLAlchemyError

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

@users_bp.route("/me/edit_profile", methods=["PUT"])
@limiter.limit("100 per minute")
@jwt_required()
def edit_profile():
    user = get_current_user()

    if not user:
        return make_api_response(ResponseTypes.NOT_FOUND, message="User not found")
    
    user_data = request.get_json(silent=True)
    if not user_data:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Invalid JSON or missing data")

    raw_username = user_data.get("username")
    if raw_username is not None:
        username = sanitize_input(str(raw_username)).strip()
        if not (Constants.MIN_USERNAME_LEN <= len(username) <= Constants.MAX_USERNAME_LEN):
            return make_api_response(ResponseTypes.INVALID_DATA, message=f"Username must be between {Constants.MIN_USERNAME_LEN} and {Constants.MAX_USERNAME_LEN} characters")
        user.username = username
    
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in edit_profile: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Profile edited successfully")