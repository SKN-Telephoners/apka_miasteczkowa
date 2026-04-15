from flask import Blueprint, request, current_app, url_for
from flask_jwt_extended import jwt_required, get_current_user, create_access_token, get_jwt_identity
from backend.extensions import db, limiter
from backend.models import User, Friendship
from backend.responses import ResponseTypes, make_api_response
from backend.tasks import send_email_async
from backend.helpers import (
    sanitize_input, 
    revoke_all_user_tokens, 
    add_token_to_db,
    validate_uuid
)
from backend.constants import Constants
from datetime import datetime, timezone, timedelta
import re
import uuid
from sqlalchemy.exc import SQLAlchemyError
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from sqlalchemy import or_, and_, case

users_bp = Blueprint("users", __name__, url_prefix="/api/users")

@users_bp.route("/profile/<user_id>", methods=["GET"])
@jwt_required()
def get_user_info(user_id):
    user = User.query.filter_by(user_id=user_id).first()

    if not user:
        return make_api_response(ResponseTypes.NOT_FOUND, message="User not found")
    
    profile_pic_data = None
    if user.profile_picture:
        url, _ = cloudinary_url(user.profile_picture, secure=True)
        profile_pic_data = {
            "cloud_id": user.profile_picture,
            "url": url
        }

    friend_count = Friendship.query.filter(
        or_(
            Friendship.user_id == user.user_id,
            Friendship.friend_id == user.user_id
        )
    ).count()

    user_data = {
        "user_id": str(user.user_id),
        "username": user.display_name,
        "email": user.email,
        "created_at": user.created_at.isoformat(),
        "academy": user.academy,
        "course": user.course,
        "year": user.year,
        "faculty": user.faculty,
        "academic_clubs": user.academic_clubs,
        "description": user.description,
        "profile_picture": profile_pic_data,
        "friend_count": friend_count,
        "deleted": user.deleted
    }

    return make_api_response(ResponseTypes.SUCCESS, data=user_data)


@users_bp.route("/profile/<user_id>", methods=["GET"])
@jwt_required()
def get_public_user_info(user_id):
    target_user_id = validate_uuid(user_id)
    if not target_user_id:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid user ID")

    user = User.query.filter_by(user_id=target_user_id).first()
    if not user or user.deleted is True:
        return make_api_response(ResponseTypes.NOT_FOUND, message="User not found")

    profile_pic_data = None
    if user.profile_picture:
        url, _ = cloudinary_url(user.profile_picture, secure=True)
        profile_pic_data = {
            "cloud_id": user.profile_picture,
            "url": url,
        }

    user_data = {
        "user_id": str(user.user_id),
        "id": str(user.user_id),
        "username": user.display_name,
        "academy": user.academy,
        "course": user.course,
        "year": user.year,
        "description": user.description,
        "profile_picture": profile_pic_data,
    }

    return make_api_response(ResponseTypes.SUCCESS, data=user_data)


@users_bp.route("/update_profile", methods=["PUT"])
@limiter.limit("300 per minute")
@jwt_required()
def update_profile():
    user = get_current_user()

    if user.deleted:
        return make_api_response(ResponseTypes.FORBIDDEN, message="Account is deleted")

    user_data = request.get_json(silent=True)
    if not user_data:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Invalid JSON or missing data")

    raw_username = user_data.get("username")
    if raw_username is not None:
        username = sanitize_input(str(raw_username)).strip()
        if not username:
            return make_api_response(ResponseTypes.INVALID_DATA, message="Username cannot be empty")
        
        if (not re.match(Constants.USERNAME_PATTERN, username)
            or not Constants.MIN_USERNAME_LEN <= len(username) <= Constants.MAX_USERNAME_LEN):
            return make_api_response(ResponseTypes.INVALID_DATA, message="Incorrect username")

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

    academy_data = current_app.config.get('ACADEMY_DATA', {})

    raw_academy = user_data.get("academy")

    if raw_academy is not None:
        academy = sanitize_input(str(raw_academy)).strip()
        
        if academy and academy not in academy_data:
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Such academy doesn't exist")
        
        user.academy = academy if academy else None

        if user.academy != Constants.PRIMARY_ACADEMY:
            user.course = None
            user.year = None
            user.faculty = None
            user.academic_clubs = None

    if "profile_picture" in user_data:
        pic_data = user_data["profile_picture"]
        current_pic = user.profile_picture if user.profile_picture else None

        if pic_data is None:
            if current_pic:
                try:
                    cloudinary.uploader.destroy(current_pic)
                except Exception as cloud_err:
                    current_app.logger.error(f"Cloudinary delete error: {cloud_err}")
                
                user.profile_picture = None

        elif isinstance(pic_data, dict) and "cloud_id" in pic_data:
            new_cloud_id = pic_data["cloud_id"]
            
            if current_pic:
                if current_pic != new_cloud_id:
                    try:
                        cloudinary.uploader.destroy(current_pic)
                    except Exception as cloud_err:
                        current_app.logger.error(f"Cloudinary delete error: {cloud_err}")
                    
                    user.profile_picture = new_cloud_id
            else:
                user.profile_picture = new_cloud_id

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in update_profile: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Profile updated successfully")


@users_bp.route("/update_academic_details", methods=["PUT"])
@limiter.limit("100 per minute")
@jwt_required()
def update_academic_details():
    user = get_current_user()
    
    if not user:
        return make_api_response(ResponseTypes.NOT_FOUND, message="User not found")

    if user.deleted:
        return make_api_response(ResponseTypes.FORBIDDEN, message="Account is deleted")
    
    if user.academy != Constants.PRIMARY_ACADEMY:
        return make_api_response(ResponseTypes.BAD_REQUEST, message=f"Only {Constants.PRIMARY_ACADEMY} students can add academic details")


    data = request.get_json(silent=True)
    if not data:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Invalid JSON")

    raw_course = data.get("course")
    raw_year = data.get("year")
    raw_faculty = data.get("faculty")
    raw_clubs = data.get("academic_clubs")

    courses_data = current_app.config.get('COURSES_DATA', [])
    academic_clubs_data = current_app.config.get('CLUBS_DATA', {})
    faculties_data = current_app.config.get('FACULTIES_DATA', [])


    if raw_faculty is not None or raw_course is not None or raw_year is not None:
        if not raw_faculty or not raw_course or not raw_year:
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Faculty, course and year must be provided together")

        faculty = sanitize_input(str(raw_faculty)).strip()
        course = sanitize_input(str(raw_course)).strip()
        year = sanitize_input(str(raw_year)).strip()

        if faculty not in faculties_data:
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Such faculty doesn't exist")

        if course not in courses_data:
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Such course doesn't exist")
            
        if str(year) not in ["1", "2", "3", "4", "5", "6"]:
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Year must be between 1 and 6")

        user.faculty = faculty
        user.course = course
        user.year = int(year) 

    if raw_clubs is not None:
        clubs_str = sanitize_input(str(raw_clubs)).strip()
        if not clubs_str:
            user.academic_clubs = None
        else:
            user_clubs = [club.strip() for club in clubs_str.split(",")]
            for club in user_clubs:
                if club not in academic_clubs_data:
                    return make_api_response(ResponseTypes.BAD_REQUEST, message=f"Club '{club}' doesn't exist")
            
            user.academic_clubs = user_clubs

    try:
        db.session.commit()
        return make_api_response(ResponseTypes.SUCCESS, message="Academic details updated successfully")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating academic details: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)


@users_bp.route("/settings/password", methods=["PUT"])
@jwt_required()
@limiter.limit("500 per minute")
def change_password():
    user = get_current_user()
    password_data = request.get_json(silent=True)
    
    required_keys = {"old_password", "new_password"}

    if not password_data or not required_keys.issubset(password_data.keys()):
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Missing password data")

    if not user.validate_password(password_data["old_password"]):
        return make_api_response(ResponseTypes.INVALID_CREDENTIALS, message="Old password incorrect")

    new_password = password_data["new_password"]
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

@users_bp.route("/settings/change_email", methods=["PUT"])
@jwt_required()
@limiter.limit("300 per minute")
def change_email_request():
    user = get_current_user()
    data = request.get_json(silent=True)
    
    if not data or "new_email" not in data:
        return make_api_response(ResponseTypes.BAD_REQUEST)

    new_email = sanitize_input(data["new_email"]).lower().strip()

    if not re.match(Constants.EMAIL_PATTERN, new_email) or len(new_email) > Constants.MAX_EMAIL_LEN:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid email format")
    if User.query.filter_by(email=new_email).first():
        return make_api_response(ResponseTypes.CONFLICT, message="Account with this email already exists")

    email_change_token = create_access_token(
        identity=str(user.user_id),
        expires_delta=timedelta(minutes=Constants.CHANGE_EMAIL_EXPIRES),
        additional_claims={"type": "email_change"}
    )

    try:
        add_token_to_db(email_change_token)
    except Exception as e:
        current_app.logger.error(f"Failed to log email change token for user {user.user_id}: {e}")

    email_change_url = url_for("email.confirm_change", token=email_change_token, _external=True)
    
    new_email_body = f"Hello! Click the link to change your email: {email_change_url}"
    
    security_alert_body = (
        f"Hello,\n\n"
        f"A request was made to change the email address associated with your account to {new_email}.\n"
        f"If you made this request, you can safely ignore this email.\n"
        f"If you did NOT make this request, please log in immediately and change your password, "
        f"or contact support to secure your account."
    )

    try:
        user.pending_email = new_email 
        db.session.commit()
        
        send_email_async.delay('Change email confirmation', new_email, new_email_body)
        send_email_async.delay('Security Alert: Email Change Requested', user.email, security_alert_body)
        
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
    

@users_bp.route("/settings/delete_account", methods=["DELETE"])
@jwt_required()
def delete_account():
    user = get_current_user()
    data = request.get_json(silent=True)
    
    if not data or "password" not in data:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Password required to delete account")
    
    if not user.validate_password(data["password"]):
        return make_api_response(ResponseTypes.INVALID_CREDENTIALS, message="Incorrect password")

    try:
        user.deleted = True
        
        short_random_id = uuid.uuid4().hex[:15] 
        
        user.username = f"del_{short_random_id}"
        user.email = f"del_{short_random_id}@del.local"
        user.pending_email = None

        user.description = None
        user.academy = None
        user.faculty = None
        user.course = None
        user.year = None
        user.academic_clubs = None
        
        user.update_password(uuid.uuid4().hex)
        
        revoke_all_user_tokens(user.user_id)

        if user.profile_picture:
            try:
                cloudinary.uploader.destroy(user.profile_picture)
            except Exception as cloud_err:
                current_app.logger.error(f"Failed to delete profile picture {user.profile_picture} from Cloudinary: {cloud_err}")
            user.profile_picture = None
        
        db.session.commit()
        return make_api_response(ResponseTypes.SUCCESS, message="Account successfully deleted")
    
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Delete account error: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    
@users_bp.route("/users_list", methods=["GET"])
@limiter.limit("600 per second")
@jwt_required()
def get_users_list():
    current_user_id = validate_uuid(get_jwt_identity())
    
    try:
        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=Constants.PAGINATION_DEFAULT_LIMIT, type=int)
        if limit > Constants.MAX_PAGINATION_LIMIT:
            limit = Constants.MAX_PAGINATION_LIMIT
    except (ValueError, TypeError):
        return make_api_response(ResponseTypes.INVALID_DATA, message="Pagination must be a positive integer")

    search_val = request.args.get("search", default="", type=str).strip()

    query = db.session.query(User, Friendship.friend_id).outerjoin(
        Friendship, 
        or_(
            and_(Friendship.user_id == current_user_id, Friendship.friend_id == User.user_id),
            and_(Friendship.friend_id == current_user_id, Friendship.user_id == User.user_id)
        )
    ).filter(User.deleted == False, User.user_id != current_user_id)

    if search_val:
        clean_search = sanitize_input(search_val).strip()[:Constants.MAX_USERNAME_LEN]
        if clean_search:
            escaped_search = clean_search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            query = query.filter(User.username.startswith(f"{escaped_search}"))


    friend_priority = case(
        (Friendship.friendship_id.isnot(None), 1), 
        else_=0
    )

    query = query.order_by(friend_priority.desc(), User.username.asc())

    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    users_list = []
    for user, f_id in pagination.items:
        is_friend = f_id is not None
        user_info = {
            "user_id": str(user.user_id),
            "username": user.display_name,
            "academy": user.academy,
            "profile_picture": user.profile_picture,
            "is_friend": is_friend
        }
        users_list.append(user_info)

    return make_api_response(ResponseTypes.SUCCESS, data={
        "users": users_list,
        "pagination": {
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": pagination.page
        }
    })
