from backend.extensions import db
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime, timezone
import enum

class NotificationTag(enum.Enum):
    friend_request_incoming = "friend_request_incoming"
    friend_request_accepted = "friend_request_accepted"
    event_invite = "event_invite"
    event_shared = "event_shared"
    event_joined = "event_joined"
    event_comment = "event_comment"
    event_invitation_by_other = "event_invitation_by_other"
    event_deleted = "event_deleted"
    other = "other"

class Notification(db.Model):
    __tablename__ = 'Notifications'

    notification_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("User.user_id", ondelete='CASCADE'), nullable=False, index=True)
    
    tag = db.Column(db.Enum(NotificationTag), nullable=False, default=NotificationTag.other)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    payload = db.Column(JSONB, nullable=False, default={})

    user = db.relationship("User", foreign_keys=[user_id])

    def __init__(self, user_id, tag, is_read, payload):
        self.user_id = user_id
        self.tag = tag
        self.is_read = is_read
        self.payload = payload