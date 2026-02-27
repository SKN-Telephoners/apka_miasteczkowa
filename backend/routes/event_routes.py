from flask import Blueprint, request, jsonify, abort
from backend.models import Event
from backend.models import Invite, User
from backend.extensions import db, limiter
from flask_jwt_extended import jwt_required, get_current_user,get_jwt_identity
import uuid
from datetime import datetime, timezone

events_bp = Blueprint("events", __name__, url_prefix="/api/events")

@events_bp.route("/create", methods=["POST"])
@limiter.limit("100 per minute")
@jwt_required()
def create_event():
    user = get_current_user()

    event_data = request.get_json()
    required_keys = {"name", "description", "date", "time", "location"}

    if not event_data or not required_keys.issubset(event_data.keys()):
        return jsonify({"message": "Bad request"}), 400
    
    name = event_data.get("name", "").strip()
    description = event_data.get("description", "").strip()
    date_str = event_data.get("date")
    time_str = event_data.get("time")
    location = event_data.get("location", "").strip()

    if not (3 <= len(name) <= 32):
        return jsonify({"message": "Event name must be between 3 and 32 characters"}), 400
        
    if len(location) > 32:
        return jsonify({"message": "Location name is too long (max 32 chars)"}), 400
        
    if len(description) > 1000:
         return jsonify({"message": "Description is too long (max 1000 chars)"}), 400

    try:
        dt_string = f"{date_str} {time_str}"
        date_and_time = datetime.strptime(dt_string, "%d.%m.%Y %H:%M")
        date_and_time = date_and_time.replace(tzinfo=timezone.utc)
        
        if date_and_time <= datetime.now(timezone.utc):
             return jsonify({"message": "Event date must be in the future"}), 400
             
    except ValueError:
        return jsonify({"message": "Invalid date format. Use DD.MM.YYYY and HH:MM"}), 400

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
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({"message": "Internal server error"}), 500
    
    return {
        "message": "Event created successfully",
        "event_id": new_event.event_id
    }, 200

@events_bp.route("/delete/<event_id>", methods=["DELETE"])
@jwt_required()
def delete_event(event_id):
    user = get_current_user()
    try:
        event_id = uuid.UUID(event_id)
    except Exception:
        return jsonify({"message": "Invalid event ID format"}), 400
    
    event = Event.query.filter_by(event_id=event_id).first()

    if event is None:
        return {
            "message": "Event doesn't exist"
        }, 404

    if user.user_id != event.creator_id:
        return {
            "message": "You can delete your own events only"
        }, 403
    
    try:
        db.session.delete(event)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({"message": "Internal server error"}), 500

    return jsonify ({
        "message": "Event deleted successfully"
    }), 200

@events_bp.route("/feed", methods=["GET"])
def feed():
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=20, type=int)
    sort=request.args.get("sort",default=1,type=int)
    
    if sort==1:
        events=Event.query \
            .order_by(Event.date_and_time.asc())
    elif sort==2:
        events=Event.query \
            .order_by(Event.date_and_time.desc())
    
    pagination = events.paginate(page=page, per_page=limit, error_out=False)
    
    event_list=[
        {
            "id": event.event_id,
            "name": event.name,
            "description": event.description,
            "date": event.date_and_time.strftime("%d.%m.%Y"),
            "time": event.date_and_time.strftime("%H:%M"),
            "location": event.location,
            "creator_id": event.creator_id
        }
        for event in pagination.items
    ]

    return jsonify({
        "data": event_list,
        "pagination": {
            "page": pagination.page,
            "limit": limit,
            "total": pagination.total,
            "pages": pagination.pages
        }
    }) ,200

@events_bp.route("/<uuid:event_id>/invite/new", methods=["POST"])
@jwt_required()
def invite_for_event(event_id):
    
    event=event_id_sefe(event_id)
    jwt_check(event)

    invent_data = request.get_json()
    required_keys = {"user_id"}

    

    if not invent_data or not required_keys.issubset(invent_data.keys()):
        return jsonify({"message": "Bad request"}), 400
    
    list_invite_id=invent_data.get("user_id")

    for invite_id in list_invite_id:
        existing=Invite.query.filter_by(event_id=event_id,user_id=invite_id).first()

        if not existing:

            new_record=Invite(
                event_id=event_id,
                user_id=invite_id
            )

            db.session.add(new_record)
                
             
    try:
        db.session.commit()
    except  Exception as e:
                db.session.rollback()
                print(f"Database error: {e}")
                return jsonify({"message": "Internal server error"}), 500
    return {
        "message": "Invite successfully"
    }, 200

@events_bp.route("/<uuid:event_id>/invite/list",methods=["GET"])
@jwt_required()
def invite_on_event(event_id):

    event=event_id_sefe(event_id)
    jwt_check(event)

    users=(db.session.query(User)
           .join(Invite, Invite.user_id == User.user_id)
           .filter(Invite.event_id == event_id)
           .all()
           )
    
    invite_list=[
        {
            "id":user.user_id,
            "username":user.username,
            "email":user.email
        }
        for user in users
    ]

    return jsonify(
        {
            "data":invite_list
        }
    ),200

@events_bp.route("/<uuid:event_id>/invite/delete",methods=["DELETE"])
@jwt_required()
def delete_invite(event_id):

    event=event_id_sefe(event_id)
    jwt_check(event)

    invent_data = request.get_json()
    required_keys = {"user_id"}

    if not invent_data or not required_keys.issubset(invent_data.keys()):
        return jsonify({"message": "Bad request"}), 400
    
    list_invite_id_to_delete=invent_data.get("user_id")

    
    for invite_id in list_invite_id_to_delete:
        existing=Invite.query.filter_by(event_id=event_id,user_id=invite_id).first()

        if existing:

            db.session.delete(existing)

    try:
        db.session.commit()
    except  Exception as e:
                db.session.rollback()
                print(f"Database error: {e}")
                return jsonify({"message": "Internal server error"}), 500
    return {
        "message": "delete successfully"
    }, 200


####sefty######

def event_id_sefe(event_id):
    event = Event.query.get(event_id)
    if not event:
        abort(404,description="Event not found")
    return event
    
def jwt_check(event):
    current_user_id = get_jwt_identity()

    if event.creator_id != current_user_id:
        abort(403, description="Unauthorized")
                

