from backend.extensions import db
from sqlalchemy import CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

class Event(db.Model):
    __tablename__ = "event"
    
    event_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = db.Column(db.String(32), nullable=False)
    description = db.Column(db.String(1000))
    date_and_time = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    location = db.Column(db.String(32), nullable=False)
    creator_id = db.Column(UUID(as_uuid=True), db.ForeignKey("app_user.user_id", ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint('date_and_time > CURRENT_TIMESTAMP', name='check_event_date_future'),
    )

    creator = db.relationship("User", foreign_keys=[creator_id])

class Invite(db.Model):
    __tablename__ = "event_invite"
    
    invite_id=db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    event_id=db.Column(UUID(as_uuid=True), db.ForeignKey("event.event_id", ondelete='CASCADE'), nullable=False, index=True)
    user_id=db.Column(UUID(as_uuid=True), db.ForeignKey("app_user.user_id", ondelete='CASCADE'), nullable=False, index=True)


    __table_args__ = (
        db.UniqueConstraint("event_id", "user_id", name="unique_event_invite"),
    )

    event = db.relationship("Event", foreign_keys=[event_id])
    user = db.relationship("User", foreign_keys=[user_id])