from flask import Blueprint, request, current_app
from backend.models import Event, Comment, User
from backend.extensions import db, limiter
from backend.constants import Constants
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required, get_current_user
from backend.helpers import validate_uuid, sanitize_input, has_event_access,  get_event_cache_key, invalidate_event_cache, get_cached_event, cache_event_data
from sqlalchemy.exc import SQLAlchemyError

comments_bp = Blueprint("comments", __name__, url_prefix="/api/comments")

@comments_bp.route("/create/<event_id>", methods=["POST"])
@jwt_required()
@limiter.limit("600 per minute")
def create_comment(event_id):
    user = get_current_user()
    e_uuid = validate_uuid(event_id)
    if not e_uuid:
        current_app.logger.warning(f"WARNING: /create_comment, user: {user.user_id} tried to add comment to event of invalid event_id: {event_id}")
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid event ID")
    event = db.session.get(Event, e_uuid)

    if not event:
        current_app.logger.warning(f"WARNING: /create_comment, user: {user.user_id} tried to add comment to not existing event")
        return make_api_response(ResponseTypes.NOT_FOUND, message="Event doesn't exist")
    
    comment_data = request.get_json(silent=True)
    required_keys = {"content"}
    
    if not comment_data or not required_keys.issubset(comment_data.keys()):
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Missing content")
    
    content = sanitize_input(str(comment_data["content"])).strip()
    if not content:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Content cannot be empty")
    
    if len(content) > Constants.MAX_COMMENT_LEN:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Comment too long")
    
    try:
        new_comment = Comment(user_id=user.user_id, event_id=event_id, content=comment_data["content"])

        db.session.add(new_comment)
        db.session.commit()
        invalidate_event_cache(str(event_id))
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /create_comment, DB exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
    current_app.logger.info(f"INFO: /create_comment, user: {user.user_id} successfuly added comment to event of event_id: {event_id}")
    return make_api_response(ResponseTypes.CREATED, message="Comment created successfully")


@comments_bp.route("/reply/<parent_comment_id>", methods=["POST"])
@jwt_required()
@limiter.limit("90 per minute")
def reply_to_comment(parent_comment_id):
    user = get_current_user()
    p_uuid = validate_uuid(parent_comment_id)
    
    if not p_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid parent comment ID")
    parent_comment = Comment.query.filter_by(comment_id=parent_comment_id).first()

    if parent_comment is None:
        current_app.logger.warning(f"WARNING: /reply_to_comment, parent comment does not exist/is invalid, ID: {parent_comment_id}")
        return make_api_response(ResponseTypes.NOT_FOUND, message="Parent comment doesn't exist")

    event = db.session.get(Event, parent_comment.event_id)

    if event is None:
        current_app.logger.warning(f"WARNING: /reply_to_comment, event does not exist, parent comment ID: {parent_comment_id}")
        return make_api_response(ResponseTypes.NOT_FOUND, message="Event doesn't exist")
    
    comment_data = request.get_json(silent=True)
    required_keys = {"content"}
    
    if not comment_data or not required_keys.issubset(comment_data.keys()):
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Missing content")
    
    content = str(comment_data["content"]).strip()
    if not content:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Content cannot be empty")
    
    if len(content) > Constants.MAX_COMMENT_LEN:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Comment too long")

    try:
        new_comment = Comment(
            user_id=user.user_id,
            event_id=parent_comment.event_id,
            content=comment_data["content"],
            parent_comment_id=parent_comment_id
            )

        db.session.add(new_comment)
        db.session.commit()
        invalidate_event_cache(str(parent_comment.event_id))
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /reply_to_comment, DB exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    current_app.logger.info(f"INFO: /reply_to_comment, user: {user.user_id} successfuly replied to comment of ID {parent_comment.comment_id}")
    return make_api_response(ResponseTypes.CREATED, message="Reply created successfully")

@comments_bp.route("/delete/<comment_id>", methods=["DELETE"])
@jwt_required()
@limiter.limit("90 per minute")
def delete_comment(comment_id):
    user = get_current_user()
    c_uuid = validate_uuid(comment_id)

    if not c_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid comment ID format")

    comment = Comment.query.filter_by(comment_id=comment_id).first()

    if comment is None:
        current_app.logger.warning(f"WARNING: /delete_comment, user {user.user_id} tried to delete not existing comment of ID: {comment_id}")
        return make_api_response(ResponseTypes.NOT_FOUND, message="Comment doesn't exist")

    if user.user_id != comment.user_id:
        current_app.logger.warning(f"WARNING: /delete_comment, user {user.user_id} tried to delete a comment that is not his of ID: {comment_id}")
        return make_api_response(ResponseTypes.FORBIDDEN, message="You can delete your own comments only")
        
    try: 
        comment.soft_delete()
        db.session.commit()
        invalidate_event_cache(str(comment.event_id))
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /delete_comment, DB exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    current_app.logger.info(f"INFO: /delete_comment, user: {user.user_id} successfuly deleted comment of ID {comment_id}")
    return make_api_response(ResponseTypes.SUCCESS, message="Comment deleted successfully")

@comments_bp.route("/edit/<comment_id>", methods=["POST"])
@jwt_required()
def edit_comment(comment_id):
    user = get_current_user()
    c_uuid = validate_uuid(comment_id)
    if not c_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid UUID format")
    
    comment = Comment.query.filter_by(comment_id=comment_id).first()

    if not comment:
        current_app.logger.warning(f"WARNING: /edit_comment, user {user.user_id} tried to edit non existant comment")
        return make_api_response(ResponseTypes.NOT_FOUND, message="Comment doesn't exist")

    if user.user_id != comment.user_id:
        current_app.logger.warning(f"WARNING: /edit_comment, user: {user.user_id} tried to edit comment: {comment_id} of user: {comment.user_id}")
        return make_api_response(ResponseTypes.FORBIDDEN, message="You can edit your own comments only")
    if comment.deleted:
        current_app.logger.warning(f"WARNING: /edit_comment, user: {user.user_id} tried to edit comment: {comment_id} that is deleted")
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Cannot edit a deleted comment")
        
    data = request.get_json(silent=True)
    if not data or "new_content" not in data:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Missing new_content")
    new_content = str(data["new_content"]).strip()

    if not new_content:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Content cannot be enpty")
    
    if len(new_content) > Constants.MAX_COMMENT_LEN:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Comment too long")    
    try:
        comment.content = new_content
        comment.edited = True
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /edit_comment, DB exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)

    current_app.logger.info(f"INFO: /edit_comment, user {user.user_id} successfully edited comment: {comment_id}")
    return make_api_response(ResponseTypes.SUCCESS, message="Comment edited successfully")

@comments_bp.route("/event/<event_id>", methods=["GET"])
@jwt_required()
def get_comments_list(event_id):
    user = get_current_user()
    e_uuid = validate_uuid(event_id)
    if not e_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid event ID")
    
    event = db.session.get(Event, e_uuid)
    if not event:
        current_app.logger.warning(f"WARNING: /get_comment, event: {event_id} does not exist, user: {user.user_id} tried to get comments of that event")
        return make_api_response(ResponseTypes.NOT_FOUND)
    
    if not has_event_access(user.user_id, event):
        current_app.logger.warning(f"WARNING: /get_comment, user: {user.user_id} tried to get comments of event {event_id} that is not visible to him")
        return make_api_response(ResponseTypes.FORBIDDEN, message="You do not have access to this event")

    try:
        comments = Comment.query.filter_by(event_id=event_id).order_by(Comment.created_at.asc()).all()

        if not comments:
            current_app.logger.info(f"INFO: /get_comment, no comments available in event {event_id}")
            return make_api_response(ResponseTypes.SUCCESS, message="Empty comments list", data={"comments": []})

        user_ids = {c.user_id for c in comments if c.user_id is not None and not c.deleted}
        users = User.query.filter(User.user_id.in_(user_ids)).all() if user_ids else []
        usernames_by_id = {str(user.user_id): user.display_name for user in users}

        top_level_comments = [c for c in comments if c.parent_comment_id is None]
        comments_tree = [c.to_dict() for c in top_level_comments]

        def attach_usernames(comment_node):
            comment_user_id = comment_node.get("user_id")
            comment_node["username"] = usernames_by_id.get(comment_user_id) if comment_user_id else None
            for reply in comment_node.get("replies", []):
                attach_usernames(reply)

        for comment_node in comments_tree:
            attach_usernames(comment_node)

        current_app.logger.info(f"INFO: /get_comment, comments in event {event_id} sent to frontend")
        return make_api_response(ResponseTypes.SUCCESS, message="Comments list", data={"comments": comments_tree})
    except SQLAlchemyError as e:
        current_app.logger.error(f"ERROR: /get_comment, DB exception occured: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR)
