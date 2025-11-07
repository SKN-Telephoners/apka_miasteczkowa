from flask import url_for
from flask_mail import Message
from flask_jwt_extended import create_access_token
from backend.models import User
from backend.extensions import db, mail

def send_verification_email(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return {"message": "User not found"}, 404

    if user.is_confirmed:
        return {"message": "User already confirmed"}, 400

    token = create_access_token(identity=email)
    verify_url = url_for("mail.mail_auth", token=token, _external=True)

    msg = Message(
        "Verify your account",
        recipients=[email],
        body=f"Click to verify your account: {verify_url}"
    )
    mail.send(msg)

    return {"message": "Verification email sent"}, 200


def send_reset_email(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return {"message": "User not found"}, 404

    token = create_access_token(identity=email)
    reset_url = url_for("mail.reset_password", token=token, _external=True)

    msg = Message(
        "Reset your password",
        recipients=[email],
        body=f"Click to reset your password: {reset_url}"
    )
    mail.send(msg)

    return {"message": "Reset email sent successfully"}, 200
