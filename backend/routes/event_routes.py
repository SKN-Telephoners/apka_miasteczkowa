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
    
    required_keys = {"name", "description", "date", "time", "location"}

    if not required_keys.issubset(event_data.keys()):
        current_app.logger.error("dupa")
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Missing fields")
    
    name = sanitize_input(str(event_data.get("name", ""))).strip()
    description = sanitize_input(str(event_data.get("description", ""))).strip()
    date_str = str(event_data.get("date", "")).strip()
    time_str = str(event_data.get("time", "")).strip()
    location = sanitize_input(str(event_data.get("location", ""))).strip()

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
            creator_id=user.user_id
        )
        db.session.add(new_event)
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
        event.edited = True

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in edit_event: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Event edited successfully")

@events_bp.route("/feed", methods=["GET"])
@limiter.limit("600 per minute")
def feed():
    try:
        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=Constants.PAGINATION_DEFAULT_LIMIT, type=int)
        sort=request.args.get("sort", default=1, type=int)

        #walidacja danych wejściowych
        if page < 1:
            page = 1
        if limit < 1:
            limit = Constants.PAGINATION_DEFAULT_LIMIT
        if limit > Constants.MAX_PAGINATION_LIMIT:
            limit = Constants.MAX_PAGINATION_LIMIT

        events = Event.query
        if sort==1:
            events=events.order_by(Event.date_and_time.asc())
        elif sort==2:
            events=events.order_by(Event.date_and_time.desc())
        else:
            events = events.order_by(Event.date_and_time.asc())

        pagination = events.paginate(page=page, per_page=limit, error_out=False)

        event_list=[
            {
                "id": str(event.event_id),
                "name": event.event_name,
                "description": event.description,
                "date": event.date_and_time.astimezone(local_tz).strftime("%d.%m.%Y"),
                "time": event.date_and_time.astimezone(local_tz).strftime("%H:%M"),
                "location": event.location,
                "creator_id": str(event.creator_id)
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
