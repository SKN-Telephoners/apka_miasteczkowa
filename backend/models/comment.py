from backend.extensions import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

class Comment(db.Model):
    __tablename__ = 'comments'

    comment_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,  unique=True, nullable=False)
    parent_comment_id = db.Column(UUID(as_uuid=True), db.ForeignKey("comments.comment_id", ondelete='SET NULL'), default=None, nullable=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("app_user.user_id", ondelete='CASCADE'), nullable=False)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey("event.event_id", ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    content = db.Column(db.String(1000), nullable=False)
    edited = db.Column(db.Boolean, default=False)
    deleted = db.Column(db.Boolean, default=False)

    parent_comment = db.relationship('Comment', remote_side=[comment_id], backref='replies') #comment.replies - list of child comments
    user = db.relationship('User', foreign_keys=[user_id])
    event = db.relationship('Event', foreign_keys=[event_id])

    def __init__(self, user_id, event_id, content, parent_comment_id=None):
        self.user_id = user_id
        self.event_id = event_id
        self.content = content
        self.parent_comment_id = parent_comment_id
    
    def soft_delete(self):
        self.deleted = True
        self.content = ""
        self.edited = True

    def to_dict(self):
        return {
            "comment_id": str(self.comment_id),
            "user_id": str(self.user_id) if not self.deleted else None,
            "content": self.content if not self.deleted else "[deleted]",
            "deleted": self.deleted,
            "created_at": self.created_at.isoformat(),
            "parent_comment_id": (str(self.parent_comment_id) if self.parent_comment_id else None),
            "replies": [reply.to_dict() for reply in self.replies]
        }