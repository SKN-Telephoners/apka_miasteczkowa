from backend.extensions import db, bcrypt
from sqlalchemy import CheckConstraint
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
    is_confirmed = db.Column(db.Boolean, default=False)

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