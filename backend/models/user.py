from backend.extensions import db, bcrypt
from sqlalchemy import CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from datetime import datetime, timezone

class User(db.Model):
    __tablename__ = "User"
    
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = db.Column(db.String(32), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(320), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    academy = db.Column(db.String(10), nullable=True)
    course = db.Column(db.String(100), nullable=True)
    year = db.Column(db.SmallInteger, nullable=True)
    academic_circles = db.Column(ARRAY(db.String(100)), nullable=True)
    is_confirmed = db.Column(db.Boolean, default=False)
    password_changed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    confirmed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    description = db.Column(db.String(320))

    is_deleted = db.Column(db.Boolean, default=False)
    pending_email = db.Column(db.String(320), nullable=True)
    tokens_revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)

    profile_pictures = db.relationship("ProfilePicture", back_populates="user", cascade="all, delete-orphan")
    blocks_initiated = db.relationship(
        "BlockList",
        foreign_keys="BlockList.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    blocks_received = db.relationship(
        "BlockList",
        foreign_keys="BlockList.blocked_user_id",
        back_populates="blocked_user",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(r"email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'", name="email_format"),
        CheckConstraint("year >= 1 AND year <= 6", name="valid_year")
    )
    
    def __init__(self, username, password, email, is_confirmed=False):
        self.username = username
        self.email = email # TODO! Add function that checks email using regex
        pass_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        self.password_hash = pass_hash
        self.is_confirmed = is_confirmed
        
    def validate_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def update_password(self, password):
        pass_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        self.password_hash = pass_hash

    def __repr__(self):
        return f"User {self.username}"
    
    def to_dict(self):
        #pętla rozbijająca długiego stringa z kołami naukowymi wymienionymi po przecinku na listę
        #pętla rozbijająca długiego stringa z kierunkami wymienionymi po przecinku na listę

        return {
            #TODO
            #"academic_circles": ["circle1", "circle2"]
        }

    
class ProfilePicture(db.Model):
    __tablename__="Profile_pictures"
    
    profile_picture_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("User.user_id", ondelete='CASCADE'), nullable=False, index=True)
    picture_link = db.Column(db.String(1000))

    user = db.relationship("User", back_populates="profile_pictures", foreign_keys=[user_id])
    
class BlockList(db.Model):
    __tablename__="Block_list"
    
    block_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("User.user_id", ondelete='CASCADE'), nullable=False, index=True)
    blocked_user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("User.user_id", ondelete='CASCADE'), nullable=False, index=True)

    user = db.relationship("User", foreign_keys=[user_id], back_populates="blocks_initiated")
    blocked_user = db.relationship("User", foreign_keys=[blocked_user_id], back_populates="blocks_received")
    
    
    