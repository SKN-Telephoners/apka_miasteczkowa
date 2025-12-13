from flask import Blueprint, request, jsonify
from backend.models import Event, Comment
from backend.extensions import db
from flask_jwt_extended import jwt_required, get_current_user
import uuid

comments_bp = Blueprint("comments", __name__, url_prefix="/api/comments")

@comments_bp.route("/create/<event_id>", methods=["POST"])
@jwt_required()
def create_comment(event_id):
    user = get_current_user()
    event_id = uuid.UUID(event_id)

    event = Event.query.filter_by(event_id=event_id)

    if event is None:
        return {
            "message": "Event doesn't exist"
        }, 400
    
    comment_data = request.get_json()
    required_keys = {"content"}
    
    if not comment_data or not required_keys.issubset(comment_data.keys()):
        return jsonify({"message": "Bad request"}), 400
    
    new_comment = Comment(user_id=user.user_id, event_id=event_id, content=comment_data["content"])

    db.session.add(new_comment)
    db.session.commit()

    return {
        "message": "Comment created successfully"
    }, 200

@comments_bp.route("/reply/<parent_comment_id>", methods=["POST"])
@jwt_required()
def reply_to_comment(parent_comment_id):
    user = get_current_user()
    parent_comment_id = uuid.UUID(parent_comment_id)
    parent_comment = Comment.query.filter_by(comment_id=parent_comment_id).first()

    if parent_comment is None:
        return {
            "message": "Parent comment doesn't exist"
        }, 400
    
    comment_data = request.get_json()
    required_keys = {"content"}
    
    if not comment_data or not required_keys.issubset(comment_data.keys()):
        return jsonify({"message": "Bad request"}), 400
    
    new_comment = Comment(
        user_id=user.user_id,
        event_id=parent_comment.event_id,
        content=comment_data["content"],
        parent_comment_id=parent_comment_id
        )

    db.session.add(new_comment)
    db.session.commit()

    return {
        "message": "Comment created successfully"
    }, 200

@comments_bp.route("/delete/<comment_id>", methods=["DELETE"])
@jwt_required()
def delete_comment(comment_id):
    user = get_current_user()
    comment_id = uuid.UUID(comment_id)
    comment = Comment.query.filter_by(comment_id=comment_id).first()
    if comment is None:
        return {
            "message": "Comment doesn't exist"
        }, 400

    if user.user_id != comment.user_id:
        return {
            "message": "You can delete your own comments only"
        }, 401
        
    comment.soft_delete()
    db.session.commit()

    return {
        "message": "Comment deleted successfully"
    }, 200

@comments_bp.route("/edit/<comment_id>", methods=["PUT"])
@jwt_required()
def edit_comment(comment_id):
    user = get_current_user()
    comment_id = uuid.UUID(comment_id)
    comment = Comment.query.filter_by(comment_id=comment_id).first()

    if comment is None:
        return {
            "message": "Comment doesn't exist"
        }, 400

    if user.user_id != comment.user_id:
        return {
            "message": "You can edit your own comments only"
        }, 401
        
    data = request.get_json()
    new_content = data["new_content"]
    comment.content = new_content
    comment.edited = True
    db.session.commit()

    return {
        "message": "Comment edited successfully"
    }, 200

@comments_bp.route("/event/<event_id>", methods=["GET"])
@jwt_required()
def get_comments_list(event_id):

    comments = Comment.query.filter_by(event_id=event_id).order_by(Comment.created_at.asc()).all()

    if not comments:
        return jsonify({
            "message": "Empty comments list",
            "comments": []
        }), 200

    top_level_comments = [c for c in comments if c.parent_comment_id is None]
    comments_tree = [c.to_dict() for c in top_level_comments]

    return jsonify({
        "message": "Comments list",
        "comments": comments_tree
    }), 200