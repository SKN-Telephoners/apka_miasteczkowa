from backend.models import User
from backend.responses import ResponseTypes, make_api_response
from backend.extensions import db, jwt
from backend.helpers import is_token_revoked

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