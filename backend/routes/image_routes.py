from flask import Blueprint, request, current_app, jsonify
from backend.models import Event, Comment
from backend.extensions import db, limiter
from backend.constants import Constants
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required, get_current_user
from backend.helpers import validate_uuid, sanitize_input
from sqlalchemy.exc import SQLAlchemyError

import cloudinary

images_bp = Blueprint("images", __name__, url_prefix="/api/photos")

@images_bp.route("/upload", methods=["POST"])
@jwt_required()
@limiter.limit("600 per minute")
def upload_file():
    if 'file' not in request.files:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="No file provided")
        return jsonify({"status": "error", "message": "No file provided"}), 400

    file = request.files['file']
    
    # 2. Get manual tags from the request body
    # We expect a comma-separated string from the frontend, e.g., "sunset, vacation, 2024"
    manual_tags = request.form.get('tags', '') 

    try:
        response = cloudinary.uploader.upload(
            file,
            upload_preset="aplikacja_miasteczkowa",
            tags=manual_tags,  # Cloudinary accepts a list or a comma-separated string
            unique_filename=True,
            overwrite=True,
            eager=[{"width": 500, "height": 500, "crop": "fill"}]
        )

        return make_api_response(ResponseTypes.CREATED, data={
            "image_url": response.get('eager')[0].get('secure_url'),
            "public_id": response.get('public_id'),
            "tags": response.get('tags', [])
        }, message="Image uploaded and tagged successfully") # Returns the tags as a Python list

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500