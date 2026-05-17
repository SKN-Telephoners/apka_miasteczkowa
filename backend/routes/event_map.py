from flask import Blueprint, request, current_app
from backend.models.event import Event, Event_visibility, Location
from backend.models import User
from backend.extensions import db, limiter
from backend.constants import Constants
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required, get_current_user
from backend.helpers import sanitize_input
from datetime import datetime, timezone
from sqlalchemy import or_, and_, exists
from .event_helpers import parse_location_coordinates
from zoneinfo import ZoneInfo

map_bp = Blueprint("map", __name__, url_prefix="/api/events")
local_tz = ZoneInfo("Europe/Warsaw")

'''
Input: Query Parameter { "location": <str> }, Header { "Authorization": "Bearer <Access_Token>" }
Action: Searches the Event_location table for a predefined location name and returns its stored coordinates
Data sent to the frontend: {"coordinates": <str>}
Output: 200 OK (or 404/400/500 on error)
'''
@map_bp.route("/get_coordinates", methods=["GET"])
@limiter.limit("1000 per second")
@jwt_required()
def get_coordinates():
    location_name = request.args.get('location') # request for that endpoint ex: /api/events/get_coordinates?location=Krakow
    location_name = str(sanitize_input(location_name))
    if not location_name or location_name == "":
        return make_api_response(ResponseTypes.INVALID_DATA, message="Location name must not be empty")

    if len(location_name) > Constants.MAX_LOCATION_LEN:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Location name too long")

    query = db.session.query(Location).filter_by(location_name=location_name).first()    
    
    if not query:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Location of that name not found")
    
    coordinates = query.coordinates
    current_app.logger.info(f"INFO: /get_coordinates, successfully fetched coordinates for {location_name}")
    return make_api_response(ResponseTypes.SUCCESS, data={"coordinates": str(coordinates)})

'''
Input: Header { "Authorization": "Bearer <Access_Token>" }
Action: Retrieves all upcoming events visible to the user that contain valid coordinate data for map
Data sent to the frontend: {"data": [{
    "event_id": <str>, 
    "name": <str>, 
    "date": <str>, 
    "time": <str>, 
    "location": <str>, 
    "location_coordinates": [<float>, <float>], 
    "creator_username": <str>, 
    "is_private": <bool>}]}
Output: 200 OK (or 500 on error)
'''
@map_bp.route("/map", methods=["GET"])
@limiter.limit("600 per minute")
@jwt_required()
def map_events():
    try:
        user = get_current_user()
        user_id = user.user_id
        now_utc = datetime.now(timezone.utc)

        visibility_exists = exists().where(
            and_(
                Event_visibility.event_id == Event.event_id,
                Event_visibility.shared_with == user_id,
            )
        )

        events = db.session.query(Event, User.username).join(
            User, Event.creator_id == User.user_id
        ).filter(
            Event.date_and_time >= now_utc,
            or_(
                Event.is_private == False,
                Event.creator_id == user_id,
                visibility_exists,
            )
        ).order_by(Event.date_and_time.asc()).all()

        final_map_data = []

        for event, creator_name in events:
            coords = parse_location_coordinates(event.location)
            if coords is None:
                continue

            local_dt = event.date_and_time.astimezone(local_tz)

            final_map_data.append({
                "event_id": str(event.event_id),
                "name": event.event_name,
                "date": local_dt.strftime("%d.%m.%Y"),
                "time": local_dt.strftime("%H:%M"),
                "location": event.location,
                "location_coordinates": coords,
                "creator_username": creator_name,
                "is_private": event.is_private
            })

        return make_api_response(
            ResponseTypes.SUCCESS,
            data={"data": final_map_data},
        )
    except Exception as e:
        current_app.logger.error(f"ERROR: /map, exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
