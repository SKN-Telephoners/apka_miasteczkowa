from flask import Blueprint, request, jsonify, url_for
from backend.models import User
from backend.extensions import db, mail, limiter
from flask_jwt_extended import create_access_token, decode_token
from backend.helpers import add_token_to_db, revoke_token, is_token_revoked, revoke_all_user_tokens
import re
from flask_mail import Message
from datetime import timedelta

email_bp = Blueprint("email", __name__, url_prefix="/api/email")

@email_bp.route("/verify_request",methods=["POST"])
def verify_request():
    user_data = request.get_json()

    if not user_data or not "email" in user_data.keys():
        return jsonify({"message":"Bad request"}),400
    
    email=user_data["email"]
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"message": "There is no user with such email"}), 401
    if user.is_confirmed:
        return jsonify({"message": "User already confirmed"}), 400
    
    auth_token = create_access_token(identity=user.email)
    auth_url=url_for("email.verify", token=auth_token, _external=True)
        
    msg = Message(
            'Auth account',
            recipients=[email],
            body=f"Hello! Click the link to authorize your account: {auth_url}"
        )
    mail.send(msg)

    return{
        "message": "Email sent successfully"
    },200

@email_bp.route("/verify/<token>", methods=["GET"])
def verify(token):
    decoded = decode_token(token)
    user_email = decoded["sub"]

    user = User.query.filter_by(email=user_email).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    if user.is_confirmed:
        return jsonify({"message": "User already confirmed"}), 400
    
    user.is_confirmed=True
    db.session.commit()

    return {
        "message": "Verification succesful"
    }, 200

@email_bp.route("/reset_password_request", methods=["POST"])
@limiter.limit("500 per hour")   # for tests, 500 password resets for IP per hour, change before deployment to 5
def reset_password_request():
    user_data = request.get_json()
    email = user_data.get("email")
    
    if not email:
        return jsonify({"message": "Bad request"}), 400

    email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if not re.match(email_pattern, email):
        return jsonify({"message": "Invalid email format"})
        
    user = User.query.filter_by(email=email).first()  
    
    #now there will be multiple active tokens for password resetting (we don't want that) - to be fixed
    if user:
        reset_token = create_access_token(
            identity=user.user_id,
            expires_delta=timedelta(minutes=15),
            additional_claims={"type": "password_reset"}                              
        )
        try:
            add_token_to_db(reset_token)
        except Exception as e:
            print(f"Failed to log reset token for user {user.user_id}: {e}")

        reset_url = url_for("main.reset_password", token=reset_token, _external=True) #this will have to be changed into deep link for app

        msg = Message(
            'Reset password',
            recipients=[email],
            body=f"Hello! Click the link to reset your password: {reset_url}"
        )
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Error sending email with password reset: {e}")

    return {
        "message": "If user with that email is present in the database the "
    }, 200

@email_bp.route("/reset_password/<token>", methods=["POST"])
@limiter.limit("500 per hour")
def reset_password(token):
    decoded = None
    try:
        decoded = decode_token(token)
        is_revoked = is_token_revoked(decoded) 

        if is_revoked:
             return jsonify({"message": "Link has already been used or expired"}), 400
        
        if decoded.get("type") != "password_reset":
            return jsonify({"message": "Invalid token type"}), 400
        
        user_id = decoded["sub"]

    except Exception:

        return jsonify({"message": "Invalid or expired token"}), 400
    
    user = User.query.filter_by(user_id=user_id).first()

    if not user:
        return jsonify({"message": "User not found"}), 404
    
    data = request.get_json()
    if not data or "new_password" not in data:
        return jsonify({"message": "Missing new_password"}), 400
    
    password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,72}$"
    new_password = data["new_password"]
    if not re.match(password_pattern, new_password):
        return jsonify({"message": "Incorrect password format"}), 400
    
    user.update_password(new_password)
    db.session.commit()

    try:
        revoke_token(decoded["jti"], decoded["sub"])
        revoke_all_user_tokens(user.user_id)
    except Exception as e:
        print(f"Failed to revoke all tokens after password reset: {e}")

    return jsonify({
        "message": "Password changed successfully"
    }), 200