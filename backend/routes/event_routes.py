from flask import jsonify, Blueprint, request, current_app
from backend.models import Event
from backend.extensions import db, limiter
from backend.constants import Constants
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required, get_current_user
from backend.helpers import validate_uuid, sanitize_input
import uuid
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError

events_bp = Blueprint("events", __name__, url_prefix="/api/events")

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
        date_and_time = datetime.strptime(dt_string, "%d.%m.%Y %H:%M")
        date_and_time = date_and_time.replace(tzinfo=timezone.utc)
        
        if date_and_time <= datetime.now(timezone.utc):
            return make_api_response(ResponseTypes.BAD_REQUEST, message="Event date must be in the future")
             
    except ValueError:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid date format. Use DD.MM.YYYY and HH:MM")

    try:
        new_event = Event(
            name=name,
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

#NEEDS TO BE ADJUSTED
@events_bp.route("/edit/<event_id>", methods=["PUT"])
@limiter.limit("100 per minute")
@jwt_required()
def edit_event(event_id):
    user = get_current_user()

    try:
        event_id = uuid.UUID(event_id)
    except Exception:
        return jsonify({"message": "Invalid event ID format"}), 400

    event = Event.query.filter_by(event_id=event_id).first()

    if event is None:
        return jsonify({"message": "Event doesn't exist"}), 404

    if user.user_id != event.creator_id:
        return jsonify({"message": "You can edit your own events only"}), 403

    event_data = request.get_json()
    if not event_data:
        return jsonify({"message": "Bad request"}), 400

    name = event_data.get("name", "")
    description = event_data.get("description", "")
    date_str = event_data.get("date")
    time_str = event_data.get("time")
    location = event_data.get("location", "")

    if name is not None:
        name = name.strip()
        if not (3 <= len(name) <= 32):
            return jsonify({"message": "Event name must be between 3 and 32 characters"}), 400
        event.name = name

    if description is not None:
        description = description.strip()
        if len(description) > 1000:
            return jsonify({"message": "Description is too long (max 1000 characters)"}), 400
        event.description = description

    if location is not None:
        location = location.strip()
        if len(location) > 32:
            return jsonify({"message": "Location name is too long (max 32 characters)"}), 400
        event.location = location

    if date_str is not None or time_str is not None:
        if not date_str or not time_str:
            return jsonify({"message": "Both date and time are required"}), 400

        try:
            dt_string = f"{date_str} {time_str}"
            date_and_time = datetime.strptime(dt_string, "%d.%m.%Y %H:%M")
            date_and_time = date_and_time.replace(tzinfo=timezone.utc)

            if date_and_time <= datetime.now(timezone.utc):
                return jsonify({"message": "Event date must be in the future"}), 400

            event.date_and_time = date_and_time
        except ValueError:
            return jsonify({"message": "Invalid date format. Use DD.MM.YYYY and HH:MM"}), 400
    
    event.edited = True

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({"message": "Internal server error"}), 500

    return jsonify({
        "message": "Event edited successfully"
    }), 200

@events_bp.route("/feed", methods=["GET"])
@limiter.limit("600 per minute")
def feed():
    try:
        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=Constants.PAGINATION_DEFAULT_LIMIT, type=int)
        sort=request.args.get("sort",default=1,type=int)
        
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
                "name": event.name,
                "description": event.description,
                "date": event.date_and_time.strftime("%d.%m.%Y"),
                "time": event.date_and_time.strftime("%H:%M"),
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