from flask import Blueprint, request, current_app
from backend.models import Notification
from backend.models.notification import NotificationTag
from backend.extensions import limiter, db
from backend.constants import Constants
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required, get_current_user
from backend.helpers import sanitize_input
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")
local_tz = ZoneInfo("Europe/Warsaw")

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
        notif_type = request.args.get("type", default="all", type=str)
        created_window = request.args.get("created_window", default="all", type=str).lower()
        sort_mode = request.args.get("sort_mode", default="newest", type=str).lower()


        if page < 1:
            page = 1
        if limit < 1:
            limit = Constants.PAGINATION_DEFAULT_LIMIT
        if limit > Constants.MAX_PAGINATION_LIMIT:
            limit = Constants.MAX_PAGINATION_LIMIT

        help_query = db.select(Notification).filter(Notification.user_id == user_id)
        query = db.session.execute(help_query, bind_arguments={'bind_key': 'readonly'}).scalars().all()

        if q:
            search_filter = f"%{q}%"
            query = query.filter(
                Notification.payload.op('->>')('message').ilike(search_filter)
            )

        if status == "unread":
            query = query.filter(Notification.is_read == False)
        elif status == "read":
            query = query.filter(Notification.is_read == True)

        if notif_type != "all":
            try:
                enum_type = NotificationTag(notif_type)
                query = query.filter(Notification.type == enum_type)
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
                "type": notif.type.value,
                "is_read": notif.is_read,
                "date": notif.created_at.astimezone(local_tz).strftime("%d.%m.%Y"),
                "time": notif.created_at.astimezone(local_tz).strftime("%H:%M"),
                "payload": notif.payload 
            }
            for notif in pagination.items
        ]

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
        current_app.logger.error(f"Error in get_notifications: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)