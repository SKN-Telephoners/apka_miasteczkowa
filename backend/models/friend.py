from backend.extensions import db
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

class Friendship(db.Model):
    __tablename__ = 'friendships'

    friendship_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,  unique=True, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("app_user.user_id", ondelete='CASCADE'), nullable=False, index=True)
    friend_id = db.Column(UUID(as_uuid=True), db.ForeignKey("app_user.user_id", ondelete='CASCADE'), nullable=False, index=True)
    accepted_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint('user_id <> friend_id', name='user_cannot_befriend_self'),
        CheckConstraint('user_id < friend_id', name='enforce_user_order'),
        UniqueConstraint('user_id', 'friend_id', name='unique_friendship_pair'),
    )

    user = db.relationship("User", foreign_keys=[user_id])
    friend = db.relationship("User", foreign_keys=[friend_id])

class FriendRequest(db.Model):
    __tablename__ = 'friend_requests'

    request_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,  unique=True, nullable=False)
    sender_id = db.Column(UUID(as_uuid=True), db.ForeignKey("app_user.user_id", ondelete='CASCADE'), nullable=False, index=True)
    receiver_id = db.Column(UUID(as_uuid=True), db.ForeignKey("app_user.user_id", ondelete='CASCADE'), nullable=False, index=True)
    requested_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.CheckConstraint('sender_id <> receiver_id', name='sender_not_receiver'),
        db.UniqueConstraint('sender_id', 'receiver_id', name='unique_request_pair'),
    )

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])