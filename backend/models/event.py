from backend.extensions import db
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy.orm import validates


class InviteRequestStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"

class Event(db.Model):
    __tablename__ = "Event"
    
    event_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    event_name = db.Column(db.String(32), nullable=False)
    description = db.Column(db.String(1000))
    date_and_time = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    location = db.Column(db.String(32), nullable=False)
    creator_id = db.Column(UUID(as_uuid=True), db.ForeignKey("User.user_id", ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    is_edited = db.Column(db.Boolean, default=False)
    comment_count = db.Column(db.Integer, default=0, nullable = False)
    participant_count = db.Column(db.Integer, default=0, nullable = False)
    is_private = db.Column(db.Boolean, default = False, nullable = False)

    __table_args__ = (
        CheckConstraint('comment_count >= 0', name='check_comment_count_positive'),
        CheckConstraint('participant_count >= 0', name='check_participant_count_positive'),
    )

    creator = db.relationship("User", foreign_keys=[creator_id])

    @validates('date_and_time')
    def validate_date(self, key, date_and_time):
        if date_and_time:
            if date_and_time.tzinfo is None:
                date_and_time = date_and_time.replace(tzinfo=timezone.utc)

            if date_and_time <= datetime.now(timezone.utc):
                raise ValueError("Data wydarzenia musi być w przyszłości.")
            
        return date_and_time

class Event_participants(db.Model):
    __tablename__ = "Event_participants"

    event_participants_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Event.event_id", ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("User.user_id", ondelete='CASCADE'), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'event_id', name='unique_event_participants'),
    )

    event = db.relationship("Event", foreign_keys=[event_id])
    user = db.relationship("User", foreign_keys=[user_id])
    
class Event_visibility(db.Model):
    __tablename__ = "Private_events_shared"

    private_shared_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Event.event_id", ondelete='CASCADE'), nullable=False, index=True)    
    sharing = db.Column(UUID(as_uuid=True), db.ForeignKey("User.user_id", ondelete='CASCADE'), nullable=False, index=True)
    shared_with = db.Column(UUID(as_uuid=True), db.ForeignKey("User.user_id", ondelete='CASCADE'), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint('sharing', 'shared_with', 'event_id', name='unique_private_events_shared'),
        CheckConstraint('sharing <> shared_with', name='cannot_share_with_oneself'),
    )

    event = db.relationship("Event", foreign_keys=[event_id])
    user_sharing = db.relationship("User", foreign_keys=[sharing])
    user_shared_with = db.relationship("User", foreign_keys=[shared_with])

class Invites(db.Model):
    __tablename__ = "Invites"

    invite_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Event.event_id", ondelete='CASCADE'), nullable=False, index=True)
    inviter_id = db.Column(UUID(as_uuid=True), db.ForeignKey("User.user_id", ondelete='CASCADE'), nullable=False, index=True)
    invited_id = db.Column(UUID(as_uuid=True), db.ForeignKey("User.user_id", ondelete='CASCADE'), nullable=False, index=True)
    status = db.Column(db.Enum(InviteRequestStatus), default=InviteRequestStatus.pending, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint('inviter_id', 'invited_id', 'event_id', name='unique_event_invite'),
        CheckConstraint('invited_id <> inviter_id', name='cannot_invite_oneself'),
    )

    event = db.relationship("Event", foreign_keys=[event_id])
    inviter = db.relationship("User", foreign_keys=[inviter_id])
    invited = db.relationship("User", foreign_keys=[invited_id])

class Pictures(db.Model):
    __tablename__ = "Event_Pictures"

    event_picture_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    event_picture_link = db.Column(db.String(64), nullable=False, unique=True)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Event.event_id", ondelete='CASCADE'), nullable=False, index=True)

    event = db.relationship("Event", foreign_keys=[event_id])