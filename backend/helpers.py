from datetime import datetime, timezone
from backend.extensions import db
from flask_jwt_extended import decode_token
from backend.models import TokenBlocklist
from backend.models.event import Event_visibility
from sqlalchemy.exc import NoResultFound
import uuid
import bleach
from backend.extensions import redis_client
import json
from backend.constants import Constants
from flask import current_app

'''
Input: encoded_token: <jwt_str>
Action: Decodes the provided JWT string to extract the jti (unique ID), sub (user ID), and exp (expiration). It then creates a new entry in the TokenBlocklist database table to track the token's validity
Output: None (or raises an Exception on database error)
'''
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


'''
Input: token_jti: <str>, user_id: <uuid>
Action: Searches the TokenBlocklist for a specific token associated with the given user. If found, it sets the revoked_at timestamp to the current time, blacklisting the token
Output: bool (True if successfully revoked, False if token not found or on error).
'''
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

'''
Input: jwt_payload: <dict> (containing jti and sub claims).
Action: Queries the database to check if the specific token (via its JTI) has been marked as revoked. If the token record is missing or the revoked_at column is populated, the token is considered invalid.
Output: bool (True if the token is revoked/invalid, False if it is active).
'''
def is_token_revoked(jwt_payload):
    jti = jwt_payload["jti"]
    user_id = jwt_payload["sub"]
    try:
        token_query = db.select(TokenBlocklist).filter_by(jti=jti, user_id=user_id)
        token = db.session.execute(
            token_query, 
            bind_arguments={'bind_key': 'readonly'}
        ).scalar_one_or_none()
        
        if token is None:
            return True
        return token.revoked_at is not None
    except Exception as e:
        print(f"Database error in is_token_revoked: {e}")
        return True

'''
Input: user_id: <uuid>, token_type: <str> (optional filter like "access", "refresh", or "email_verification").
Action: Locates all active (non-revoked) tokens in the database for a specific user and marks them all as revoked simultaneously
Output: bool (or raises an Exception on database error)
'''
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

'''
Input: <any> (usually str or uuid.UUID object)
Action: Attempts to convert a value into a valid UUID object
Output: uuid.UUID object or None if invalid.
'''
def validate_uuid(uuid_val):
    if isinstance(uuid_val, uuid.UUID):
        return uuid_val
    try:
        return uuid.UUID(str(uuid_val))
    except (ValueError, TypeError, AttributeError):
        return None

'''
Input: <str> or None
Action: Strips all HTML tags and attributes using the bleach library
Output: Cleaned <str>
'''
def sanitize_input(text):
    if text is None:
        return ""
    clean_text = bleach.clean(str(text), tags=[], attributes=[], strip=True)
    return clean_text

'''
Input: user_id: <uuid>, event: <Event_Model_Object>
Action: Logic gate to check if a user can view an event (Public OR Creator OR Shared With)
Output: bool
'''
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

'''
Input: event_id: <uuid/str>
Action: Generates a standardized string key for Redis storage using the format "event:v1:<event_id>".
Output: <str:cache_key>
'''
def get_event_cache_key(event_id):
    return f"event:v1:{event_id}"

'''
Input: event_id: <uuid/str>, data: <dict>
Action: Prepares event data for long-term storage by stripping dynamic user-specific flags (such as is_participating, is_joined, and participation_count). It then serializes the dictionary to JSON and saves it in Redis with a pre-configured TTL (Time To Live)
Output: None (Logs error if Redis fails).
'''
def cache_event_data(event_id, data):
    try:
        cache_ready_data = data.copy()
        cache_ready_data.pop("is_participating", None)
        cache_ready_data.pop("is_joined", None)
        cache_ready_data.pop("participation_count", None)
        redis_client.setex(
            get_event_cache_key(event_id),
            Constants.CACHE_TTL,
            json.dumps(cache_ready_data)
        )
    except Exception as e:
        current_app.logger.error(f"Redis Set Error: {e}")

'''
Input: event_id: <uuid/str>
Action: Immediately deletes the cached data for a specific event from Redis. This is used when an event is updated, deleted, or joined to ensure data consistency
Output: None (Logs error if Redis fails).
'''
def invalidate_event_cache(event_id):
    try:
        redis_client.delete(get_event_cache_key(event_id))

    except Exception as e:
        current_app.logger.error(f"Redis Delete Error: {e}")

'''
Input: event_id: <uuid/str>
Action: Attempts to retrieve the serialized JSON data from Redis for the given event ID. If found, it deserializes the JSON back into a Python dictionary
Output: <dict:cached_data> or None (if cache miss or Redis error)
'''
def get_cached_event(event_id):
    try:
        cached = redis_client.get(get_event_cache_key(event_id))
        return json.loads(cached) if cached else None
    except Exception as e:
        current_app.logger.error(f"Redis Get Error: {e}")
        return None
