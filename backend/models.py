from main import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from flask_bcrypt import bcrypt

class User(db.Model):
    __tablename__ = "app_user"
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = db.Column(db.String(32), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=False, unique=True)

    def __repr__(self):
        return f"User {self.username}"