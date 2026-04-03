from datetime import datetime, timezone
from backend.extensions import db
from flask_jwt_extended import decode_token
from backend.models import TokenBlocklist
from backend.models.event import Event_visibility
from sqlalchemy.exc import NoResultFound
import uuid
import bleach

def add_token_to_db(encoded_token):
    decoded_token = decode_token(encoded_token)
    token_expires = datetime.fromtimestamp(decoded_token["exp"], tz=timezone.utc)
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
            token.revoked_at = datetime.now(timezone.utc)
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
    except Exception as e:
        print(f"Database error in is_token_revoked: {e}")
        return True

def revoke_all_user_tokens(user_id, token_type=None):
    try:
        query = TokenBlocklist.query.filter_by(user_id=user_id, revoked_at=None)
        if token_type:
            query = query.filter_by(token_type=token_type)

        tokens = query.all()
        for token in tokens:
            token.revoked_at = datetime.now(timezone.utc)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error revoking all tokens from user: {user_id}: {e}")
        raise

def validate_uuid(uuid_val):
    if isinstance(uuid_val, uuid.UUID):
        return uuid_val
    try:
        return uuid.UUID(str(uuid_val))
    except (ValueError, TypeError, AttributeError):
        return None

def sanitize_input(text):
    if text is None:
        return ""
    clean_text = bleach.clean(str(text), tags=[], attributes=[], strip=True)
    return clean_text

def has_event_access(user_id, event):
    if not event.is_private:
        return True
    if event.creator_id == user_id:
        return True

    access = Event_visibility.query.filter_by(
        event_id=event.event_id, 
        shared_with=user_id
    ).first()
    
    return access is not None
