import datetime
from backend.extensions import db
from flask_jwt_extended import decode_token
from backend.models import TokenBlocklist
from sqlalchemy.exc import NoResultFound

def add_token_to_db(encoded_token):
    decoded_token = decode_token(encoded_token)
    token_expires = datetime.datetime.fromtimestamp(decoded_token["exp"], tz=datetime.timezone.utc)
    token = TokenBlocklist(
        jti=decoded_token["jti"],
        token_type=decoded_token["type"],
        user_id=decoded_token["sub"],
        expires=token_expires
    )

    try:
        db.session.add(token)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error adding token to blocklist: {e}")
        raise


def revoke_token(token_jti, user_id):
    try:
        token = TokenBlocklist.query.filter_by(jti=token_jti, user_id=user_id).one()
        if token:
            token.revoked_at = datetime.datetime.now(datetime.timezone.utc)
            db.session.commit()
            return True
    except NoResultFound:
        print(f"Token with jti {token_jti} for user {user_id} not found")
        db.session.rollback()
        return False
    except Exception as e:
        print(f"Error revoking token: {e}")
        return False
    return False

def is_token_revoked(jwt_payload):
    jti = jwt_payload["jti"]
    user_id = jwt_payload["sub"]
    try:
        token = TokenBlocklist.query.filter_by(jti=jti, user_id=user_id).one_or_none()
        if token is None:
            return True
        return token.revoked_at is not None
    except NoResultFound:
        #change before deployment to line: "return True" for security purpouses 
        raise Exception(f"Could not find token {jti}")

def revoke_all_user_tokens(user_id):
    try:
        tokens = TokenBlocklist.query.filter_by(user_id=user_id, revoked_at=None).all()
        for token in tokens:
            token.revoked_at = datetime.datetime.now(datetime.timezone.utc)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error revoking all tokens from user: {user_id}: {e}")
        raise