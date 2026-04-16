from datetime import timedelta
from flask import Blueprint, request, url_for, current_app
from backend.models import User
from backend.extensions import db, mail, limiter
from backend.constants import Constants
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt, get_jwt_identity, decode_token
from backend.helpers import add_token_to_db, revoke_token, sanitize_input
import re
from flask_mail import Message

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/register",methods=["POST"])
@limiter.limit("500 per hour")   # for tests, 500 registers for IP per hour, change before deployment to 5
def register_user():
    user_data = request.get_json()
    required_keys = {"username", "password", "email"}

    if not user_data or not required_keys.issubset(user_data.keys()):
        return make_api_response(ResponseTypes.BAD_REQUEST)
    
    username = sanitize_input(user_data["username"])
    password = user_data["password"]
    email = sanitize_input(user_data["email"]).lower()

    if (
        not re.match(Constants.EMAIL_PATTERN, email)
        or not re.match(Constants.USERNAME_PATTERN, username)
        or not len(email) < Constants.MAX_EMAIL_LEN
        or not Constants.MIN_USERNAME_LEN <= len(username) <= Constants.MAX_USERNAME_LEN
    ):
        return make_api_response(ResponseTypes.INVALID_DATA, message="Incorrect username or email")
    
    if not re.match(Constants.PASSWORD_PATTERN, password):
        return make_api_response(ResponseTypes.INVALID_DATA, message="Incorrect password format")
    
    new_user = User(username=username, password=password, email=email)
    if User.query.filter_by(username=username).first() is not None:
        return make_api_response(ResponseTypes.CONFLICT, message="Username already taken")
    if User.query.filter_by(email=email).first() is not None:
        return make_api_response(ResponseTypes.CONFLICT, message="Account with this email already exists")

    db.session.add(new_user)
    db.session.flush()
    #send auth email
    auth_token = create_access_token(
        identity=new_user.user_id,
        expires_delta=timedelta(hours=24),
        additional_claims={"type": "email_verification"}
        )
    add_token_to_db(auth_token)
    auth_url = url_for("email.verify", token=auth_token, _external=True)

    msg = Message(
            'Auth account',
            recipients=[email],
            body=f"Hello! Click the link to authorize your account: {auth_url}"
        )
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration db commit error: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR, message="Registration failed")

    try:
        mail.send(msg)
    except Exception as e:
        # Registration is already committed; do not fail with 500 just because email delivery failed.
        current_app.logger.error(f"Registration mail send error for {email}: {e}")
        return make_api_response(
            ResponseTypes.CREATED,
            message="Registration successful. Verification email could not be sent, please request it again."
        )
    
    return make_api_response(ResponseTypes.CREATED, message="Registration successful")

@auth_bp.route("/login", methods=["POST"])
@limiter.limit("500 per 15 minutes")   # for tests, 500 logins for IP per 15 minutes, change before deployment to 5
def login_user():
    user_data = request.get_json()
    required_keys = {"username", "password"}
    
    if not user_data or not required_keys.issubset(user_data.keys()):
        return make_api_response(ResponseTypes.BAD_REQUEST)
    
    username = user_data["username"]
    password = user_data["password"]

    if (
        not isinstance(username, str)
        or not isinstance(password, str) 
        or len(username) > Constants.MAX_USERNAME_LEN
        or len(password) > Constants.MAX_PASSWORD_LEN
    ):
        return make_api_response(ResponseTypes.INVALID_CREDENTIALS)

    user = User.query.filter_by(username=username).first()
    if not user or not user.validate_password(password) or user.deleted:
        return make_api_response(ResponseTypes.INVALID_CREDENTIALS)
    if not user.is_confirmed:
       return make_api_response(ResponseTypes.ACCOUNT_NOT_VERIFIED)
    
    limiter.reset()


    access_token = create_access_token(identity=user.user_id)
    refresh_token = create_refresh_token(identity=user.user_id)
    
    add_token_to_db(access_token)
    add_token_to_db(refresh_token)

    return make_api_response(ResponseTypes.LOGIN_SUCCESS, data={
        "user": {"username": user.username},
        "access_token": access_token,
        "refresh_token": refresh_token
    })

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    jti = get_jwt()["jti"]

    revoke_token(jti, identity)

    new_access_token = create_access_token(identity=identity)
    new_refresh_token = create_refresh_token(identity=identity)

    add_token_to_db(new_access_token)
    add_token_to_db(new_refresh_token)
    
    return make_api_response(ResponseTypes.SUCCESS, data={
        "access_token": new_access_token,
        "refresh_token": new_refresh_token
        })

@auth_bp.route("/logout", methods=["DELETE"])
@jwt_required(refresh=True)
def logout():
    user_id = get_jwt_identity()
    refresh_jti = get_jwt()["jti"]
    revoke_token(refresh_jti, user_id)  

    data = request.get_json(silent=True)
    access_token = data.get("access_token") if data else None

    if access_token:
        try:
            access_payload = decode_token(access_token, allow_expired=True)
            if access_payload["sub"] == user_id:
                access_jti = access_payload["jti"]
                revoke_token(access_jti, user_id)
        except Exception:
            pass
            
    return make_api_response(ResponseTypes.LOGOUT_SUCCESS)

@auth_bp.route("/revoke_access", methods=["DELETE"])
@jwt_required()
def revoke_access_token():
    jti = get_jwt()["jti"]
    user_id = get_jwt_identity()
    revoked = revoke_token(jti, user_id)
    if not revoked:
        pass
    return make_api_response(ResponseTypes.TOKEN_REVOKED, message="Access token revoked")

@auth_bp.route("/revoke_refresh", methods=["DELETE"])
@jwt_required(refresh=True)
def revoke_refresh_token():
    jti = get_jwt()["jti"]
    user_id = get_jwt_identity()
    revoke_token(jti, user_id)
    return make_api_response(ResponseTypes.TOKEN_REVOKED, message="Refresh token revoked")
