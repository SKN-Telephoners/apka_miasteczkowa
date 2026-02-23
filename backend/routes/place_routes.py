
from flask import jsonify, Blueprint, request, current_app
from backend.models import Event
from backend.extensions import db, limiter
from backend.constants import Constants
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required, get_current_user
from backend.helpers import validate_uuid, sanitize_input
import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.exc import SQLAlchemyError
from backend.models import Review, User , Place
place = Blueprint("place", __name__, url_prefix="api/place")
local_tz = ZoneInfo("Europe/Warsaw")   


@place.route("/get_place_details/<place_id>", methods=["GET"])
@jwt_required()
def get_place_details(place_id : int):
    user =get_current_user()
    try:
        places = Place.query.filter_by(id=place_id).first()
    except Exception:
        return jsonify({"message": "Invalid place ID format"}), 400
    if places is None:
        return {
            "message": "Place doesn't exist"
        }, 404
    return jsonify({
        places.to_dict()
        
    }), 200         