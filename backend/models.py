from backend.extensions import db, bcrypt
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

class User(db.Model):
    __tablename__ = "app_user"
    
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = db.Column(db.String(32), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(320), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    
    __table_args__ = (
        CheckConstraint(r"email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'", name="email_format"),
    )
    
    def __init__(self, username, password, email):
        self.username = username
        self.email = email # TODO! Add function that checks email using regex
        pass_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        self.password_hash = pass_hash
        
    def validate_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def update_password(self, password):
        pass_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        self.password_hash = pass_hash

    def __repr__(self):
        return f"User {self.username}"
    
class TokenBlocklist(db.Model):
    __tablename__ = "token_blocklist"

    token_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    jti = db.Column(db.String(36), nullable=False, unique=True)
    token_type = db.Column(db.String(18), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("app_user.user_id", ondelete='CASCADE'), nullable=False, index=True)
    revoked_at = db.Column(db.DateTime)
    expires = db.Column(db.DateTime, nullable=False)

    user = db.relationship("User")

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