from flask import Blueprint, request, current_app
from backend.models.event import Event, Event_visibility, Location, Event_participants
from backend.models import User
from backend.extensions import db, limiter, redis_client
from backend.constants import Constants
from backend.responses import ResponseTypes, make_api_response
from backend.helpers import validate_uuid, sanitize_input, get_event_cache_key, cache_event_data
from .event_helpers import serialize_event_payload
import json
from flask_jwt_extended import jwt_required, get_current_user
from backend.helpers import sanitize_input
from datetime import datetime, timezone, timedelta
from sqlalchemy import or_, and_, exists
from .event_helpers import parse_location_coordinates, get_friend_ids
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
/api/events/map?visibility=all&participation=all&created_window=all&friends_only=false&friends_attending=false
Input: Header { "Authorization": "Bearer <Access_Token>" } 
       Query Params: visibility (all/public/private), participation (all/joined/not_joined), 
       friends_only (bool), friends_attending (bool).
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

        visibility = request.args.get("visibility", default="all", type=str).lower()
        participation = request.args.get("participation", default="all", type=str).lower()
        created_window = request.args.get("created_window", default="all", type=str).lower()
        sort_mode = request.args.get("sort_mode", default="default", type=str).lower()
        show_friends_only = request.args.get("friends_only", default="false").lower() == "true"
        show_friends_attending = request.args.get("friends_attending", default="false").lower() == "true"


        visibility_subquery = db.session.query(Event_visibility.event_id).filter(
            Event_visibility.event_id == Event.event_id,
            Event_visibility.shared_with == user_id,
        )

        participation_subquery = db.session.query(Event_participants.event_id).filter(
            Event_participants.event_id == Event.event_id,
            Event_participants.user_id == user_id
        )

        query = Event.query.filter(
            Event.date_and_time >= now_utc,
            or_(
                Event.is_private == False,
                Event.creator_id == user_id,
                visibility_subquery.exists(),
                participation_subquery.exists()
            )
        )

        if show_friends_only or show_friends_attending:
            friend_ids = get_friend_ids(user_id)

            if not friend_ids:
                current_app.logger.info(f"INFO: /map, user {user_id} filtered by friends but has no friends :(")
                return make_api_response(ResponseTypes.SUCCESS, data={"data": []})
            
            friend_conditions = []
            if show_friends_only:
                friend_conditions.append(Event.creator_id.in_(friend_ids))
            if show_friends_attending:
                friends_in_event = db.session.query(Event_participants.event_id).filter(
                    Event_participants.user_id.in_(friend_ids)
                )
                friend_conditions.append(Event.event_id.in_(friends_in_event))
            
            query = query.filter(or_(*friend_conditions))
            current_app.logger.info(f"INFO: /map, user {user_id} filtered by friends_only={show_friends_only}, friends_attending={show_friends_attending}")

        events = query.distinct().all() 

        if visibility == "public":
            query = query.filter(Event.is_private == False)
        elif visibility == "private":
            query = query.filter(Event.is_private == True)

        if participation != "all":
            participation_exists = db.session.query(Event_participants.event_id).filter(
                Event_participants.event_id == Event.event_id,
                Event_participants.user_id == user_id
            ).exists()

            query = query.filter(participation_exists if participation == "joined" else ~participation_exists)

        events = query.distinct().order_by(Event.date_and_time.asc()).all()

        if created_window != "all":
            if created_window == "today":
                start_date = now_utc - timedelta(days=1)
            elif created_window == "week":
                start_date = now_utc - timedelta(weeks=1)
            elif created_window == "month":
                start_date = now_utc - timedelta(days=30)
            elif created_window == "year":
                start_date = now_utc - timedelta(days=365)
            if created_window == "older":
                query = query.filter(Event.created_at < (now_utc - timedelta(days=365)))
            else:
                query = query.filter(Event.created_at >= start_date)

        if sort_mode == "members_asc": 
            query = query.order_by(Event.participant_count.asc())
        elif sort_mode == "members_desc": 
            query = query.order_by(Event.participant_count.desc())
        elif sort_mode == "comments_asc": 
            query = query.order_by(Event.comment_count.asc())
        elif sort_mode == "comments_desc": 
            query = query.order_by(Event.comment_count.desc())
        else:
            query = query.order_by(Event.date_and_time.asc())

        creator_ids = {e.creator_id for e in events}
        creator_users = User.query.filter(User.user_id.in_(creator_ids)).all() if creator_ids else []
        creator_lookup = {str(u.user_id): u for u in creator_users}

        final_map_data = []

        for event in events:
            eid_str = str(event.event_id)
            cached_val = redis_client.get(get_event_cache_key(eid_str))

            if cached_val:
                full_event_data = json.loads(cached_val)
            else:
                full_event_data = serialize_event_payload(event, None, creator_lookup, set())
                cache_event_data(eid_str, full_event_data)
                
            coords = parse_location_coordinates(event.location)
            if coords is None:
                continue

            map_item = {
                "event_id": eid_str,
                "name": full_event_data.get("name"),
                "date": full_event_data.get("date"),
                "time": full_event_data.get("time"),
                "location": full_event_data.get("location"),
                "location_coordinates": coords,
                "creator_username": full_event_data.get("creator_username"),
                "is_private": full_event_data.get("is_private")
            }
            final_map_data.append(map_item)

        current_app.logger.info(f"INFO: /map, user {user_id} fetched {len(final_map_data)} events for map")

        return make_api_response(
            ResponseTypes.SUCCESS,
            data={"data": final_map_data},
        )
    except Exception as e:
        current_app.logger.error(f"ERROR: /map, exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
