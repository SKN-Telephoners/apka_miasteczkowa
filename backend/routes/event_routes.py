from flask import jsonify, Blueprint, request, current_app
from backend.models.event import Event, Event_visibility, Event_participants, Invites, InviteRequestStatus
from backend.models.event import Pictures
from backend.models import User, Comment, Friendship 
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
from sqlalchemy import or_, and_, func, case, exists
from sqlalchemy.orm import joinedload

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
        q = sanitize_input(str(request.args.get("q", ""))).strip()
        visibility = str(request.args.get("visibility", "all")).strip().lower()
        participation = str(request.args.get("participation", "all")).strip().lower()
        created_window = str(request.args.get("created_window", "all")).strip().lower()
        sort_mode = str(request.args.get("sort_mode", "default")).strip().lower()
        creator_source = str(request.args.get("creator_source", "all")).strip().lower()

        if page < 1:
            page = 1
        if limit < 1:
            limit = Constants.PAGINATION_DEFAULT_LIMIT
        if limit > Constants.MAX_PAGINATION_LIMIT:
            limit = Constants.MAX_PAGINATION_LIMIT

        participant_exists = exists().where(
            and_(
                Event_participants.event_id == Event.event_id,
                Event_participants.user_id == user_id,
            )
        )

        visibility_exists = exists().where(
            and_(
                Event_visibility.event_id == Event.event_id,
                Event_visibility.shared_with == user_id,
            )
        )

        events = Event.query.options(joinedload(Event.pictures)).filter(
            or_(
                Event.is_private.is_(False),
                Event.creator_id == user_id,
                participant_exists,
                visibility_exists,
            )
        )

        if visibility == "public":
            events = events.filter(Event.is_private.is_(False))
        elif visibility == "private":
            events = events.filter(Event.is_private.is_(True))

        if participation == "joined":
            events = events.filter(
                or_(
                    Event.creator_id == user_id,
                    participant_exists,
                )
            )
        elif participation == "not_joined":
            events = events.filter(
                and_(
                    Event.creator_id != user_id,
                    ~participant_exists,
                )
            )

        if creator_source in ("friends", "others"):
            friend_ids = db.session.query(
                Friendship.friend_id
            ).filter(Friendship.user_id == user_id).union(
                db.session.query(
                    Friendship.user_id
                ).filter(Friendship.friend_id == user_id)
            ).all()
            friend_ids_set = {str(f[0]) for f in friend_ids}

            if creator_source == "friends":
                events = events.filter(Event.creator_id.in_(friend_ids_set) if friend_ids_set else False)
            elif creator_source == "others":
                events = events.filter(~Event.creator_id.in_(friend_ids_set) if friend_ids_set else True)

        now_utc = datetime.now(timezone.utc)

        if created_window == "today":
            threshold = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
            events = events.filter(Event.created_at >= threshold)
        elif created_window == "week":
            start_today = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
            weekday = start_today.weekday()
            threshold = start_today - timedelta(days=weekday)
            events = events.filter(Event.created_at >= threshold)
        elif created_window == "month":
            threshold = now_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            events = events.filter(Event.created_at >= threshold)
        elif created_window == "year":
            threshold = now_utc.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            events = events.filter(Event.created_at >= threshold)
        elif created_window == "older":
            threshold = now_utc.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            events = events.filter(or_(Event.created_at.is_(None), Event.created_at < threshold))

        if q:
            normalized = "%" + "%".join(q.lower().split()) + "%"
            events = events.join(User, User.user_id == Event.creator_id).filter(
                or_(
                    func.lower(Event.event_name).like(normalized),
                    func.lower(Event.location).like(normalized),
                    func.lower(Event.description).like(normalized),
                    func.lower(User.username).like(normalized),
                )
            )

        upcoming_first = case((Event.date_and_time >= now_utc, 0), else_=1)

        if sort_mode == "members_desc":
            events = events.order_by(
                upcoming_first.asc(),
                func.coalesce(Event.participant_count, 0).desc(),
                case((Event.date_and_time >= now_utc, Event.date_and_time), else_=None).asc(),
                case((Event.date_and_time < now_utc, Event.date_and_time), else_=None).desc(),
                Event.event_id.asc(),
            )
        elif sort_mode == "members_asc":
            events = events.order_by(
                upcoming_first.asc(),
                func.coalesce(Event.participant_count, 0).asc(),
                case((Event.date_and_time >= now_utc, Event.date_and_time), else_=None).asc(),
                case((Event.date_and_time < now_utc, Event.date_and_time), else_=None).desc(),
                Event.event_id.asc(),
            )
        elif sort_mode == "comments_desc":
            events = events.order_by(
                upcoming_first.asc(),
                func.coalesce(Event.comment_count, 0).desc(),
                case((Event.date_and_time >= now_utc, Event.date_and_time), else_=None).asc(),
                case((Event.date_and_time < now_utc, Event.date_and_time), else_=None).desc(),
                Event.event_id.asc(),
            )
        elif sort_mode == "comments_asc":
            events = events.order_by(
                upcoming_first.asc(),
                func.coalesce(Event.comment_count, 0).asc(),
                case((Event.date_and_time >= now_utc, Event.date_and_time), else_=None).asc(),
                case((Event.date_and_time < now_utc, Event.date_and_time), else_=None).desc(),
                Event.event_id.asc(),
            )
        else:
            events = events.order_by(
                upcoming_first.asc(),
                case((Event.date_and_time >= now_utc, Event.date_and_time), else_=None).asc(),
                case((Event.date_and_time < now_utc, Event.date_and_time), else_=None).desc(),
                Event.event_id.asc(),
            )

        pagination = events.paginate(page=page, per_page=limit, error_out=False)

        event_ids = [event.event_id for event in pagination.items]

        participant_rows = (
            db.session.query(Event_participants.event_id)
            .filter(
                Event_participants.user_id == user_id,
                Event_participants.event_id.in_(event_ids),
            )
            .all()
        ) if event_ids else []
        participating_event_ids = {event_id for (event_id,) in participant_rows}

        creator_ids = {event.creator_id for event in pagination.items if event.creator_id is not None}
        creator_users = User.query.filter(User.user_id.in_(creator_ids)).all() if creator_ids else []
        creator_usernames = {str(u.user_id): u.display_name for u in creator_users}
        creator_profile_pictures = {
            str(u.user_id): cloudinary_url(u.profile_picture, secure=True)[0] if u.profile_picture else None
            for u in creator_users
        }

        event_list = []
        for event in pagination.items:
            local_dt = event.date_and_time.astimezone(local_tz) if event.date_and_time else None
            event_payload = {
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
                "creator_username": creator_usernames.get(str(event.creator_id)),
                "creator_profile_picture_url": creator_profile_pictures.get(str(event.creator_id)),
                "created_at": event.created_at.isoformat() if event.created_at else None,
                "comment_count": int(event.comment_count or 0),
                "participant_count": int(event.participant_count or 0),
                "participation_count": int(event.participant_count or 0),
                "is_participating": event.creator_id == user_id or event.event_id in participating_event_ids,
                "is_joined": event.creator_id == user_id or event.event_id in participating_event_ids,
                "is_private": event.is_private,
            }
            event_list.append(event_payload)

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
        if event.creator_id != u_uuid:
            return make_api_response(ResponseTypes.FORBIDDEN, message="Only creator of the private event can invite")

        has_visibility = db.session.query(Event_visibility).filter_by(event_id=e_uuid, shared_with=i_uuid).first()
    else:
        has_visibility = None

    is_already_participant = db.session.query(Event_participants).filter_by(event_id=e_uuid, user_id=i_uuid).first()
    if is_already_participant:
        return make_api_response(ResponseTypes.CONFLICT, message="User is already participating in this event")
        
    existing_invite = db.session.query(Invites).filter_by(event_id=e_uuid, inviter_id=u_uuid, invited_id=i_uuid).first()
    if existing_invite:
        return make_api_response(ResponseTypes.CONFLICT, message="Invite already sent")
        
    try:
        if event.is_private and not has_visibility:
            db.session.add(
                Event_visibility(
                    event_id=e_uuid,
                    sharing=u_uuid,
                    shared_with=i_uuid,
                )
            )

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


@events_bp.route("/invites/<event_id>", methods=["GET"])
@limiter.limit("200 per minute")
@jwt_required()
def get_event_invites(event_id):
    user = get_current_user()
    e_uuid = validate_uuid(event_id)
    u_uuid = validate_uuid(user.user_id)

    if not e_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid event ID")
    if not u_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid user ID")

    event = db.session.get(Event, e_uuid)
    if event is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="This event does not exist")

    invited_ids = [
        str(invite.invited_id)
        for invite in db.session.query(Invites).filter_by(
            event_id=e_uuid,
            inviter_id=u_uuid,
            status=InviteRequestStatus.pending,
        ).all()
    ]

    return make_api_response(ResponseTypes.SUCCESS, data={"invited_ids": invited_ids})


@events_bp.route("/invites/incoming", methods=["GET"])
@limiter.limit("300 per minute")
@jwt_required()
def get_incoming_invites():
    user = get_current_user()
    u_uuid = validate_uuid(user.user_id)

    if not u_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid user ID")

    invites = db.session.query(Invites).filter_by(
        invited_id=u_uuid,
        status=InviteRequestStatus.pending,
    ).order_by(Invites.created_at.desc()).all()

    incoming_invites = []
    for invite in invites:
        inviter = invite.inviter
        event = invite.event
        creator = event.creator if event else None

        if not inviter or not event:
            continue

        inviter_profile_picture = None
        if inviter.profile_picture:
            inviter_profile_picture = {
                "cloud_id": inviter.profile_picture,
                "url": cloudinary_url(inviter.profile_picture, secure=True)[0],
            }

        creator_profile_picture_url = None
        if creator and creator.profile_picture:
            creator_profile_picture_url = cloudinary_url(creator.profile_picture, secure=True)[0]

        pictures = []
        for pic in event.pictures:
            pictures.append({
                "cloud_id": pic.cloud_id,
                "url": cloudinary_url(pic.cloud_id, secure=True)[0],
            })

        incoming_invites.append({
            "id": str(invite.invite_id),
            "createdAt": invite.created_at.isoformat() if invite.created_at else None,
            "inviter": {
                "id": str(inviter.user_id),
                "username": inviter.display_name,
                "email": inviter.email,
                "academy": inviter.academy,
                "course": inviter.course,
                "profile_picture": inviter_profile_picture,
            },
            "event": {
                "id": str(event.event_id),
                "name": event.event_name,
                "description": event.description or "",
                "date": event.date_and_time.astimezone(local_tz).strftime("%d.%m.%Y"),
                "time": event.date_and_time.astimezone(local_tz).strftime("%H:%M"),
                "location": event.location,
                "creator_id": str(event.creator_id),
                "creator_username": creator.display_name if creator else None,
                "creator_profile_picture_url": creator_profile_picture_url,
                "created_at": event.created_at.isoformat() if event.created_at else None,
                "comment_count": int(event.comment_count or 0),
                "participant_count": int(event.participant_count or 0),
                "is_private": event.is_private,
                "pictures": pictures,
            },
        })

    return make_api_response(ResponseTypes.SUCCESS, data={"incomingInvites": incoming_invites})


@events_bp.route("/<user_id>/info", methods=["GET"])
@jwt_required()
def get_my_events(user_id):
    user = User.query.filter_by(user_id=user_id).first()
    
    created_events = Event.query.filter_by(creator_id=user.user_id).all()
    
    participating_events = db.session.query(Event).join(
        Event_participants, Event.event_id == Event_participants.event_id
    ).filter(Event_participants.user_id == user.user_id).all()
    
    created_data = [{"event_id": str(e.event_id), "name": e.event_name} for e in created_events]
    participating_data = [{"event_id": str(e.event_id), "name": e.event_name} for e in participating_events]
    
    return make_api_response(
        ResponseTypes.SUCCESS, 
        data={"created": created_data, "participating": participating_data}
    )