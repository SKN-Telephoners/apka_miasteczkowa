from flask import Blueprint, request, current_app
from backend.models.event import Event, Event_visibility, Event_participants, Invites, InviteRequestStatus, Pictures, Location
from backend.models import User, Friendship
from backend.extensions import db, limiter, redis_client
from backend.constants import Constants
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required, get_current_user
from backend.helpers import validate_uuid, sanitize_input, get_event_cache_key, invalidate_event_cache, get_cached_event, cache_event_data
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.exc import SQLAlchemyError
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from sqlalchemy import or_, and_, exists
from sqlalchemy.orm import joinedload
from backend.notifications.signals import (
    invite_created, 
    event_new_participant, 
    invite_status_update, 
    joined_event_updated,
    joined_event_deleted,
    friend_new_private_event,
    friend_new_public_event
)
import json

events_bp = Blueprint("events", __name__, url_prefix="/api/events")
local_tz = ZoneInfo("Europe/Warsaw")

'''
Input: raw_location: <str> / [<float:lng>, <float:lat>] / <json_str>
Action: Standardizes location data. It checks if the input is a coordinate pair, a JSON string of coordinates, or a plain text name. It validates that coordinates are within geographical ranges and returns a formatted string like "[lng,lat]" or a sanitized string
Data sent to the frontend: N/A (Internal use)
Output: tuple (<str:normalized_val> or None, <str:error_message> or None)
'''
def normalize_location_input(raw_location):
    if raw_location is None:
        return None, "Location is required"

    parsed_coords = None

    if isinstance(raw_location, (list, tuple)) and len(raw_location) == 2:
        parsed_coords = raw_location
    else:
        location_text = sanitize_input(str(raw_location)).strip()
        if not location_text:
            return None, "Location is required"

        try:
            parsed_json = json.loads(location_text)
            if isinstance(parsed_json, (list, tuple)) and len(parsed_json) == 2:
                parsed_coords = parsed_json
        except (TypeError, ValueError, json.JSONDecodeError):
            parsed_json = None

        if parsed_coords is None and "," in location_text and not location_text.startswith("["):
            parts = [p.strip() for p in location_text.split(",")]
            if len(parts) == 2:
                parsed_coords = parts

        if parsed_coords is None:
            if len(location_text) > Constants.MAX_LOCATION_LEN:
                return None, "Location name is too long"
            return location_text, None

    try:
        lng = float(parsed_coords[0])
        lat = float(parsed_coords[1])
    except (TypeError, ValueError):
        return None, "Invalid location coordinates format"

    if not (-180.0 <= lng <= 180.0 and -90.0 <= lat <= 90.0):
        return None, "Location coordinates are out of range"

    normalized = f"[{lng:.6f},{lat:.6f}]"
    if len(normalized) > Constants.MAX_LOCATION_LEN:
        return None, "Location name is too long"

    return normalized, None


'''
Input: raw_location: <str> / <list>
Action: Specifically attempts to extract numerical longitude and latitude from a database string or list
Data sent to the frontend: N/A (Internal use)
Output: [<float:lng>, <float:lat>] or None
'''
def parse_location_coordinates(raw_location):
    if raw_location is None:
        return None

    if isinstance(raw_location, (list, tuple)) and len(raw_location) == 2:
        candidate = raw_location
    else:
        location_text = str(raw_location).strip()
        if not location_text:
            return None

        try:
            candidate = json.loads(location_text)
        except (TypeError, ValueError, json.JSONDecodeError):
            return None

    if not isinstance(candidate, (list, tuple)) or len(candidate) != 2:
        return None

    try:
        lng = float(candidate[0])
        lat = float(candidate[1])
    except (TypeError, ValueError):
        return None

    if not (-180.0 <= lng <= 180.0 and -90.0 <= lat <= 90.0):
        return None

    return [lng, lat]


'''
Input: event: <Event_Model>, user_id: <uuid>, creator_lookup: <dict>, participating_event_ids: <set>
Action: Converts a database Event object into a comprehensive dictionary for the frontend. It calculates timezones (Europe/Warsaw), generates Cloudinary URLs for event pictures and the creator's profile picture, and sets flags for participation status
Data sent to the frontend: N/A (Internal use - returned to route)
Output: <dict:Serialized_Event_Object>
'''
def serialize_event_payload(event, user_id, creator_lookup, participating_event_ids):
    local_dt = event.date_and_time.astimezone(local_tz) if event.date_and_time else None
    creator = creator_lookup.get(str(event.creator_id))

    return {
        "id": str(event.event_id),
        "event_id": str(event.event_id),
        "name": event.event_name,
        "description": event.description,
        "date": local_dt.strftime("%d.%m.%Y") if local_dt else None,
        "time": local_dt.strftime("%H:%M") if local_dt else None,
        "location": event.location,
        "creator_id": str(event.creator_id),
        "pictures": [
            {
                "cloud_id": pic.cloud_id,
                "url": cloudinary_url(pic.cloud_id, secure=True)[0],
            }
            for pic in event.pictures
        ],
        "creator_username": creator.display_name if creator else None,
        "creator_profile_picture_url": cloudinary_url(creator.profile_picture, secure=True)[0] if creator and creator.profile_picture else None,
        "creator_academy": creator.academy if creator else None,
        "creator_faculty": creator.faculty if creator else None,
        "creator_course": creator.course if creator else None,
        "creator_year": creator.year if creator else None,
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "comment_count": int(event.comment_count or 0),
        "participant_count": int(event.participant_count or 0),
        "participation_count": int(event.participant_count or 0),
        "is_participating": event.creator_id == user_id or event.event_id in participating_event_ids,
        "is_joined": event.creator_id == user_id or event.event_id in participating_event_ids,
        "is_private": event.is_private,
        "location_coordinates": parse_location_coordinates(event.location),
    }

'''
Input: JSON { 
    "name": <str>, 
    "description": <str>, 
    "date": "DD.MM.YYYY", 
    "time": "HH:MM", 
    "location": <str> OR [<float:lng>, <float:lat>], 
    "is_private": <bool>, 
    "shared_list": [<uuid>], 
    "pictures": [{"cloud_id": <str>}] }
Action: Creates an event, handles time conversion to UTC, saves location format, and sets privacy visibility.
Data sent to the frontend: {"event_id": <uuid>, "message": "Event created successfully"}
Output: 201 Created (or 400/404/500 on error)
'''
@events_bp.route("/create", methods=["POST"])
@limiter.limit("100 per minute")
@jwt_required()
def create_event():
    user = get_current_user()
    event_data = request.get_json()

    if not event_data:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Invalid JSON")
    
    required_keys = {"name", "description", "date", "time", "location", "is_private"}

    if not required_keys.issubset(event_data.keys()):
        current_app.logger.warning(f"WARNING: /create_event, user {user.user_id} tried to create event with missing fields")
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Missing fields")
    
    name = sanitize_input(str(event_data.get("name", ""))).strip()
    description = sanitize_input(str(event_data.get("description", ""))).strip()
    date_str = str(event_data.get("date", "")).strip()
    time_str = str(event_data.get("time", "")).strip()
    location, location_error = normalize_location_input(event_data.get("location"))
    if location_error:
        current_app.logger.warning(f"WARNING: /create_event, for user {user.user_id} location error: {location_error}")
        return make_api_response(ResponseTypes.INVALID_DATA, message=location_error)
    is_private_raw = event_data.get("is_private", False)
    is_private = str(is_private_raw).strip().lower() in ['true', '1', 't', 'y', 'yes']

    shared_list = []
    if is_private:
        raw_shared_list = event_data.get("shared_list", [])
        if not isinstance(raw_shared_list, list):
            return make_api_response(ResponseTypes.INVALID_DATA, message="shared_list must be an array of user IDs")
        shared_list = raw_shared_list

    if not (Constants.MIN_EVENT_NAME <= len(name) <= Constants.MAX_EVENT_NAME):
        return make_api_response(ResponseTypes.INVALID_DATA, message=f"Event name must be between {Constants.MIN_EVENT_NAME} and {Constants.MAX_EVENT_NAME} characters")
        
    if len(description) > Constants.MAX_DESCRIPTION_LEN:
         return make_api_response(ResponseTypes.INVALID_DATA, message="Description is too long")

    try:
        dt_string = f"{date_str} {time_str}"
        local_dt = datetime.strptime(dt_string, "%d.%m.%Y %H:%M")
        local_dt = local_dt.replace(tzinfo=local_tz)

        date_and_time = local_dt.astimezone(timezone.utc)
        
        if date_and_time <= datetime.now(timezone.utc):
            current_app.logger.warning(f"WARNING: /create_event, user {user.user_id} tried to create event with date in past")
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Event date must be in the future")
             
    except ValueError:
        current_app.logger.error(f"ERROR: /create_event, user {user.user_id} tried to create event with invalid date format")
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid date format. Use DD.MM.YYYY and HH:MM")

    # IMPORTANT: Before calling create/event endpoint frontend needs to call /upload and upload pictures to the cloud one by one
    # or use /upload-batch to upload multiple pictures
    # then frontend needs to send a list with picture data to /create or /edit

    pictures_data = event_data.get("pictures", [])
    if not isinstance(pictures_data, list):
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Pictures must be a list")
    
    if len(pictures_data) > Constants.MAX_PICTURES_COUNT:
        return make_api_response(ResponseTypes.BAD_REQUEST, message=f"Maximum of {Constants.MAX_PICTURES_COUNT} pictures allowed per event")

    try:
        new_event = Event(
            event_name=name,
            description=description,
            date_and_time=date_and_time,
            location=location,
            creator_id=user.user_id,
            is_private=is_private
        )
        db.session.add(new_event)
        db.session.flush()

        for pic in pictures_data:
            pub_id = pic.get("cloud_id")
            
            if pub_id:
                new_picture = Pictures(
                    event_id=new_event.event_id,
                    cloud_id=pub_id
                )
                db.session.add(new_picture)

        db.session.commit()

        creator_participant = Event_participants(event_id=new_event.event_id, user_id=user.user_id)
        db.session.add(creator_participant)
        new_event.participant_count = 1

        valid_shared_ids = []

        if is_private and shared_list:
            for shared_with_id in shared_list:
                u_uuid = validate_uuid(shared_with_id)
                if u_uuid is None:
                    db.session.rollback()
                    return make_api_response(ResponseTypes.INVALID_DATA, message=f"Invalid shared_with id {shared_with_id}")
                if u_uuid == user.user_id:
                    continue

                shared_with = User.query.filter_by(user_id=u_uuid).first()
                if shared_with is None:
                    db.session.rollback()
                    return make_api_response(ResponseTypes.NOT_FOUND, message=f"User ID {shared_with_id} does not exist")
                new_event_visibility = Event_visibility(
                    event_id=new_event.event_id,
                    sharing=user.user_id,
                    shared_with=u_uuid
                )
                db.session.add(new_event_visibility)
                
                valid_shared_ids.append(u_uuid)

        db.session.commit() 
        creator_lookup = {str(user.user_id): user}
        ser_event_data = serialize_event_payload(new_event, user.user_id, creator_lookup, set())
        cache_event_data(str(new_event.event_id), ser_event_data)
        

        if new_event.is_private:
            if valid_shared_ids:
                friend_new_private_event.send(
                    current_app._get_current_object(),
                    creator_id=user.user_id,
                    creator_name=user.username,
                    event_id=new_event.event_id,
                    event_name=new_event.event_name,
                    shared_with_ids=valid_shared_ids
                )
        else:
            friendships = Friendship.query.filter(
                or_(Friendship.user_id == user.user_id, Friendship.friend_id == user.user_id)
            ).all()
            
            friend_ids = [f.friend_id if f.user_id == user.user_id else f.user_id for f in friendships]
            
            if friend_ids:
                friend_new_public_event.send(
                    current_app._get_current_object(),
                    creator_id=user.user_id,
                    creator_name=user.username,
                    event_id=new_event.event_id,
                    event_name=new_event.event_name,
                    friend_ids=friend_ids
                )

        current_app.logger.info(f"INFO: /create_event, user {user.user_id} created event {new_event.event_id}")

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /create_event, DB exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    return make_api_response(ResponseTypes.CREATED, message="Event created successfully", data={"event_id": str(new_event.event_id)})

'''
Input: URL Parameter <uuid:event_id>, Header { "Authorization": "Bearer <Access_Token>" }
Action: Verifies that the requester is the event creator. Deletes all associated images from Cloudinary, removes the event record from the database, and clears the Redis cache
Data sent to the frontend: {"message": "Event deleted successfully"}
Output: 200 OK (or 404/403/400/500 on error)
'''
@events_bp.route("/delete/<event_id>", methods=["DELETE"])
@limiter.limit("100 per minute")
@jwt_required()
def delete_event(event_id):
    user = get_current_user()
    e_uuid = validate_uuid(event_id)

    if not e_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid Event ID")

    event = Event.query.filter_by(event_id=e_uuid).first()

    if event is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Event doesn't exist")

    if user.user_id != event.creator_id:
        current_app.logger.warning(f"WARNING: /delete_event, user {user.user_id} tried to delete event {event_id} without permissions")
        return make_api_response(ResponseTypes.FORBIDDEN, message="You can delete your own events only")
    try:
        #info needed for notifications
        participants = Event_participants.query.filter(
            Event_participants.event_id == event.event_id,
            Event_participants.user_id != user.user_id
        ).all()
        
        participant_ids = [p.user_id for p in participants]
        event_name_cache = event.event_name

        for picture in event.pictures:
            try:
                cloudinary.uploader.destroy(picture.cloud_id)
            except Exception as cloud_err:
                current_app.logger.error(f"ERROR: /delete_event, failed to delete picture {picture.cloud_id} from Cloudinary: {cloud_err}")

        db.session.delete(event)
        db.session.commit()
        invalidate_event_cache(str(e_uuid))

        if participant_ids:
            joined_event_deleted.send(
                current_app._get_current_object(),
                event_name=event_name_cache,
                creator_username=user.username,
                participant_ids=participant_ids
            )

        current_app.logger.info(f"INFO: /delete_event, user {user.user_id} deleted event {event_id}")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /delete_event, DB exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Event deleted successfully")

'''
Input: URL Parameter <uuid:event_id>, Header { "Authorization": "Bearer <Access_Token>" }, 
    JSON { 
        "name": <str>, 
        "description": <str>, 
        "location": <str/list>, 
        "is_private": <bool>, 
        "shared_list": [<uuid>], 
        "date": "DD.MM.YYYY", 
        "time": "HH:MM", 
        "pictures": [{"cloud_id": <str>}] } (all fields optional).
Action: Updates event details. It handles synchronization for private event visibility (adding/removing users), updates dates/times in UTC, and manages Cloudinary image cleanup for removed pictures.
Data sent to the frontend: {"message": "Event edited successfully"}
Output: 200 OK (or 404/403/400/500 on error)
'''
@events_bp.route("/edit/<event_id>", methods=["PUT"])
@limiter.limit("100 per minute")
@jwt_required()
def edit_event(event_id):
    user = get_current_user()

    e_uuid = validate_uuid(event_id)
    if not e_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid event UD format")

    event = db.session.get(Event, e_uuid)
    if event is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="This event does not exist")

    if user.user_id != event.creator_id:
        current_app.logger.warning(f"WARNING: /edit_event, user {user.user_id} attempted to edit event {event_id} without permissions")
        return make_api_response(ResponseTypes.FORBIDDEN, message="You can edit your own events only")
    
    event_data = request.get_json(silent=True)
    if not event_data:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Invalid JSON or missing data")

    raw_name = event_data.get("name")
    if raw_name is not None:
        name = sanitize_input(str(raw_name)).strip()
        # Validate only when title is actually changed to keep legacy events editable.
        if name != event.event_name:
            if not (Constants.MIN_EVENT_NAME <= len(name) <= Constants.MAX_EVENT_NAME):
                return make_api_response(ResponseTypes.INVALID_DATA, message=f"Event name must be between {Constants.MIN_EVENT_NAME} and {Constants.MAX_EVENT_NAME} characters")
            event.event_name = name

    raw_desc = event_data.get("description")
    if raw_desc is not None:
        description = sanitize_input(str(raw_desc)).strip()
        if len(description) > Constants.MAX_DESCRIPTION_LEN:
            return make_api_response(ResponseTypes.INVALID_DATA, message="Description is too long")
        event.description = description

    raw_loc = event_data.get("location")
    if raw_loc is not None:
        location, location_error = normalize_location_input(raw_loc)
        if location_error:
            return make_api_response(ResponseTypes.INVALID_DATA, message=location_error)
        event.location = location

    raw_is_private = event_data.get("is_private")
    if raw_is_private is not None:
        new_is_private = str(raw_is_private).strip().lower() in ['true', '1', 't', 'y', 'yes']
        if event.is_private and not new_is_private: 
            Event_visibility.query.filter_by(event_id=event.event_id).delete()
        event.is_private = new_is_private
    
    if event.is_private and "shared_list" in event_data:
        raw_shared_list = event_data["shared_list"]
        if not isinstance(raw_shared_list, list):
            return make_api_response(ResponseTypes.BAD_REQUEST, message="shared_list must be an array")
        incoming_user_uuids = set()
        for uid in raw_shared_list:
            u_uuid = validate_uuid(uid)
            if u_uuid and u_uuid != user.user_id:
                incoming_user_uuids.add(u_uuid)

        current_visibility = Event_visibility.query.filter_by(event_id=event.event_id).all()
        current_user_ids = {v.shared_with for v in current_visibility}
        
        #synchronization
        to_remove = current_user_ids - incoming_user_uuids
        to_add = incoming_user_uuids - current_user_ids

        if to_remove:
            Event_visibility.query.filter(
                Event_visibility.event_id == event.event_id,
                Event_visibility.shared_with.in_(list(to_remove))
            ).delete(synchronize_session=False)

        for new_uid in to_add:
            if db.session.get(User, new_uid):
                new_vis = Event_visibility(event_id=event.event_id, sharing=user.user_id, shared_with=new_uid)
                db.session.add(new_vis)

    date_str = event_data.get("date")
    time_str = event_data.get("time")
    
    if date_str is not None or time_str is not None:
        if not date_str or not time_str:
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Both date and time are required")
        try:
            clean_date = sanitize_input(str(date_str)).strip()
            clean_time = sanitize_input(str(time_str)).strip()

            dt_string = f"{clean_date} {clean_time}"
            local_dt = datetime.strptime(dt_string, "%d.%m.%Y %H:%M")
            local_dt = local_dt.replace(tzinfo=local_tz)

            date_and_time = local_dt.astimezone(timezone.utc)

            if date_and_time <= datetime.now(timezone.utc):
                return make_api_response(ResponseTypes.BAD_REQUEST, message="Event date must be in the future")
            event.date_and_time = date_and_time
        except ValueError:
            current_app.logger.error(f"ERROR: /edit_event, user {user.user_id} tried to create event with invalid date format")
            return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid date format. Use DD.MM.YYYY and HH:MM")

    raw_pictures = event_data.get("pictures", [])
    if raw_pictures is not None:
        if not isinstance(raw_pictures, list):
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Pictures must be a list")
        
        existing_pictures_map = {pic.cloud_id: pic for pic in event.pictures}
        existing_ids = set(existing_pictures_map.keys())
        
        incoming_ids = {pic["cloud_id"] for pic in raw_pictures if pic.get("cloud_id")}

        staying_ids = existing_ids.intersection(incoming_ids)

        ids_to_delete = existing_ids - incoming_ids
        ids_to_add = incoming_ids - existing_ids

        count_staying = len(staying_ids)
        count_to_add = len(ids_to_add)
        total_after_edit = count_staying + count_to_add
        if total_after_edit > Constants.MAX_PICTURES_COUNT:
            return make_api_response(ResponseTypes.BAD_REQUEST, message=f"Limit of pictures exceeded, you can only add {Constants.MAX_PICTURES_COUNT} pictures at best")

        for pic_id in ids_to_delete:
            pic_to_remove = existing_pictures_map[pic_id]
            try:
                cloudinary.uploader.destroy(pic_id)
            except Exception as cloud_err:
                current_app.logger.error(f"ERROR: /edit_event, Cloudinary delete error: {cloud_err}")

            event.pictures.remove(pic_to_remove)

        for new_id in ids_to_add:
            new_picture = Pictures(cloud_id=new_id, event_id=event.event_id)
            event.pictures.append(new_picture)

    try:
        event.is_edited = True
        db.session.commit()
        invalidate_event_cache(str(event.event_id))

        #get all participants except the creator who is editing the event
        participants = Event_participants.query.filter(
            Event_participants.event_id == event.event_id,
            Event_participants.user_id != user.user_id
        ).all()
        
        participant_ids = [p.user_id for p in participants]

        if participant_ids:
            joined_event_updated.send(
                current_app._get_current_object(),
                event_id=event.event_id,
                event_name=event.event_name,
                participant_ids=participant_ids
            )

        current_app.logger.info(f"INFO: /edit_event, user {user.user_id} successfully edited event {event_id}")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /edit_event, DB exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Event edited successfully")

@events_bp.route("get/<event_id>", methods=["GET"])
@limiter.limit("600 per minute")
@jwt_required()
def get_event(event_id):
    try:
        user = get_current_user()
        e_uuid = validate_uuid(event_id)

        if not e_uuid:
            return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid Event ID")

        event = db.session.get(Event, e_uuid)

        if event is None:
            return make_api_response(ResponseTypes.NOT_FOUND, message="This event does not exist")

        if event.is_private and event.creator_id != user.user_id:
            has_access = db.session.query(Event_visibility).filter_by(event_id=e_uuid, shared_with=user.user_id).first()
            if not has_access:
                current_app.logger.warning(f"WARNING: /get_event, user {user.user_id} tried to access private event {event_id} without permission")
                return make_api_response(ResponseTypes.FORBIDDEN, message="This event is private")

        creator = db.session.get(User, event.creator_id)
        creator_lookup = {str(event.creator_id): creator} if creator else {}

        event_data = serialize_event_payload(event, None, creator_lookup, set())

        is_joined = (event.creator_id == user.user_id)
        if not is_joined:
            participant = db.session.query(Event_participants).filter_by(event_id=e_uuid, user_id=user.user_id).first()
            if participant is not None:
                is_joined = True

        event_data["is_participating"] = is_joined
        event_data["is_joined"] = is_joined

        current_app.logger.info(f"INFO: /get_event, user {user.user_id} successfully fetched event {event_id}")
        return make_api_response(ResponseTypes.SUCCESS, data=event_data)

    except Exception as e:
        current_app.logger.error(f"ERROR: /get_event, exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

'''
/api/events/feed?page=1&limit=20&visibility=all&participation=all&created_window=all&sort_mode=default
Input: Query Params { page=<int> & limit=<int> & q=<str> & visibility=all / public / private & participation=all/ joined / not_joined & sort_mode=default / members_desc / ... }
Action: Returns a paginated list of events the user is permitted to see. Uses Redis for caching
Data sent to the frontend: {
    "data": [<Event_Objects>], 
    "pagination": {
        "page": <int>, 
        "pages": <int>, 
        "total": <int>, 
        "has_next": <bool>}}
Output: 200 OK (or 500 on error)
'''
@events_bp.route("/feed", methods=["GET"])
@limiter.limit("600 per minute")
@jwt_required()
def feed():
    try:
        user = get_current_user()
        user_id = user.user_id
        engine_ro = db.engines['readonly']

        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=Constants.PAGINATION_DEFAULT_LIMIT, type=int)
        
        q = request.args.get("q", default="", type=str).strip()
        q = sanitize_input(q) if q else ""

        visibility = request.args.get("visibility", default="all", type=str).lower()
        participation = request.args.get("participation", default="all", type=str).lower()
        created_window = request.args.get("created_window", default="all", type=str).lower()
        sort_mode = request.args.get("sort_mode", default="default", type=str).lower()

        if page < 1:
            page = 1
        if limit < 1:
            limit = Constants.PAGINATION_DEFAULT_LIMIT
        if limit > Constants.MAX_PAGINATION_LIMIT:
            limit = Constants.MAX_PAGINATION_LIMIT

        visibility_subquery = db.select(Event_visibility.event_id).filter(
            Event_visibility.event_id == Event.event_id,
            Event_visibility.shared_with == user_id
        )

        participation_subquery = db.select(Event_participants.event_id).filter(
            Event_participants.event_id == Event.event_id,
            Event_participants.user_id == user_id,
        )

        query = db.select(Event).filter(
            or_(
                Event.is_private == False,
                Event.creator_id == user_id,
                visibility_subquery.exists(),
                participation_subquery.exists(),
            )
        ).distinct()

        if q:
            search_filter = f"%{q}%"
            query = query.filter(or_(
                Event.event_name.ilike(search_filter),
                Event.description.ilike(search_filter)
            ))

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

        now = datetime.now(timezone.utc)
        if created_window != "all":
            if created_window == "today":
                start_date = now - timedelta(days=1)
            elif created_window == "week":
                start_date = now - timedelta(weeks=1)
            elif created_window == "month":
                start_date = now - timedelta(days=30)
            elif created_window == "year":
                start_date = now - timedelta(days=365)
            if created_window == "older":
                query = query.filter(Event.created_at < (now - timedelta(days=365)))
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
        
        query = query.execution_options(bind_key="readonly")
        pagination = db.paginate(
            query, 
            page=page, 
            per_page=limit, 
            error_out=False,
        )

        creator_ids = {e.creator_id for e in pagination.items if e.creator_id}
        user_query = db.select(User).filter(User.user_id.in_(creator_ids))
        creator_users = db.session.execute(user_query, bind_arguments={'bind_key': 'readonly'}).scalars().all() if creator_ids else []
        creator_lookup = {str(u.user_id): u for u in creator_users}

        event_ids = [event.event_id for event in pagination.items]
        if event_ids:

            query_participants = db.select(Event_participants.event_id).filter(
                Event_participants.user_id == user_id,
                Event_participants.event_id.in_(event_ids)
            )
            
            participant_rows = db.session.execute(
                query_participants, 
                bind_arguments={'bind_key': 'readonly'}
            ).all()
        else:
            participant_rows = []

        participating_event_ids = {event_id for (event_id,) in participant_rows}

        event_list = [
            serialize_event_payload(event, user_id, creator_lookup, participating_event_ids)
            for event in pagination.items
        ]

        return make_api_response(ResponseTypes.SUCCESS, data={
            "data": event_list,
            "pagination": {
                "page": pagination.page,
                "limit": limit,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next
            }
        })
    except Exception as e:
        current_app.logger.error(f"ERROR: /feed, exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

'''
Input: URL Parameter <uuid:event_id>, Header { "Authorization": "Bearer <Access_Token>" }
Action: Checks the database to see if the current user is a participant or the creator. Retrieves the total participant count
Data sent to the frontend: {"is_participating": <bool>, "participant_count": <int>}
Output: 200 OK (or 404/400/500 on error)
'''
@events_bp.route("/participation/<event_id>", methods=["GET"])
@limiter.limit("600 per minute")
@jwt_required()
def participation_status(event_id):
    user = get_current_user()
    e_uuid = validate_uuid(event_id)

    engine_ro = db.engines['readonly']

    if not e_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid Event ID")

    event_query = db.select(Event).filter_by(event_id=e_uuid)
    event = db.session.execute(event_query, bind_arguments={'bind_key': 'readonly'}).scalar_one_or_none()
    if event is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="This event does not exist")
    
    if event.creator_id == user.user_id:
        is_participating = True
    else:
        is_participating_query = db.select(Event_participants).filter_by(event_id=e_uuid, user_id=user.user_id)
        is_participating = db.session.execute(is_participating_query, bind_arguments={'bind_key': 'readonly'}).scalar_one_or_none() is not None

    current_app.logger.info(f"INFO: /participation_status, user {user.user_id} checked participation status for event {event_id}")
    return make_api_response(ResponseTypes.SUCCESS, data={
        "is_participating": is_participating,
        "participant_count": int(event.participant_count or 0),
    })

'''
Input: URL Parameter <uuid:event_id>
Action: Adds user as a participant to the event, increments participant_count, and invalidates cache
Data sent to the frontend: {"message": "Joined event successfully", "participant_count": <int>}
Output: 200 OK (or 400/403/404/409/500 on error)
'''
@events_bp.route("/join/<event_id>", methods=["POST"])
@limiter.limit("100 per minute")
@jwt_required()
def join_event(event_id):
    user = get_current_user()
    e_uuid = validate_uuid(event_id)
    engine_ro = db.engines['readonly']

    if not e_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid Event ID")

    event = db.session.get(Event, e_uuid)
    if event is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="This event does not exist")

    if event.creator_id == user.user_id:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Creator is already participating")

    if event.is_private:
        has_access = db.session.query(Event_visibility).filter_by(event_id=e_uuid, shared_with=user.user_id).first()
        if not has_access:
            current_app.logger.warning(f"WARNING: /join, user {user.user_id} tried to join private event {event_id} without access")
            return make_api_response(ResponseTypes.FORBIDDEN, message="This event is private")

    existing_query = db.select(Event_participants).filter_by(event_id=e_uuid, user_id=user.user_id)
    existing = db.session.execute(existing_query, bind_arguments={'bind_key': 'readonly'}).scalar_one_or_none()
    
    if existing:
        return make_api_response(ResponseTypes.CONFLICT, message="You are already participating in this event")

    try:
        participant = Event_participants(event_id=e_uuid, user_id=user.user_id)
        db.session.add(participant)
        event.participant_count = Event.participant_count + 1
        db.session.commit()
        invalidate_event_cache(str(e_uuid))
        db.session.refresh(event)
        current_app.logger.info(f"INFO: /join, user {user.user_id} successfully joined event {event_id}")

        event_new_participant.send(
            current_app._get_current_object(),
            participant_id=user.user_id,
            participant_username=user.username,
            creator_id=event.creator_id,
            event_id=event.event_id,
            event_name=event.event_name
        )

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /join, DB exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Joined event successfully", data={
        "participant_count": int(event.participant_count or 0),
    })

'''
Input: URL Parameter <uuid:event_id>, Header { "Authorization": "Bearer <Access_Token>" }
Action: Removes the user from the Event_participants table and decrements the event's participant_count. Creators are blocked from leaving their own events
Data sent to the frontend: {"message": "Left event successfully", "participant_count": <int>}
Output: 200 OK (or 404/400/500 on error)
'''
@events_bp.route("/leave/<event_id>", methods=["DELETE"])
@limiter.limit("100 per minute")
@jwt_required()
def leave_event(event_id):
    user = get_current_user()
    e_uuid = validate_uuid(event_id)

    if not e_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid Event ID")

    event = db.session.get(Event, e_uuid)
    if event is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="This event does not exist")

    if event.creator_id == user.user_id:
        current_app.logger.warning(f"WARNING: /leave_event, user {user.user_id} tried to leave their own event")
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Creator cannot leave their own event")

    participant = db.session.query(Event_participants).filter_by(event_id=e_uuid, user_id=user.user_id).first()
    if not participant:
        current_app.logger.warning(f"WARNING: /leave_event, user {user.user_id} tried to leave event which he is not participating in")
        return make_api_response(ResponseTypes.NOT_FOUND, message="You are not participating in this event")

    try:
        db.session.delete(participant)
        event.participant_count = Event.participant_count - 1
        db.session.commit()
        invalidate_event_cache(str(e_uuid))
        db.session.refresh(event)
        current_app.logger.info(f"INFO: /leave_event, user {user.user_id} successfully left event {event_id}")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /leave_event, DB exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Left event successfully", data={
        "participant_count": int(event.participant_count or 0),
    })

'''
Input: URL Parameter <uuid:event_id>, Header { "Authorization": "Bearer <Access_Token>" }, JSON { "invited": <uuid> }
Action: Verifies the inviter and invited are friends. Checks privacy rules (only creators can invite for private events). Creates an invite record and triggers an async notification
Data sent to the frontend: {"message": "Invite created successfully"}
Output: 201 Created (or 404/400/403/409/500 on error)
'''
@events_bp.route("/invite/<event_id>", methods=["POST"])
@limiter.limit("100 per minute")
@jwt_required()
def invite_to_event(event_id):
    user = get_current_user()
    e_uuid = validate_uuid(event_id)
    u_uuid = validate_uuid(user.user_id)

    invite_data = request.get_json(silent=True)

    if not invite_data or "invited" not in invite_data:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Invited ID missing")

    i_uuid = validate_uuid(invite_data.get("invited"))

    if not e_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid Event ID")
    if not u_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid Inviter ID")
    if not i_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid Invited ID")
    
    if u_uuid == i_uuid:
        current_app.logger.warning(f"WARNING: /invite_to_event, user {user.user_id} tried to invite himself for an event")
        return make_api_response(ResponseTypes.BAD_REQUEST, message="You cannot invite yourself")
    
    event = db.session.get(Event, e_uuid)
    if event is None:
        current_app.logger.warning(f"WARNING: /invite_to_event, user {user.user_id} tried to send invite to a non existant event")
        return make_api_response(ResponseTypes.NOT_FOUND, message="This event does not exist")

    query_friend = db.select(Friendship).filter(
    or_(
        and_(Friendship.user_id == u_uuid, Friendship.friend_id == i_uuid),
        and_(Friendship.user_id == i_uuid, Friendship.friend_id == u_uuid)
        )
    )

    is_friend = db.session.execute(
        query_friend, 
        bind_arguments={'bind_key': 'readonly'}
    ).scalars().first()

    if not is_friend: 
        current_app.logger.warning(f"WARNING: /invite_to_event, user {user.user_id} tried to invite a user that is not their friend")
        return make_api_response(ResponseTypes.FORBIDDEN, message="You can only invite your friends")
    
    if event.is_private:
        # na razie tylko autor ma możliwość zapraszania na swój event osoby, którym udostępnił do wyświetlania
        if event.creator_id != u_uuid:
            current_app.logger.warning(f"WARNING: /invite_to_event, user {user.user_id} tried to send invite for an event that is not his")
            return make_api_response(ResponseTypes.FORBIDDEN, message="Only creator of the private event can invite")
        
        has_visibility_query = db.select(Event_visibility).filter_by(event_id=e_uuid, shared_with=i_uuid)
        has_visibility = db.session.execute(has_visibility_query, bind_arguments={'bind_key': 'readonly'}).scalar_one_or_none()

        if not has_visibility:
            current_app.logger.warning(f"WARNING: /invite_to_event, user {user.user_id} tried to send invite to user that does not have priviledges to view this event")
            return make_api_response(ResponseTypes.FORBIDDEN, message=f"User does not have priviledges to view this event")

    is_already_participant_query = db.select(Event_participants).filter_by(event_id=e_uuid, user_id=i_uuid)
    is_already_participant = db.session.execute(is_already_participant_query, bind_arguments={'bind_key': 'readonly'}).scalar_one_or_none()
    if is_already_participant:
        return make_api_response(ResponseTypes.CONFLICT, message="User is already participating in this event")
    existing_invite_query = db.select(Invites).filter_by(event_id=e_uuid, inviter_id=u_uuid, invited_id=i_uuid)
    existing_invite = db.session.execute(existing_invite_query, bind_arguments={'bind_key': 'readonly'}).scalar_one_or_none()
    if existing_invite:
        current_app.logger.warning(f"WARNING: /invite_to_event, user {user.user_id} tried to send invite that already exists")
        return make_api_response(ResponseTypes.CONFLICT, message="Invite already sent")
        
    try:
        new_invite = Invites(
            event_id=e_uuid,
            inviter_id=u_uuid,
            invited_id=i_uuid,
            status=InviteRequestStatus.pending
        )
        db.session.add(new_invite)
        db.session.commit()
        
        invite_created.send(
            current_app._get_current_object(),
            from_user_id=u_uuid,
            from_user_username=user.username,
            to_user_id=i_uuid,
            invite_id=new_invite.invite_id,
            event_id=e_uuid,
            event_name=event.event_name
        )
        current_app.logger.info(f"INFO: /invite, user {u_uuid} invited user {i_uuid} to event {e_uuid}")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /invite, DB exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    
    return make_api_response(ResponseTypes.CREATED, message="Invite created successfully")

'''
Input: URL Parameter <uuid:event_id>, Header { "Authorization": "Bearer <Access_Token>" }
Action: Retrieves all user IDs currently invited to the event. Endpoint restricted to the event creator only
Data sent to the frontend: {"invited_ids": [<str:uuid>]}
Output: 200 OK (or 404/403/400/500 on error)
'''
@events_bp.route("/invites/<event_id>", methods=["GET"])
@limiter.limit("100 per minute")
@jwt_required()
def get_sent_invites(event_id):
    user = get_current_user()
    u_uuid = validate_uuid(user.user_id)
    e_uuid = validate_uuid(event_id)

    if not u_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid user ID")
    if not e_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid event ID")

    event_query = db.select(Event).filter_by(event_id=e_uuid)
    event = db.session.execute(event_query, bind_arguments={'bind_key': 'readonly'}).scalar_one_or_none()
    
    if event is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="This event does not exist")

    # Only the event creator can view sent invites
    if event.creator_id != u_uuid:
        return make_api_response(ResponseTypes.FORBIDDEN, message="Only the event creator can view sent invites")

    try:
        invites_query = db.select(Invites).filter_by(event_id=e_uuid)
        invites = db.session.execute(invites_query, bind_arguments={'bind_key': 'readonly'}).scalars().all()
        invited_ids = [str(invite.invited_id) for invite in invites]
        current_app.logger.info(f"INFO: /invites, user {u_uuid} successfully fetched invites for event {e_uuid}")
        return make_api_response(ResponseTypes.SUCCESS, data={"invited_ids": invited_ids})
    except SQLAlchemyError as e:
        current_app.logger.error(f"ERROR: /invites, DB exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

'''
Input: URL Parameter <uuid:event_id>, Header { "Authorization": "Bearer <Access_Token>" }, JSON { "invited": <uuid> }
Action: Locates a specific invitation from the inviter to the invited user for the given event and deletes it
Data sent to the frontend: {"message": "Invite deleted successfully"}
Output: 200 OK (or 404/400/500 on error)
''' 
@events_bp.route("/delete_invite/<event_id>", methods=["DELETE"])
@limiter.limit("100 per minute")
@jwt_required()
def delete_invite(event_id):
    user = get_current_user()
    u_uuid = validate_uuid(user.user_id)
    e_uuid = validate_uuid(event_id)

    invite_data = request.get_json(silent=True)
    i_uuid = validate_uuid(invite_data.get("invited") if invite_data else None)

    if not u_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid inviter ID")
    if not e_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid event ID")
    if not i_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid invited ID")
    
    invite = db.session.query(Invites).filter_by(event_id=e_uuid, inviter_id=u_uuid, invited_id=i_uuid).first()
    if not invite:
        return make_api_response(ResponseTypes.NOT_FOUND, message=f"invitattion to event: {e_uuid} from: {u_uuid} to: {i_uuid} does not exist")
    
    try:
        db.session.delete(invite)
        db.session.commit()
        current_app.logger.info(f"INFO: /delete_invite, user {u_uuid} successfully deleted invite for user {i_uuid}")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /delete_invite, DB exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    
    return make_api_response(ResponseTypes.SUCCESS, message="Invite deleted successfully")
    
'''
Input: URL Parameter <uuid:invite_id>, Header { "Authorization": "Bearer <Access_Token>" }, JSON { "status": "accepted" / "declined" }
Action: Updates the status of a received invite. If accepted, the user is added to the Event_participants table and the event's count is incremented
Data sent to the frontend: {"message": "Invite status changed successfully"}
Output: 200 OK (or 404/400/403/409/500 on error)
'''
@events_bp.route("/change_invite_status/<invite_id>", methods=["POST"])
@limiter.limit("100 per minute")
@jwt_required()
def change_invite_status(invite_id):
    user = get_current_user()
    u_uuid = validate_uuid(user.user_id)
    i_uuid = validate_uuid(invite_id)

    if not u_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid user ID")
    if not i_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid invite ID")
    
    invite = db.session.get(Invites, i_uuid)
    if invite is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="This invite does not exist")

    if invite.invited_id != u_uuid:
        current_app.logger.warning(f"WARNING: /change_invite_status, user {u_uuid} tried to change status of invite {invite_id} not meant for him")
        return make_api_response(ResponseTypes.FORBIDDEN, message="You can only change status of the invites meant to you")
    
    if invite.status != InviteRequestStatus.pending:
        return make_api_response(ResponseTypes.CONFLICT, message="This invite is already accepted/declined")
    
    invite_data = request.get_json(silent=True)
    new_status = sanitize_input(str(invite_data.get("status"))).lower()

    try:
        if new_status == "accepted":
            invite.status = InviteRequestStatus.accepted
            already_in_query = db.select(Event_participants).filter_by(event_id=invite.event_id, user_id=u_uuid)
            already_in = db.session.execute(already_in_query, bind_arguments={'bind_key': 'readonly'}).scalar_one_or_none()
            if not already_in:
                participant = Event_participants(
                    event_id=invite.event_id,
                    user_id=u_uuid,
                )
                db.session.add(participant)
                event = db.session.get(Event, invite.event_id)
                if event:
                    event.participant_count = Event.participant_count + 1
            
                event_new_participant.send(
                current_app._get_current_object(),
                participant_id=user.user_id,
                participant_username=user.username,
                creator_id=event.creator_id,
                event_id=event.event_id,
                event_name=event.event_name
                )

            invite_status_update.send(
            current_app._get_current_object(),
            invite_id=invite.invite_id,
            inviter_id=invite.inviter_id,
            invitee_id=user.user_id,
            invitee_username=user.username,
            event_id=event.event_id,
            event_name=event.event_name,
            status="accepted"
            )
        elif new_status == "declined":
            invite.status = InviteRequestStatus.declined
            invite_status_update.send(
                current_app._get_current_object(),
                invite_id=invite.invite_id,
                inviter_id=invite.inviter_id,
                invitee_id=user.user_id,
                invitee_username=user.username,
                event_id=event.event_id,
                event_name=event.event_name,
                status="declined"
            )
        else:
            return make_api_response(ResponseTypes.INVALID_DATA, message="Incorrect status")
        db.session.commit()
        current_app.logger.info(f"INFO: /change_invite_status, user {u_uuid} successfully set status to {new_status} for invite {invite_id}")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /change_invite_status, DB exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    
    return make_api_response(ResponseTypes.SUCCESS, message="Invite status changed successfully")

'''
Input: URL Parameter <uuid:user_id>, Header { "Authorization": "Bearer <Access_Token>" }
Action: Fetches all events where the specified user is the creator. Returns a list of serialized event objects
Data sent to the frontend: {"data": [<Serialized_Event_Object>]}
Output: 200 OK (or 400/500 on error)
'''
@events_bp.route("/<user_id>/creator", methods=["GET"])
@jwt_required()
def get_user_events_creator(user_id):
    u_uuid = validate_uuid(user_id)

    if not u_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid user ID")

    user_query = db.select(User).filter_by(user_id=u_uuid)
    user = db.session.execute(user_query, bind_arguments={'bind_key': 'readonly'}).scalar_one_or_none()

    created_events_query = db.select(Event).filter_by(creator_id=user.user_id)
    created_events = db.session.execute(created_events_query, bind_arguments={'bind_key': 'readonly'}).scalars().all()
    
    created_data=[
            {
                "event_id": str(event.event_id),
                "name": event.event_name,
                "description": event.description,
                "date": event.date_and_time.astimezone(local_tz).strftime("%d.%m.%Y"),
                "time": event.date_and_time.astimezone(local_tz).strftime("%H:%M"),
                "location": event.location,
                "creator_id": str(event.creator_id),
                "pictures": [
                    {
                        "cloud_id": pic.cloud_id,
                        "url": cloudinary_url(pic.cloud_id, secure=True)[0]
                    } 
                    for pic in event.pictures
                ],
                "creator_username": user.username,
                "comment_count": str(event.comment_count),
                "participation_count": event.participant_count,
                "is_private": event.is_private,
            }
            for event in created_events
        ]
    
    current_app.logger.info(f"INFO: /user/creator, successfully fetched created events for user {u_uuid}")
    return make_api_response(
        ResponseTypes.SUCCESS, 
        data={"data": created_data}
    )

'''
Input: URL Parameter <uuid:user_id>, Header { "Authorization": "Bearer <Access_Token>" }
Action: Fetches all events where the specified user is listed as a participant
Data sent to the frontend: {"data": [<Serialized_Event_Object>]}
Output: 200 OK (or 400/500 on error)
'''
@events_bp.route("/<user_id>/participant", methods=["GET"])
@jwt_required()
def get_user_events_participand(user_id):
    u_uuid = validate_uuid(user_id)

    if not u_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid user ID")

    user_query = db.select(User).filter_by(user_id=u_uuid)
    user = db.session.execute(user_query, bind_arguments={'bind_key': 'readonly'}).scalar_one_or_none()
    
    participating_events_query = db.select(Event).join(
        Event_participants, Event.event_id == Event_participants.event_id
    ).filter(
        Event_participants.user_id == user.user_id
    ).execution_options(bind_key="readonly")

    participating_events = db.session.execute(participating_events_query).scalars().all()

    participating_data=[
            {
                "event_id": str(event.event_id),
                "name": event.event_name,
                "description": event.description,
                "date": event.date_and_time.astimezone(local_tz).strftime("%d.%m.%Y"),
                "time": event.date_and_time.astimezone(local_tz).strftime("%H:%M"),
                "location": event.location,
                "creator_id": str(event.creator_id),
                "pictures": [
                    {
                        "cloud_id": pic.cloud_id,
                        "url": cloudinary_url(pic.cloud_id, secure=True)[0]
                    } 
                    for pic in event.pictures
                ],
                "creator_username": User.query.filter_by(user_id=event.creator_id).first().username,
                "comment_count": str(event.comment_count),
                "participation_count": event.participant_count,
                "is_private": event.is_private,
            }
            for event in participating_events
        ]
    
    current_app.logger.info(f"INFO: /user/participant, successfully fetched participating events for user {u_uuid}")
    return make_api_response(
        ResponseTypes.SUCCESS, 
        data={"data": participating_data}
    )

'''
Input: Query Parameter { "location": <str> }, Header { "Authorization": "Bearer <Access_Token>" }
Action: Searches the Event_location table for a predefined location name and returns its stored coordinates
Data sent to the frontend: {"coordinates": <str>}
Output: 200 OK (or 404/400/500 on error)
'''
@events_bp.route("/get_coordinates", methods=["GET"])
@limiter.limit("1000 per second")
@jwt_required()
def get_coordinates():
    location_name = request.args.get('location') # request for that endpoint ex: /api/events/get_coordinates?location=Krakow
    location_name = str(sanitize_input(location_name))
    if not location_name or location_name == "":
        return make_api_response(ResponseTypes.INVALID_DATA, message="Location name must not be empty")

    if len(location_name) > Constants.MAX_LOCATION_LEN:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Location name too long")

    location_query = db.select(Location).filter_by(location_name=location_name)
    query = db.session.execute(location_query, bind_arguments={'bind_key': 'readonly'}).scalar_one_or_none()  
    
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
@events_bp.route("/map", methods=["GET"])
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


        events_query = db.select(Event).options(
            joinedload(Event.pictures)
        ).filter(
            Event.date_and_time >= now_utc,
            or_(
                Event.is_private == False,
                Event.creator_id == user_id,
                visibility_exists,
            )
        ).order_by(
            Event.date_and_time.asc(), 
            Event.event_id.asc()
        ).execution_options(bind_key="readonly") 
        events = db.session.execute(events_query).scalars().unique().all()

        events = [event for event in events if parse_location_coordinates(event.location) is not None]

        creator_ids = {event.creator_id for event in events if event.creator_id is not None}

        creator_users_query = db.select(User).filter(User.user_id.in_(creator_ids))
        creator_users = db.session.execute(creator_users_query, bind_arguments={'bind_key': 'readonly'}).scalars().all() if creator_ids else []

        creator_lookup = {str(user.user_id): user for user in creator_users}

        event_ids = [event.event_id for event in events]

        if event_ids:
            participant_rows_query = db.select(Event_participants.event_id).filter(
                Event_participants.user_id == user_id,
                Event_participants.event_id.in_(event_ids)
            ).execution_options(bind_key="readonly")
            participant_rows = db.session.execute(participant_rows_query).all()
        else:
            participant_rows = []
            
        participating_event_ids = {event_id for (event_id,) in participant_rows}

        return make_api_response(
            ResponseTypes.SUCCESS,
            data={
                "data": [
                    serialize_event_payload(event, user_id, creator_lookup, participating_event_ids)
                    for event in events
                ]
            },
        )
    except Exception as e:
        current_app.logger.error(f"Error in map_events: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
