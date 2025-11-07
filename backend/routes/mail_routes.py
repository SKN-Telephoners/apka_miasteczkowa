from flask import Blueprint, request, jsonify
from flask_jwt_extended import decode_token
from backend.models import User
from backend.extensions import db
from backend.services.mail_service import send_verification_email, send_reset_email

mail_bp = Blueprint("mail", __name__)

@mail_bp.route("/reset_password_request", methods=["POST"])
def reset_password_request():
    data = request.get_json()
    if not data or "email" not in data:
        return jsonify({"message": "Bad request"}), 400

    result, status = send_reset_email(data["email"])
    return jsonify(result), status


@mail_bp.route("/reset_password/<token>", methods=["POST"])
def reset_password(token):
    decoded = decode_token(token)
    email = decoded["sub"]

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    new_password = data.get("new_password")
    if not new_password:
        return jsonify({"message": "Missing new password"}), 400

    user.update_password(new_password)
    db.session.commit()
    return jsonify({"message": "Password changed successfully"}), 200


@mail_bp.route("/mail_auth_request", methods=["POST"])
def mail_auth_request():
    data = request.get_json()
    if not data or "email" not in data:
        return jsonify({"message": "Bad request"}), 400

    result, status = send_verification_email(data["email"])
    return jsonify(result), status


@mail_bp.route("/mail_auth/<token>", methods=["GET"])
def mail_auth(token):
    decoded = decode_token(token)
    email = decoded["sub"]

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    if user.is_confirmed:
        return jsonify({"message": "User already confirmed"}), 400

    user.is_confirmed = True
    db.session.commit()
    return jsonify({"message": "Verification successful"}), 200
