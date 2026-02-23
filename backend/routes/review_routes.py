from flask import jsonify, Blueprint, request, current_app
from backend.models import Event
from backend.extensions import db, limiter
from backend.constants import Constants
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required, get_current_user
from backend.helpers import validate_uuid, sanitize_input
import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.exc import SQLAlchemyError
from backend.models import Review, User
main = Blueprint("reviews", __name__, url_prefix="/api/reviews")
local_tz = ZoneInfo("Europe/Warsaw")
@main.route("/get_reviews/<place_id>", methods=["GET"])
@jwt_required()
def get_reviews():
    user = get_current_user()
    try:
        place_id = uuid.UUID(place_id)
    except Exception:
        return jsonify({"message": "Invalid place ID format"}), 400
    reviews = Review.query.filter_by(place_id=place_id, is_deleted=False).all()
    if reviews is None:
        return {
            "message": "Place doesn't exist"
        }, 404
    reviews_data = []
    for review in reviews:  
        author = User.query.filter_by(user_id=review.author_id).first()
        reviews_data.append({
            "review_id": review.id,
            "author_username": author.username if author else "Unknown",
            "rating": review.rating,
            "text": review.text,
            "created_at": review.created_at.isoformat(),
            "updated_at": review.updated_at.isoformat()
        })
    return jsonify({
        "reviews": reviews_data
    }), 200


@main.route("/delete_review/<review_id>", methods=["DELETE"])
@jwt_required()
def delete_review(review_id):
    user = get_current_user()
    try:
        review_id = uuid.UUID(review_id)
    except Exception:
        return jsonify({"message": "Invalid review ID format"}), 400
    
    review = Review.query.filter_by(id=review_id).first()

    if review is None or review.is_deleted:
        return {
            "message": "Review doesn't exist"
        }, 404

    if user.user_id != review.author_id:
        return {
            "message": "You can delete your own reviews only"
        }, 403
    
    try:
        review.is_deleted = True
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({"message": "Internal server error"}), 500

    return jsonify ({
        "message": "Review deleted successfully"
    }), 200
@main.route("/create_review" , methods = ["POST"])
@jwt_required()
def create_review():
    user = get_current_user()
    author_id = user.user_id
    review_data = request.get_json()
    required_keys = ["place_id","rating" ,"text"]
    if not review_data or not required_keys.issubset(review_data.keys()):
        return jsonify({"message": "Bad request"}), 400
    place_id = review_data.get("place_id" ,"")
    rating = review_data.get("rating","")
    text = review_data.get("text","")
    
    if(rating > 5):
        return jsonify({"message" : "rating must include between 1 and 5"}) , 400
    
    if(len(text) > 1000):
        return jsonify({"message" : "your text is too long"}) , 400
    
    try:
        new_review = Review(
            place_id = place_id,
            author_id = author_id,
            rating = rating,
            text = text
        )
        db.session.add(new_review)
        db.session.commit()
            
    except Exception as e:  
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({"message": "Internal server error"}), 500
    return jsonify({
        "message": "Review created successfully",
        "review_id": new_review.id
    }), 200
@main.route("/edit_review/<review_id>", methods=["PUT"])
@jwt_required()
def edit_review(review_id):
    user = get_current_user()
    try:
        review_id = uuid.UUID(review_id)
    except Exception:
        return jsonify({"message": "Invalid review ID format"}), 400
    
    review = Review.query.filter_by(id=review_id).first()

    if review is None or review.is_deleted:
        return {
            "message": "Review doesn't exist"
        }, 404

    if user.user_id != review.author_id:
        return {
            "message": "You can edit your own reviews only"
        }, 403
    
    review_data = request.get_json()
    rating = review_data.get("rating")
    text = review_data.get("text")

    if rating is not None:
        if rating < 1 or rating > 5:
            return jsonify({"message": "Rating must be between 1 and 5"}), 400
        review.rating = rating

    if text is not None:
        if len(text) > 1000:
            return jsonify({"message": "Text is too long (max 1000 chars)"}), 400
        review.text = text

    review.is_edited = True

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({"message": "Internal server error"}), 500

    return jsonify ({
        "message": "Review edited successfully"
    }), 200