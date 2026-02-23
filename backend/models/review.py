from backend.extensions import db
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
class Review(db.Model):
    __tablename__ = "review"
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    place_id = db.Column(UUID(as_uuid=True), db.ForeignKey("event.event_id", ondelete='CASCADE'), nullable=False, index=True)
    author_id = db.Column(UUID(as_uuid=True), db.ForeignKey("app_user.user_id", ondelete='CASCADE'), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.String(1000))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    is_edited = db.Column(db.Boolean, default=False, nullable=False)

    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
        UniqueConstraint('place_id', 'author_id', name='unique_review_per_user_place'),
    )

    event = db.relationship("Event", foreign_keys=[place_id])
    reviewer = db.relationship("User", foreign_keys=[author_id])
    
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "place_id": str(self.place_id),
            "author_id": str(self.author_id),
            "rating": self.rating,
            "text": self.text,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_deleted": self.is_deleted,
            "is_edited": self.is_edited
        }
    