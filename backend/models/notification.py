from backend.extensions import db
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime, timezone
import enum

class NotificationTag(enum.Enum):
    event_new_invite = 'event-new-invite'
    event_new_participant = 'event-new-participant'
    event_new_comment = "event-new-comment"

    invite_created = 'invite-created'
    invite_status_update = 'invite-status-update'

    joined_event_changed = 'joined-event-changed'

    friend_request_created = 'friend-request-created'
    friend_request_accepted = 'friend-request-accepted'
    friend_new_public_event= 'friend-new-public-event'
    friend_new_private_event = 'friend-new-private-event'

    comment_reply_created = 'comment-reply-created'
    other = 'other'


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