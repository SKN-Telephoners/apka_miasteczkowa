from flask import Blueprint, request, current_app
from backend.models.event import Event, Event_visibility, Event_participants, Invites
from backend.models import User
from backend.extensions import db, limiter, redis_client
from backend.constants import Constants
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required, get_current_user
from backend.helpers import validate_uuid, sanitize_input, get_event_cache_key, cache_event_data
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.exc import SQLAlchemyError
from cloudinary.utils import cloudinary_url
from sqlalchemy import or_
import json
from .event_helpers import serialize_event_payload

getters_bp = Blueprint("event_getters", __name__, url_prefix="/api/events")
local_tz = ZoneInfo("Europe/Warsaw")

'''
Input: URL Parameter <uuid:event_id>, Header { "Authorization": "Bearer <Access_Token>" }
Action: Gets information about a single event. Validates user permissions
Data sent to the frontend: {
    "data": {
        <Event_Object_Fields>,
        "is_participating": <bool>,
        "is_joined": <bool>
    }
}
Output: 200 success (or 400/403/404/500 on error)
'''
@getters_bp.route("get/<event_id>", methods=["GET"])
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
            current_app.logger.warning(f"WARNING: /get_event, user {user.user_id} tried to access event {event_id} that does not exist")
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
@getters_bp.route("/feed", methods=["GET"])
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

        participation_subquery = db.session.query(Event_participants.event_id).filter(
            Event_participants.event_id == Event.event_id,
            Event_participants.user_id == user_id,
        )

        query = Event.query.filter(
            or_(
                Event.is_private == False,
                Event.creator_id == user_id,
                visibility_subquery.exists(),
                participation_subquery.exists(),
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

        event_ids = [str(e.event_id) for e in pagination.items]

        if event_ids:
            part_query = db.select(Event_participants.event_id).filter(
                Event_participants.user_id == user_id,
                Event_participants.event_id.in_(event_ids)
            )
            participating_event_ids = {str(r[0]) for r in
                                       db.session.execute(part_query, bind_arguments={'bind_key': 'readonly'}).all()}
        else:
            participating_event_ids = set()

        final_event_list = []

        creator_ids = {e.creator_id for e in pagination.items if e.creator_id}
        user_query = db.select(User).filter(User.user_id.in_(creator_ids))
        creator_users = db.session.execute(user_query, bind_arguments={'bind_key': 'readonly'}).scalars().all() if creator_ids else []
        creator_lookup = {str(u.user_id): u for u in creator_users}

        for event in pagination.items:
            eid_str = str(event.event_id)
            cached_val = redis_client.get(get_event_cache_key(eid_str))

            if cached_val:
                event_data = json.loads(cached_val)
            else:
                event_data = serialize_event_payload(event, None, creator_lookup, set())
                cache_event_data(eid_str, event_data)
            
            is_joined = (str(event.creator_id) == str(user_id)) or (eid_str in participating_event_ids)
            event_data["is_participating"] = is_joined
            event_data["is_joined"] = is_joined
            
            final_event_list.append(event_data)

        current_app.logger.info(f"INFO: /feed, user {user_id} successfully fetched events feed page {page}")
        return make_api_response(ResponseTypes.SUCCESS, data={
            "data": final_event_list,
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
Input: URL Parameter <uuid:user_id>, Header { "Authorization": "Bearer <Access_Token>" }
Action: Fetches all events where the specified user is the creator. Returns a list of serialized event objects
Data sent to the frontend: {"data": [<Serialized_Event_Object>]}
Output: 200 OK (or 400/500 on error)
'''
@getters_bp.route("/<user_id>/creator", methods=["GET"])
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
@getters_bp.route("/<user_id>/participant", methods=["GET"])
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
    
    current_app.logger.info(f"INFO: /user/participant, successfully fetched participating events for user {u_uuid}")
    return make_api_response(
        ResponseTypes.SUCCESS, 
        data={"data": participating_data}
    )

'''
Input: URL Parameter <uuid:event_id>, Header { "Authorization": "Bearer <Access_Token>" }
Action: Checks the database to see if the current user is a participant or the creator. Retrieves the total participant count
Data sent to the frontend: {"is_participating": <bool>, "participant_count": <int>}
Output: 200 OK (or 404/400/500 on error)
'''
@getters_bp.route("/participation/<event_id>", methods=["GET"])
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

    current_app.logger.info(f"INFO: /participation_status, user {user.user_id} checked participation status for event {event_id}")
    return make_api_response(ResponseTypes.SUCCESS, data={
        "is_participating": is_participating,
        "participant_count": int(event.participant_count or 0),
    })

'''
Input: URL Parameter <uuid:event_id>, Header { "Authorization": "Bearer <Access_Token>" }
Action: Retrieves all user IDs currently invited to the event. Endpoint restricted to the event creator only
Data sent to the frontend: {"invited_ids": [<str:uuid>]}
Output: 200 OK (or 404/403/400/500 on error)
'''
@getters_bp.route("/invites/<event_id>", methods=["GET"])
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

    event = db.session.get(Event, e_uuid)
    if event is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="This event does not exist")

    # Only the event creator can view sent invites
    if event.creator_id != u_uuid:
        return make_api_response(ResponseTypes.FORBIDDEN, message="Only the event creator can view sent invites")

    try:
        invites = db.session.query(Invites).filter_by(event_id=e_uuid).all()
        invited_ids = [str(invite.invited_id) for invite in invites]
        current_app.logger.info(f"INFO: /invites, user {u_uuid} successfully fetched invites for event {e_uuid}")
        return make_api_response(ResponseTypes.SUCCESS, data={"invited_ids": invited_ids})
    except SQLAlchemyError as e:
        current_app.logger.error(f"ERROR: /invites, DB exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
