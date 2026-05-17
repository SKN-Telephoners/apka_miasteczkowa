from flask import Blueprint, request, current_app
from backend.models import Notification
from backend.models.notification import NotificationTag
from backend.extensions import limiter, db
from backend.constants import Constants
from backend.responses import ResponseTypes, make_api_response
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import jwt_required, get_current_user
from backend.helpers import sanitize_input
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from backend.helpers import validate_uuid

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")
local_tz = ZoneInfo("Europe/Warsaw")

'''
Input: 
    Header { "Authorization": "Bearer <Access_Token>" }, 
    Query Params { 
        page=<int>, 
        limit=<int>, 
        q=<str>, 
        status="unread"/"read"/"all", 
        type=<NotificationTag_Value>, 
        created_window="today"/"week"/..., 
        sort_mode="newest"/"oldest" }
Action: Retrieves paginated notifications for the current user. Filters by read status, type, and creation date. Converts timestamps to the local "Europe/Warsaw" timezone.
Data sent to the frontend: {"data": [{
    "notification_id": <str>, 
    "type": <str>, 
    "is_read": <bool>, 
    "date": <str>, 
    "time": <str>, 
    "payload": <dict>}], 
"pagination": {
    "page": <int>, 
    "limit": <int>, 
    "total": <int>, 
    "pages": <int>, 
    "has_next": <bool>, 
    "unread_count": <int>}}
Output: 200 OK (or 500 on error)
'''
@notifications_bp.route("/", methods=["GET"])
@limiter.limit("600 per minute")
@jwt_required()
def get_notifications():
    try:
        user = get_current_user()
        user_id = user.user_id

        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=Constants.PAGINATION_DEFAULT_LIMIT, type=int)
        
        q = request.args.get("q", default="", type=str).strip()
        q = sanitize_input(q) if q else ""
        
        status = request.args.get("status", default="all", type=str).lower()
        notif_tag = request.args.get("tag", default="all", type=str)
        created_window = request.args.get("created_window", default="all", type=str).lower()
        sort_mode = request.args.get("sort_mode", default="newest", type=str).lower()


        if page < 1:
            page = 1
        if limit < 1:
            limit = Constants.PAGINATION_DEFAULT_LIMIT
        if limit > Constants.MAX_PAGINATION_LIMIT:
            limit = Constants.MAX_PAGINATION_LIMIT

        query = Notification.query.filter(Notification.user_id == user_id)

        if q:
            search_filter = f"%{q}%"
            query = query.filter(
                Notification.payload.op('->>')('message').ilike(search_filter)
            )

        if status == "unread":
            query = query.filter(Notification.is_read == False)
        elif status == "read":
            query = query.filter(Notification.is_read == True)

        if notif_tag != "all":
            try:
                enum_tag = NotificationTag(notif_tag)
                query = query.filter(Notification.tag == enum_tag)
            except ValueError:
                pass


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
                query = query.filter(Notification.created_at < (now - timedelta(days=365)))
            else:
                query = query.filter(Notification.created_at >= start_date)


        if sort_mode == "oldest": 
            query = query.order_by(Notification.created_at.asc())
        else:
            query = query.order_by(Notification.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=limit, error_out=False)

        notification_list = [
            {
                "notification_id": str(notif.notification_id),
                "tag": notif.tag.value,
                "is_read": notif.is_read,
                "date": notif.created_at.astimezone(local_tz).strftime("%d.%m.%Y"),
                "time": notif.created_at.astimezone(local_tz).strftime("%H:%M"),
                "payload": notif.payload 
            }
            for notif in pagination.items
        ]

        current_app.logger.info(f"INFO: /get_notifications, retrieved notifications for user: {user_id}")
        return make_api_response(ResponseTypes.SUCCESS, data={
            "data": notification_list,
            "pagination": {
                "page": pagination.page,
                "limit": limit,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "unread_count": Notification.query.filter_by(user_id=user_id, is_read=False).count() if page == 1 else None 
            }
        })
    except Exception as e:
        current_app.logger.error(f"ERROR: /get_notifications, DB exception occured:")
        current_app.logger.exception(e, stack_info=True)
        return make_api_response(ResponseTypes.SERVER_ERROR)


@notifications_bp.route("<notification_id>/read", methods=["PUT"])
@limiter.limit("600 per minute")
@jwt_required()
def read_notification(notification_id):
    user = get_current_user()

    n_uuid = validate_uuid(notification_id)
    if not n_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid notification UD format")
    
    notification = db.session.get(Notification, n_uuid)
    if notification is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="This notification does not exist")
    
    if user.user_id != notification.user_id:
        current_app.logger.warning(f"WARNING: /read_notification, user {user.user_id} attempted to read notification {notification_id} without permissions")
        return make_api_response(ResponseTypes.FORBIDDEN, message="You can read your own notifications only")
    
    try:
        notification.is_read = True
        db.session.commit()
        current_app.logger.info(f"INFO: /read_notifications, user {user.user_id} successfully read notification {notification_id}")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /read_notifiaction, DB exception occured:")
        current_app.logger.exception(e, stack_info=True)
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Notification read successfully")