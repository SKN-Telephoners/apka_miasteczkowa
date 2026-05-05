from flask import Blueprint, request, url_for, current_app
from backend.models import User
from backend.extensions import db, mail, limiter
from backend.constants import Constants
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import create_access_token, decode_token
from backend.helpers import add_token_to_db, revoke_token, is_token_revoked, revoke_all_user_tokens
from backend.tasks import send_email_async
import re
from flask_mail import Message
from datetime import datetime, timedelta, timezone

email_bp = Blueprint("email", __name__, url_prefix="/api/email")

@email_bp.route("/verify_request",methods=["POST"])
def verify_request():
    user_data = request.get_json(silent=True)    
    if not user_data or not "email" in user_data.keys():
        current_app.logger.warning(f"WARNING: /verify_request, no user_data or no email in user_data")
        return make_api_response(ResponseTypes.BAD_REQUEST)
    
    email=user_data["email"]
    user = User.query.filter_by(email=email).first()

    if user and not user.is_confirmed:
        try:
            revoke_all_user_tokens(user.user_id, token_type="email_verification")
            auth_token = create_access_token(
                identity=user.user_id, 
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
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"ERROR: /verify_request, DB exception occured: {e}")

    current_app.logger.info(f"INFO: /verify_request, sending email for user: {email}")
    return make_api_response(ResponseTypes.SUCCESS, message="If the account exists and is not verified, an email has been sent")

@email_bp.route("/verify/<token>", methods=["POST"])
@limiter.limit("100 per hour")
def verify(token):
    try:
        decoded = decode_token(token)
        if decoded.get("type") != "email_verification":
            current_app.logger.warning(f"WARNING: /verify, type of token is {decoded.get("type")} not email_verification")
            return make_api_response(ResponseTypes.INCORRECT_TOKEN)
        if is_token_revoked(decoded):
            current_app.logger.warning(f"WARNING: /verify, token already verified/expired")
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Link already used or expired")
        user_id = decoded["sub"]
        user = db.session.get(User, user_id)

        if not user:
            current_app.logger.warning(f"WARNING: /verify, no user found for token")
            return make_api_response(ResponseTypes.NOT_FOUND, message="Verification failed")

        if user.is_confirmed:
            current_app.logger.warning(f"WARNING: /verify, user: {user_id} tried to verify account that is already verified")
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Account already varified")
    
        user.is_confirmed=True
        user.confirmed_at = datetime.now(timezone.utc)
        revoke_token(decoded["jti"], user.user_id)
        revoke_all_user_tokens(user.user_id, token_type="email_verification")
        db.session.commit()

        current_app.logger.info(f"INFO: /verify, user: {user_id} successfully verified their account")
        return make_api_response(ResponseTypes.SUCCESS, message="Verification succesful")
    except Exception as e:
        current_app.logger.error(f"ERROR: /verify, mail auth token exception occured: {e}")
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Invalid or expired link")
    
@email_bp.route("/reset_password_request", methods=["POST"])
@limiter.limit("500 per hour")   # for tests, 500 password resets for IP per hour, change before deployment to 5
def reset_password_request():
    user_data = request.get_json()
    email = user_data.get("email")
    
    if not email:
        return make_api_response(ResponseTypes.BAD_REQUEST)

    if not re.match(Constants.EMAIL_PATTERN, email):
        current_app.logger.warning(f"WARNING: /reset_password_request, email invalid: {email}")
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid email format")
        
    user = User.query.filter_by(email=email).first()  
    
    if user:
        revoke_all_user_tokens(user.user_id, token_type="password_reset")

        reset_token = create_access_token(
            identity=user.user_id,
            expires_delta=timedelta(minutes=Constants.RESET_PASSWORD_EXPIRES),
            additional_claims={"type": "password_reset"}                              
        )
        try:
            add_token_to_db(reset_token)
        except Exception as e:
            current_app.logger.error(f"ERROR: /reset_password_request, failed to add (to DB) reset token for user {user.user_id}: {e}")

        reset_url = url_for("email.reset_password", token=reset_token, _external=True) #this will have to be changed into deep link for app

        email_body = f"Hello! Click the link to reset your password: {reset_url}"
        
        try:
            send_email_async.delay('Reset password', email, email_body)
            current_app.logger.info(f"INFO: /reset_password_request, sent password reset mail for user: {user.user_id}")
        except Exception as e:
            current_app.logger.error(f"ERROR: /reset_password_request, DB exception occured: {e}")

    return make_api_response(ResponseTypes.SUCCESS, message="If user with that email is present in the database the mail with password reset will be sent")

@email_bp.route("/reset_password/<token>", methods=["POST"])
@limiter.limit("500 per hour")
def reset_password(token):
    decoded = None
    try:
        decoded = decode_token(token)
        is_revoked = is_token_revoked(decoded) 

        if is_revoked:
            current_app.logger.warning(f"WARNING: /reset_password, attempt to use expired link")
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Link has already been used or expired")
        
        if decoded.get("type") != "password_reset":
            current_app.logger.warning(f"WARNING: /reset_password, type of token is {decoded.get("type")} not password_reset")
            return make_api_response(ResponseTypes.INCORRECT_TOKEN)
        
        user_id = decoded["sub"]

    except Exception as e:
        current_app.logger.error(f"ERROR: /reset_password, exception occured: {e}")
        return make_api_response(ResponseTypes.UNAUTHORIZED)
    
    user = db.session.get(User, user_id)

    if not user:
        current_app.logger.warning(f"WARNING: /reset_password, user: {user_id} was not found")
        return make_api_response(ResponseTypes.NOT_FOUND, message="User not found")
    
    data = request.get_json()
    if not data or "new_password" not in data:
        return make_api_response(ResponseTypes.INVALID_CREDENTIALS, message="Missing new_password")
    
    new_password = data["new_password"]
    if not re.match(Constants.PASSWORD_PATTERN, new_password):
        return make_api_response(ResponseTypes.INVALID_CREDENTIALS, message="Incorrect password format")
    
    user.update_password(new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    db.session.commit()

    try:
        revoke_token(decoded["jti"], decoded["sub"])
        revoke_all_user_tokens(user.user_id, token_type="access")
        revoke_all_user_tokens(user.user_id, token_type="refresh")
    except Exception as e:
        current_app.logger.error(f"ERROR: /reset_password, DB exception occured: {e}")

    current_app.logger.info(f"INFO: /reset_password, password changed for user: {user_id}")
    return make_api_response(ResponseTypes.SUCCESS, message="Password changed successfully")

@email_bp.route("/confirm_change/<token>", methods=["POST"])
@limiter.limit("100 per hour")
def confirm_change(token):
    try:
        decoded = decode_token(token)
        if decoded.get("type") != "email_change":
            current_app.logger.warning(f"WARNING: /confirm_change, type of token is {decoded.get("type")} not email_change")
            return make_api_response(ResponseTypes.INCORRECT_TOKEN)
        if is_token_revoked(decoded):
            current_app.logger.warning(f"WARNING: /confirm_change, attempt to use expired link")
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Link already used or expired")
        user_id = decoded["sub"]
        user = db.session.get(User, user_id)

        if not user:
            current_app.logger.warning(f"WARNING: /confirm_change, user: {user_id} was not found")
            return make_api_response(ResponseTypes.NOT_FOUND, message="Email change failed")
    
        user.email = user.pending_email
        user.confirmed_at = datetime.now(timezone.utc)
        revoke_token(decoded["jti"], user.user_id)
        revoke_all_user_tokens(user.user_id, token_type="email_change")
        db.session.commit()

        current_app.logger.info(f"INFO: /confirm_change, user: {user_id} changed their email")
        return make_api_response(ResponseTypes.SUCCESS, message="Email changed succesfully")
    except Exception as e:
        current_app.logger.error(f"ERROR: /confirm_change, DB exception occured {e}")
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Invalid or expired link")