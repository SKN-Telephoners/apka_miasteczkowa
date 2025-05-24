import datetime
from backend.extensions import db
from flask_jwt_extended import decode_token
from backend.models import TokenBlocklist
from sqlalchemy.exc import NoResultFound

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