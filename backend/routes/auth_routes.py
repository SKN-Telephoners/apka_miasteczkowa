from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity, get_jwt
from backend.extensions import limiter
from backend.services.auth_service import register_user_service, login_user_service
from backend.services.token_service import add_token_to_db, revoke_token
from backend.helpers.validators import validate_registration_data

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/api/register", methods=["POST"])
@limiter.limit("5 per hour")
def register_user():
    data = request.get_json()
    valid, message = validate_registration_data(data)
    if not valid:
        return jsonify({"message": message}), 400

    result, status = register_user_service(data)
    return jsonify(result), status


@auth_bp.route("/api/login", methods=["POST"])
@limiter.limit("5 per 15 minutes")
def login_user():
    data = request.get_json()
    result, status = login_user_service(data)
    return jsonify(result), status


@auth_bp.route("/api/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_token():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    add_token_to_db(access_token)
    return jsonify(access_token=access_token), 200


@auth_bp.route("/api/revoke_access", methods=["DELETE"])
@jwt_required()
def revoke_access():
    jti = get_jwt()["jti"]
    user_id = get_jwt_identity()
    revoke_token(jti, user_id)
    return jsonify(message="Access token revoked"), 200


@auth_bp.route("/api/revoke_refresh", methods=["DELETE"])
@jwt_required(refresh=True)
def revoke_refresh():
    jti = get_jwt()["jti"]
    user_id = get_jwt_identity()
    revoke_token(jti, user_id)
    return jsonify(message="Refresh token revoked"), 200
