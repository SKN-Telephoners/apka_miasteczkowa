from flask import jsonify, Blueprint, request, current_app
from backend.models.event import Event, Event_visibility, Event_participants
from backend.models import User
from backend.extensions import db, limiter
from backend.constants import Constants
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required, get_current_user
from backend.helpers import validate_uuid, sanitize_input
import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_

events_bp = Blueprint("events", __name__, url_prefix="/api/events")
local_tz = ZoneInfo("Europe/Warsaw")

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
        current_app.logger.error("dupa")
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Missing fields")
    
    name = sanitize_input(str(event_data.get("name", ""))).strip()
    description = sanitize_input(str(event_data.get("description", ""))).strip()
    date_str = str(event_data.get("date", "")).strip()
    time_str = str(event_data.get("time", "")).strip()
    location = sanitize_input(str(event_data.get("location", ""))).strip()
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
        
    if len(location) > Constants.MAX_LOCATION_LEN:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Location name is too long")
        
    if len(description) > Constants.MAX_DESCRIPTION_LEN:
         return make_api_response(ResponseTypes.INVALID_DATA, message="Description is too long")

    try:
        dt_string = f"{date_str} {time_str}"
        local_dt = datetime.strptime(dt_string, "%d.%m.%Y %H:%M")
        local_dt = local_dt.replace(tzinfo=local_tz)

        date_and_time = local_dt.astimezone(timezone.utc)
        
        if date_and_time <= datetime.now(timezone.utc):
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Event date must be in the future")
             
    except ValueError:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid date format. Use DD.MM.YYYY and HH:MM")

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
        db.session.commit()        
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.CREATED, message="Event created successfully", data={"event_id": str(new_event.event_id)})

@events_bp.route("/delete/<event_id>", methods=["DELETE"])
@limiter.limit("100 per minute")
@jwt_required()
def delete_event(event_id):
    user = get_current_user()
    e_uuid = validate_uuid(event_id)

    if not e_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid Event ID")

    event = Event.query.filter_by(event_id=event_id).first()

    if event is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Event doesn't exist")

    if user.user_id != event.creator_id:
        current_app.logger.warning(f"Użytkownik {user.user_id} próbował usunąć event {event_id} bez uprawnień do niego")
        return make_api_response(ResponseTypes.FORBIDDEN, message="You can delete your own events only")
    try:
        db.session.delete(event)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Event deleted successfully")

@events_bp.route("/edit/<event_id>", methods=["PUT"])
@limiter.limit("100 per minute")
@jwt_required()
def edit_event(event_id):
    user = get_current_user()

    e_uuid = validate_uuid(event_id)
    if not e_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid event UD format")

    event = db.session.get(Event, e_uuid)

    if not event:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Event doesn't exist")

    if user.user_id != event.creator_id:
        current_app.logger.warning(f"SECURITY: User {user.user_id} attempted to edit event {event_id} without permissions.")
        return make_api_response(ResponseTypes.FORBIDDEN, message="You can edit your own events only")
    
    event_data = request.get_json(silent=True)
    if not event_data:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Invalid JSON or missing data")

    raw_name = event_data.get("name")
    if raw_name is not None:
        name = sanitize_input(str(raw_name)).strip()
        if not (Constants.MIN_EVENT_NAME <= len(name) <= Constants.MAX_EVENT_NAME):
            return make_api_response(ResponseTypes.INVALID_DATA, message=f"Event must be between {Constants.MIN_EVENT_NAME} and {Constants.MAX_EVENT_NAME} characters")
        event.event_name = name

    raw_desc = event_data.get("description")
    if raw_desc is not None:
        description = sanitize_input(str(raw_desc)).strip()
        if len(description) > Constants.MAX_DESCRIPTION_LEN:
            return make_api_response(ResponseTypes.INVALID_DATA, message="Description is too long")
        event.description = description

    raw_loc = event_data.get("location")
    if raw_loc is not None:
        location = sanitize_input(str(raw_loc)).strip()
        if len(location) > Constants.MAX_LOCATION_LEN:
            return make_api_response(ResponseTypes.INVALID_DATA, message="Location name is too long")
        event.location = location

    raw_is_private = event_data.get("is_private")
    if raw_is_private is not None:
        event.is_private = str(raw_is_private).strip().lower() in ['true', '1', 't', 'y', 'yes']
    
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
            return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid date format. Use DD.MM.YYYY and HH:MM")
        event.is_edited = True

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in edit_event: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Event edited successfully")

@events_bp.route("/feed", methods=["GET"])
@limiter.limit("600 per minute")
@jwt_required()
def feed():
    try:
        user = get_current_user()
        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=Constants.PAGINATION_DEFAULT_LIMIT, type=int)
        sort=request.args.get("sort", default=1, type=int)

        user_id = user.user_id

        #walidacja danych wejściowych
        if page < 1:
            page = 1
        if limit < 1:
            limit = Constants.PAGINATION_DEFAULT_LIMIT
        if limit > Constants.MAX_PAGINATION_LIMIT:
            limit = Constants.MAX_PAGINATION_LIMIT

        events = Event.query.outerjoin(
            Event_visibility, Event.event_id == Event_visibility.event_id
        ).filter(
            or_(
                Event.is_private == False,              
                Event.creator_id == user_id,               
                Event_visibility.shared_with == user_id
            )
        ).distinct() 

        if sort==1:
            events=events.order_by(Event.date_and_time.asc())
        elif sort==2:
            events=events.order_by(Event.date_and_time.desc())
        else:
            events = events.order_by(Event.date_and_time.asc())

        pagination = events.paginate(page=page, per_page=limit, error_out=False)

        creator_ids = {event.creator_id for event in pagination.items if event.creator_id is not None}
        creator_users = User.query.filter(User.user_id.in_(creator_ids)).all() if creator_ids else []
        creator_usernames = {str(user.user_id): user.display_name for user in creator_users}

        event_list=[
            {
                "id": str(event.event_id),
                "name": event.event_name,
                "description": event.description,
                "date": event.date_and_time.astimezone(local_tz).strftime("%d.%m.%Y"),
                "time": event.date_and_time.astimezone(local_tz).strftime("%H:%M"),
                "location": event.location,
                "creator_id": str(event.creator_id),
                "creator_username": creator_usernames.get(str(event.creator_id)),
                "comment_count": str(event.comment_count),
                "is_private": event.is_private,
            }
            for event in pagination.items
        ]

        return make_api_response(ResponseTypes.SUCCESS, data={
            "data": event_list,
            "pagination": {
                "page": pagination.page,
                "limit": limit,
                "total": pagination.total,
                "pages": pagination.pages
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error in feed: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

@events_bp.route("/participation/<event_id>", methods=["GET"])
@limiter.limit("600 per minute")
@jwt_required()
def participation_status(event_id):
    user = get_current_user()
    e_uuid = validate_uuid(event_id)

    if not e_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid Event ID")

    event = db.session.get(Event, e_uuid)
    if not event:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Event doesn't exist")

    is_participating = Event_participants.query.filter_by(event_id=e_uuid, user_id=user.user_id).first() is not None

    return make_api_response(ResponseTypes.SUCCESS, data={
        "is_participating": is_participating,
        "participant_count": int(event.participant_count or 0),
    })

@events_bp.route("/join/<event_id>", methods=["POST"])
@limiter.limit("100 per minute")
@jwt_required()
def join_event(event_id):
    user = get_current_user()
    e_uuid = validate_uuid(event_id)

    if not e_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid Event ID")

    event = db.session.get(Event, e_uuid)
    if not event:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Event doesn't exist")

    if event.creator_id == user.user_id:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Creator is already participating")

    if event.is_private:
        return make_api_response(ResponseTypes.FORBIDDEN, message="You can join public events only")

    existing = Event_participants.query.filter_by(event_id=e_uuid, user_id=user.user_id).first()
    if existing:
        return make_api_response(ResponseTypes.CONFLICT, message="You are already participating in this event")

    try:
        participant = Event_participants(event_id=e_uuid, user_id=user.user_id)
        db.session.add(participant)
        event.participant_count = int(event.participant_count or 0) + 1
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in join_event: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Joined event successfully", data={
        "participant_count": int(event.participant_count or 0),
    })

@events_bp.route("/leave/<event_id>", methods=["DELETE"])
@limiter.limit("100 per minute")
@jwt_required()
def leave_event(event_id):
    user = get_current_user()
    e_uuid = validate_uuid(event_id)

    if not e_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid Event ID")

    event = db.session.get(Event, e_uuid)
    if not event:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Event doesn't exist")

    participant = Event_participants.query.filter_by(event_id=e_uuid, user_id=user.user_id).first()
    if not participant:
        return make_api_response(ResponseTypes.NOT_FOUND, message="You are not participating in this event")

    try:
        db.session.delete(participant)
        event.participant_count = max(int(event.participant_count or 0) - 1, 0)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in leave_event: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Left event successfully", data={
        "participant_count": int(event.participant_count or 0),
    })
