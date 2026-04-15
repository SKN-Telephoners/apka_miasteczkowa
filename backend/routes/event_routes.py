from flask import Blueprint, request, current_app
from backend.models.event import Event, Event_visibility, Event_participants, Invites, InviteRequestStatus, Pictures, Location
from backend.models import User, Friendship
from backend.extensions import db, limiter
from backend.constants import Constants
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required, get_current_user
from backend.helpers import validate_uuid, sanitize_input
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.exc import SQLAlchemyError
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from sqlalchemy import or_, and_, asc, desc

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

    event = Event.query.filter_by(event_id=e_uuid).first()

    if event is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Event doesn't exist")

    if user.user_id != event.creator_id:
        current_app.logger.warning(f"Użytkownik {user.user_id} próbował usunąć event {event_id} bez uprawnień do niego")
        return make_api_response(ResponseTypes.FORBIDDEN, message="You can delete your own events only")
    try:
        for picture in event.pictures:
            try:
                cloudinary.uploader.destroy(picture.cloud_id)
            except Exception as cloud_err:
                current_app.logger.error(f"Failed to delete picture {picture.cloud_id} from Cloudinary: {cloud_err}")

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
    if event is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="This event does not exist")

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
        new_is_private = str(raw_is_private).strip().lower() in ['true', '1', 't', 'y', 'yes']
        if event.is_private and not new_is_private: # private -> public 
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
                current_app.logger.error(f"Failed to delete picture {pic_id} from Cloudinary: {cloud_err}")

            event.pictures.remove(pic_to_remove)

        for new_id in ids_to_add:
            new_picture = Pictures(cloud_id=new_id, event_id=event.event_id)
            event.pictures.append(new_picture)

    try:
        event.is_edited = True
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
        user_id = user.user_id

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

        visibility_subquery = db.session.query(Event_visibility.event_id).filter(
            Event_visibility.event_id == Event.event_id,
            Event_visibility.shared_with == user_id
        )

        query = Event.query.filter(
            or_(
                Event.is_private == False,
                Event.creator_id == user_id,
                visibility_subquery.exists()
            )
        )

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
        
        pagination = query.distinct().paginate(page=page, per_page=limit, error_out=False)

        creator_ids = {e.creator_id for e in pagination.items if e.creator_id}
        creators = {str(u.user_id): u.display_name for u in User.query.filter(User.user_id.in_(creator_ids)).all()}

        event_list=[
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
                "creator_username": creators.get(str(event.creator_id), "[deleted]"),
                "comment_count": str(event.comment_count),
                "participation_count": event.participant_count,
                "is_private": event.is_private,
                "is_joined": db.session.query(Event_participants).filter_by(
                    event_id=event.event_id, user_id=user_id
                ).first() is not None
            }
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
    if event is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="This event does not exist")
    
    if event.creator_id == user.user_id:
        is_participating = True
    else:
        is_participating = db.session.query(Event_participants).filter_by(event_id=e_uuid, user_id=user.user_id).first() is not None

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
    if event is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="This event does not exist")

    if event.creator_id == user.user_id:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Creator is already participating")

    if event.is_private:
        has_access = db.session.query(Event_visibility).filter_by(event_id=e_uuid, shared_with=user.user_id).first()
        if not has_access:
            return make_api_response(ResponseTypes.FORBIDDEN, message="This event is private and has not been shared with you lol")

    existing = db.session.query(Event_participants).filter_by(event_id=e_uuid, user_id=user.user_id).first()
    if existing:
        return make_api_response(ResponseTypes.CONFLICT, message="You are already participating in this event")

    try:
        participant = Event_participants(event_id=e_uuid, user_id=user.user_id)
        db.session.add(participant)
        event.participant_count = Event.participant_count + 1
        db.session.commit()
        db.session.refresh(event) # pobranie aktualnego stanu licznika, ochrona przed race condition
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
    if event is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="This event does not exist")

    if event.creator_id == user.user_id:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Creator cannot leave their own event")

    participant = db.session.query(Event_participants).filter_by(event_id=e_uuid, user_id=user.user_id).first()
    if not participant:
        return make_api_response(ResponseTypes.NOT_FOUND, message="You are not participating in this event")

    try:
        db.session.delete(participant)
        event.participant_count = Event.participant_count - 1
        db.session.commit()
        db.session.refresh(event)
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in leave_event: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Left event successfully", data={
        "participant_count": int(event.participant_count or 0),
    })

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
        return make_api_response(ResponseTypes.BAD_REQUEST, message="You cannot invite yourself")
    
    event = db.session.get(Event, e_uuid)
    if event is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="This event does not exist")

    is_friend = db.session.query(Friendship).filter(
        or_(
            and_(Friendship.user_id == u_uuid, Friendship.friend_id == i_uuid),
            and_(Friendship.user_id == i_uuid, Friendship.friend_id == u_uuid)
        )
    ).first()

    if not is_friend: 
        return make_api_response(ResponseTypes.FORBIDDEN, message="You can only invite your friends")
    
    if event.is_private:
        # na razie tylko autor ma możliwość zapraszania na swój event osoby, którym udostępnił do wyświetlania
        if event.creator_id != u_uuid:
            return make_api_response(ResponseTypes.FORBIDDEN, message="Only creator of the private event can invite")
        
        has_visibility = db.session.query(Event_visibility).filter_by(event_id=e_uuid, shared_with=i_uuid).first()
        if not has_visibility:
            return make_api_response(ResponseTypes.FORBIDDEN, message=f"User does not have priviledges to view this event")

    is_already_participant = db.session.query(Event_participants).filter_by(event_id=e_uuid, user_id=i_uuid).first()
    if is_already_participant:
        return make_api_response(ResponseTypes.CONFLICT, message="User is already participating in this event")
        
    existing_invite = db.session.query(Invites).filter_by(event_id=e_uuid, inviter_id=u_uuid, invited_id=i_uuid).first()
    if existing_invite:
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
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in invite_to_event: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    
    return make_api_response(ResponseTypes.CREATED, message="Invite created successfully")
       
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
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in delete_invite: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    
    return make_api_response(ResponseTypes.SUCCESS, message="Invite deleted successfully")
    
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
        return make_api_response(ResponseTypes.FORBIDDEN, message="You can only change status of the invites meant to you")
    
    if invite.status != InviteRequestStatus.pending:
        return make_api_response(ResponseTypes.CONFLICT, message="This invite is already accepted/declined")
    
    invite_data = request.get_json(silent=True)
    new_status = sanitize_input(str(invite_data.get("status"))).lower()

    try:
        if new_status == "accepted":
            invite.status  = InviteRequestStatus.accepted
            already_in = db.session.query(Event_participants).filter_by(event_id=invite.event_id, user_id=u_uuid).first()
            if not already_in:
                participant = Event_participants(
                    event_id=invite.event_id,
                    user_id=u_uuid,
                )
                db.session.add(participant)
                event = db.session.get(Event, invite.event_id)
                if event:
                    event.participant_count = Event.participant_count + 1
        elif new_status == "declined":
            invite.status = InviteRequestStatus.declined
        else:
            return make_api_response(ResponseTypes.INVALID_DATA, message="Incorrect status, choose declined/accepted")
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error in change_invite_status: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    
    return make_api_response(ResponseTypes.SUCCESS, message="Invite status changed successfully")

@events_bp.route("/<user_id>/creator", methods=["GET"])
@jwt_required()
def get_user_events_creator(user_id):
    u_uuid = validate_uuid(user_id)

    if not u_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid user ID")

    user = db.session.get(User, u_uuid)
    created_events = Event.query.filter_by(creator_id=user.user_id).all()
    
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
    
    return make_api_response(
        ResponseTypes.SUCCESS, 
        data={"data": created_data}
    )


@events_bp.route("/<user_id>/participant", methods=["GET"])
@jwt_required()
def get_user_events_participand(user_id):
    u_uuid = validate_uuid(user_id)

    if not u_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid user ID")

    user = db.session.get(User, u_uuid)
    
    participating_events = db.session.query(Event).join(
        Event_participants, Event.event_id == Event_participants.event_id
    ).filter(Event_participants.user_id == user.user_id).all()

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
    
    return make_api_response(
        ResponseTypes.SUCCESS, 
        data={"data": participating_data}
    )


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

    query = db.session.query(Location).filter_by(location_name=location_name).first()    
    
    if not query:
        return make_api_response(ResponseTypes.NOT_FOUND, message="Location of that name not found")
    
    coordinates = query.coordinates

    return make_api_response(ResponseTypes.SUCCESS, data={"coordinates": str(coordinates)})
