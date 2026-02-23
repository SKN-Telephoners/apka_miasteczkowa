from backend.extensions import db

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select, func
from models.review import Review
class Place(db.Model):
    __tablename__ = "place"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    address = db.Column(db.String(255), nullable=False)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    edited = db.Column(db.Boolean, default=False, nullable=False)
    reviews = db.relationship("Review",foreign_keys =["place_id"])
    tags = db.Column(db.ARRAY(db.String), default=[])
    
    @hybrid_property
    def num_of_reviews(self):
        return len(self.reviews)
    
    
    @num_of_reviews.expression
    def num_of_reviews(cls):
        return (
            select(func.count(Review.id)).where(Review.place_id == cls.id, Review.is_deleted == False).label("num_of_reviews")
        )
        
    @hybrid_property
    def average_rating(self):
        if not self.reviews:
            return None
        return sum(r.rating for r in self.reviews) / len(self.reviews)
    @average_rating.expression
    def average_rating(cls):
        return (
            select(func.avg(Review.rating)).where(Review.place_id == cls.id, Review.is_deleted == False).label("average_rating")
        )
    def soft_delete(self):
        self.deleted = True
        self.edited=   True
        self.name = ""
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "address": self.address,
            "num_of_reviews": self.num_of_reviews,
            "average_rating": self.average_rating
        }