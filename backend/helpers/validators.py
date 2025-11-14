import datetime
from backend.extensions import db
from flask_jwt_extended import decode_token
from backend.models import TokenBlocklist
from sqlalchemy.exc import NoResultFound
import re

MAX_EMAIL_LEN = 320
MAX_USERNAME_LEN = 32
MIN_USERNAME_LEN = 3

def validate_registration_data(data):
    if not data or not {"username", "password", "email"}.issubset(data.keys()):
        return False, "Missing required fields"

    email = data["email"]
    username = data["username"]

    email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if (
        not re.match(email_pattern, email)
        or len(email) > MAX_EMAIL_LEN
        or not (MIN_USERNAME_LEN <= len(username) <= MAX_USERNAME_LEN)
    ):
        return False, "Invalid username or email"

    return True, ""

def add_token_to_db(encoded_token):
    decoded_token = decode_token(encoded_token)

    token = TokenBlocklist(
        jti=decoded_token["jti"],
        token_type=decoded_token["type"],
        user_id=decoded_token["sub"],
        expires=datetime.date.fromtimestamp(decoded_token["exp"])
    )

    db.session.add(token)
    db.session.commit()
    
def revoke_token(token_jti, user_id):
    try:
        token = TokenBlocklist.query.filter_by(jti=token_jti, user_id=user_id).one()
        token.revoked_at = datetime.datetime.now()
        db.session.commit()
    except NoResultFound:
        raise Exception(f"Could not find token {token_jti}")

def is_token_revoked(jwt_payload):
    jti = jwt_payload["jti"]
    user_id = jwt_payload["sub"]
    try:
        token = TokenBlocklist.query.filter_by(jti=jti, user_id=user_id).one()
        return token.revoked_at is not None
    except NoResultFound:
        raise Exception(f"Could not find token {jti}")