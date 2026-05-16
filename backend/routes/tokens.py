from backend.models import User
from backend.responses import ResponseTypes, make_api_response
from backend.extensions import db, jwt
from backend.helpers import is_token_revoked

'''
Input: jwt_header: <dict>, jwt_payload: <dict>
Action: Internal callback for Flask-JWT-Extended. It calls is_token_revoked to check the database blocklist
Output: bool (True if token is revoked, False otherwise)
'''
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return is_token_revoked(jwt_payload)

'''
Input: error: <str>
Action: Triggered when a request lacks a valid JWT.
Data sent to the frontend: {"message": "Missing or invalid token"}
Output: 401 Unauthorized
'''
@jwt.unauthorized_loader
def unauthorized_callback(error):
    return make_api_response(ResponseTypes.UNAUTHORIZED)

'''
Input: error: <str>
Action: Triggered when the JWT is malformed or invalid.
Data sent to the frontend: {"message": "Incorrect token"}
Output: 401 Unauthorized
'''
@jwt.invalid_token_loader
def invalid_token_callback(error):
    return make_api_response(ResponseTypes.INCORRECT_TOKEN)

'''
Input: jwt_header: <dict>, jwt_payload: <dict>
Action: Triggered when a token's expiration time has passed.
Data sent to the frontend: {"message": "Expired token"}
Output: 401 Unauthorized
'''
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return make_api_response(ResponseTypes.INCORRECT_TOKEN, message="Expired token")

'''
Input: jwt_header: <dict>, jwt_payload: <dict>
Action: Retrieves the User object from the database using the identity (sub) stored in the JWT payload.
Output: <User_Model_Object> or None
'''
@jwt.user_lookup_loader
def load_user(jwt_header, jwt_payload):
    user_id = jwt_payload["sub"]
    return db.session.get(User, user_id)