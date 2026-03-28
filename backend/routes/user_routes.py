from flask import Blueprint, request, current_app, url_for
from flask_jwt_extended import jwt_required, get_current_user, get_jwt, create_access_token
from backend.extensions import db, mail, limiter
from backend.models import User
from backend.responses import ResponseTypes, make_api_response
from backend.helpers import (
    sanitize_input, 
    revoke_all_user_tokens, 
    add_token_to_db, 
    revoke_token
)
from backend.constants import Constants
from flask_mail import Message
from datetime import datetime, timezone, timedelta
import re
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


@users_bp.route("/update_profile", methods=["PUT"])
@limiter.limit("300 per minute")
@jwt_required()
def update_profile():
    user = get_current_user()

    if user.is_deleted:
        return make_api_response(ResponseTypes.FORBIDDEN, message="Account is deleted")

    user_data = request.get_json(silent=True)
    if not user_data:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Invalid JSON or missing data")

    raw_username = user_data.get("username")
    if raw_username is not None:
        username = sanitize_input(str(raw_username)).strip()
        if not username:
            return make_api_response(ResponseTypes.INVALID_DATA, message="Username cannot be empty")
        
        if username != user.username:
            if User.query.filter_by(username=username).first():
                return make_api_response(ResponseTypes.BAD_REQUEST, message="Username already taken")
            user.username = username

    raw_desc = user_data.get("description")
    if raw_desc is not None:
        description = sanitize_input(str(raw_desc)).strip()
        if len(description) > Constants.MAX_DESCRIPTION_LEN:
            return make_api_response(ResponseTypes.INVALID_DATA, message="Description is too long")
        user.description = description

    # 3. Academy & Studies Data
    academy_data = current_app.config.get('ACADEMY_DATA', {})
    courses_data = current_app.config.get('COURSES_DATA', [])
    academic_circle_data = current_app.config.get('CIRCLES_DATA', {})

    raw_academy = user_data.get("academy")
    raw_course = user_data.get("course")
    raw_year = user_data.get("year")
    raw_circle = user_data.get("academic_circle")

    if raw_academy is not None:
        academy = sanitize_input(str(raw_academy)).strip()
        
        if academy and academy not in academy_data:
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Such academy doesn't exist")
        
        user.academy = academy if academy else None

        if user.academy != "AGH":
            user.course = None
            user.year = None
            user.academic_circle = None


    effective_academy = user.academy

    if raw_course is not None or raw_year is not None:
        if effective_academy != "AGH":
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Only AGH members can set course and year")

        if not raw_course or not raw_year:
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Both course and year must be provided together")

        course = sanitize_input(str(raw_course)).strip()
        year = sanitize_input(str(raw_year)).strip()

        if course not in courses_data:
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Such course doesn't exist")
            
        if str(year) not in ["1", "2", "3", "4", "5", "6"]:
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Year must be between 1 and 6")

        user.course = course
        user.year = int(year) 


    if raw_circle is not None:
        if effective_academy != "AGH":
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Only AGH members can set academic circles")

        circle_str = sanitize_input(str(raw_circle)).strip()
        if not circle_str:
            user.academic_circle = None
        else:
            user_circles = [circle.strip() for circle in circle_str.split(",")]
            for circle in user_circles:
                if circle not in academic_circle_data:
                    return make_api_response(ResponseTypes.BAD_REQUEST, message=f"Circle '{circle}' doesn't exist")
            
            user.academic_circle = user_circles

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in update_profile: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Profile updated successfully")


@users_bp.route("/settings/password", methods=["PUT"])
@jwt_required()
@limiter.limit("500 per minute")
def change_password():
    user = get_current_user()
    data = request.get_json(silent=True)
    
    if not data or not all(k in data for k in ("old_password", "new_password")):
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Missing password data")


    if not user.validate_password(data["old_password"]):
        return make_api_response(ResponseTypes.INVALID_CREDENTIALS, message="Old password incorrect")


    new_password = data["new_password"]
    if not re.match(Constants.PASSWORD_PATTERN, new_password):
        return make_api_response(ResponseTypes.INVALID_DATA, message="New password format incorrect")

    try:
        user.update_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        
        revoke_all_user_tokens(user.user_id)
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in change_password: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Password updated successfully")

@users_bp.route("/settings/email", methods=["PUT"])
@jwt_required()
@limiter.limit("3 per hour")
def initiate_email_change():
    user = get_current_user()
    data = request.get_json(silent=True)
    
    if not data or "new_email" not in data:
        return make_api_response(ResponseTypes.BAD_REQUEST)

    new_email = sanitize_input(data["new_email"]).lower().strip()

    if not re.match(Constants.EMAIL_PATTERN, new_email) or len(new_email) > Constants.MAX_EMAIL_LEN:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid email format")

    from backend.models import User
    if User.query.filter_by(email=new_email).first():
        return make_api_response(ResponseTypes.CONFLICT, message="Email already in use")

    verify_token = create_access_token(
        identity=str(user.user_id),
        expires_delta=timedelta(hours=24),
        additional_claims={"type": "email_change", "new_email": new_email}
    )
    add_token_to_db(verify_token)

    verify_url = url_for("email.confirm_change", token=verify_token, _external=True) #TODO: email.confirm_change in email_routes.py

    msg = Message(
        'Confirm Email Change',
        recipients=[new_email],
        body=f"To change your email to {new_email}, click here: {verify_url}"
    )

    try:
        user.pending_email = new_email 
        db.session.commit()
        mail.send(msg)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Email change error: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR, message="Could not send verification email")

    return make_api_response(ResponseTypes.SUCCESS, message="Verification link sent to new email")


@users_bp.route("/settings/logout_all", methods=["DELETE"])
@jwt_required()
def logout_from_all_devices():
    user_id = get_current_user().user_id
    
    try:
        revoke_all_user_tokens(user_id)
        return make_api_response(ResponseTypes.SUCCESS, message="Successfully logged out from all devices")
    except Exception as e:
        current_app.logger.error(f"Logout all error: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    

@users_bp.route("/settings/account", methods=["DELETE"])
@jwt_required()
def delete_account():
    user = get_current_user()
    data = request.get_json(silent=True)
    
    if not data or "password" not in data:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Password required to delete account")
    
    if not user.validate_password(data["password"]):
        return make_api_response(ResponseTypes.INVALID_CREDENTIALS, message="Incorrect password")

    try:
        #TODO: mądrzejsza blokada logowania XD
        user.is_confirmed = False
        user.is_deleted = True
        
        revoke_all_user_tokens(user.user_id)
        
        db.session.commit()
        return make_api_response(ResponseTypes.SUCCESS, message="Account marked for deletion")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Delete account error: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)