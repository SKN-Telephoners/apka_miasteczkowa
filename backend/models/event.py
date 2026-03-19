from backend.extensions import db
from sqlalchemy import CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

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
    comment_count = db.Column(db.Int, default=0, nullable = False)
    participant_count = db.Column(db.Int, default=0, nullable = False)
    is_private = db.Column(db.Boolean, default = False, nullable = False)

    __table_args__ = (
        CheckConstraint('date_and_time > CURRENT_TIMESTAMP', name='check_event_date_future'),
    )

    creator = db.relationship("User", foreign_keys=[creator_id])