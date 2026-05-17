from flask import Blueprint, request, current_app
from backend.models.event import Event, Event_visibility, Event_participants, Pictures
from backend.models import User, Friendship
from backend.extensions import db, limiter
from backend.constants import Constants
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required, get_current_user
from backend.helpers import validate_uuid, sanitize_input, invalidate_event_cache, cache_event_data
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.exc import SQLAlchemyError
import cloudinary.uploader
from sqlalchemy import or_
from backend.notifications.signals import (
    joined_event_updated,
    joined_event_deleted,
    friend_new_private_event,
    friend_new_public_event
)
from .event_helpers import serialize_event_payload, normalize_location_input

events_bp = Blueprint("events", __name__, url_prefix="/api/events")
local_tz = ZoneInfo("Europe/Warsaw")

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
        current_app.logger.error(f"ERROR: /create_event, DB exception occured:")
        current_app.logger.exception(e, stack_info=True)
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
                current_app.logger.error(f"ERROR: /delete_event, failed to delete picture {picture.cloud_id} from Cloudinary:")
                current_app.logger.exception(cloud_err, stack_info=True)

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
        current_app.logger.error(f"ERROR: /delete_event, DB exception occured:")
        current_app.logger.exception(e, stack_info=True)
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
                current_app.logger.error(f"ERROR: /edit_event, Cloudinary delete error:")
                current_app.logger.exception(cloud_err, stack_info=True)

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
        current_app.logger.error(f"ERROR: /edit_event, DB exception occured:")
        current_app.logger.exception(e, stack_info=True)
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Event edited successfully")
