from flask import url_for
from flask_mail import Message
from flask_jwt_extended import create_access_token, create_refresh_token
from backend.models import User
from backend.extensions import db, mail
from backend.services.token_service import add_token_to_db

def register_user_service(data):
    username = data["username"]
    email = data["email"]
    password = data["password"]

    if User.query.filter_by(username=username).first():
        return {"message": "Username already taken"}, 409

    if User.query.filter_by(email=email).first():
        return {"message": "Email already exists"}, 409

    user = User(username=username, password=password, email=email)
    db.session.add(user)
    db.session.commit()

    # Send verification email
    token = create_access_token(identity=email)
    auth_url = url_for("mail.mail_auth", token=token, _external=True)

    msg = Message(
        "Verify your account",
        recipients=[email],
        body=f"Hello! Click the link to authorize your account: {auth_url}"
    )
    mail.send(msg)

    return {"message": "Registration successful"}, 201


def login_user_service(data):
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if not user or not user.validate_password(password):
        return {"message": "Invalid username or password"}, 401

    if not user.is_confirmed:
        return {"message": "Please verify your account first"}, 403

    access_token = create_access_token(identity=user.user_id)
    refresh_token = create_refresh_token(identity=user.user_id)

    add_token_to_db(access_token)
    add_token_to_db(refresh_token)

    return {
        "message": "Login successful",
        "user": {"username": user.username},
        "access_token": access_token,
        "refresh_token": refresh_token
    }, 200
