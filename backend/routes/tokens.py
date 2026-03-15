from backend.models import User
from backend.responses import ResponseTypes, make_api_response
from backend.extensions import db, jwt
from backend.app import app
from backend.helpers import is_token_revoked
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, set_access_cookies
from datetime import datetime, timezone, timedelta

@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(seconds=10)) 
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        return response

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return is_token_revoked(jwt_payload)

@jwt.unauthorized_loader
def unauthorized_callback(error):
    return make_api_response(ResponseTypes.UNAUTHORIZED)

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return make_api_response(ResponseTypes.INCORRECT_TOKEN)

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return make_api_response(ResponseTypes.INCORRECT_TOKEN, message="Expired token")

@jwt.user_lookup_loader
def load_user(jwt_header, jwt_payload):
    user_id = jwt_payload["sub"]
    return db.session.get(User, user_id)