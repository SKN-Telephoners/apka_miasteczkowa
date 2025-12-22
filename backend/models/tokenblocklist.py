from backend.extensions import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class TokenBlocklist(db.Model):
    __tablename__ = "token_blocklist"

    token_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    jti = db.Column(db.String(36), nullable=False, unique=True)
    token_type = db.Column(db.String(18), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("app_user.user_id", ondelete='CASCADE'), nullable=False, index=True)
    revoked_at = db.Column(db.DateTime(timezone=True))
    expires = db.Column(db.DateTime(timezone=True), nullable=False)

    user = db.relationship("User")