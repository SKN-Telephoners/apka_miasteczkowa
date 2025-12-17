from flask import jsonify

class ResponseTypes:
    #2xx
    SUCCESS = ("Operation successful", 200)
    CREATED = ("Resource created successfully", 201)
    LOGIN_SUCCESS = ("Login successful", 200)
    LOGOUT_SUCCESS = ("Logged out successfully", 200)
    TOKEN_REVOKED = ("Token revoked successfully", 200)

    #4xx
    BAD_REQUEST = ("Bad request", 400)
    UNAUTHORIZED = ("Missing or invalid token", 401)
    INCORRECT_TOKEN = ("Incorrect token", 401)
    FORBIDDEN = ("Access forbidden", 403)
    NOT_FOUND = ("Resource not found", 404)
    CONFLICT = ("Resource already exisst", 409)
    INVALID_CREDENTIALS = ("Invalid username or password", 401)
    INVALID_DATA = ("Invalid data format", 400)
    ACCOUNT_NOT_VERIFIED = ("Account not verified. Please check your email.", 403)

    #5xx
    SERVER_ERROR = ("Internal server error", 400)

def make_api_response(response_type, data=None, message=None):
    default_msg, status_code = response_type

    final_msg = message if message else default_msg

    response_body = {
        "message": final_msg
    }

    if data:
        response_body.update(data)

    return jsonify(response_body), status_code