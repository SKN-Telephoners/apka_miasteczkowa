from flask import Blueprint, request, current_app, jsonify
from backend.models import Event, Comment
from backend.extensions import db, limiter
from backend.constants import Constants
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required, get_current_user
from backend.helpers import validate_uuid, sanitize_input
from sqlalchemy.exc import SQLAlchemyError

import cloudinary

images_bp = Blueprint("images", __name__, url_prefix="/api/images")

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

@images_bp.route("/upload-batch", methods=["POST"])
@jwt_required()
@limiter.limit("100 per minute")
def upload_multiple_files():
    if 'files' not in request.files:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="No files provided")

    files = request.files.getlist('files')
    
    if len(files) == 0:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="File list is empty")

    if len(files) > 5:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Maximum 5 images allowed per upload")

    manual_tags = request.form.get('tags', '') 
    
    uploaded_data = []
    errors = []

    for file in files:
        if file.filename == '':
            continue

        try:
            response = cloudinary.uploader.upload(
                file,
                upload_preset="aplikacja_miasteczkowa",
                tags=manual_tags,
                unique_filename=True,
                overwrite=True,
                eager=[{"width": 500, "height": 500, "crop": "fill"}]
            )
            
            uploaded_data.append({
                "image_url": response.get('eager')[0].get('secure_url'),
                "public_id": response.get('public_id')
            })

        except Exception as e:
            current_app.logger.error(f"Cloudinary upload error for {file.filename}: {e}")
            errors.append({"filename": file.filename, "error": str(e)})

    # If all uploads failed
    if not uploaded_data and errors:
        return make_api_response(ResponseTypes.SERVER_ERROR, message="Failed to upload images", data={"errors": errors})

    # Return partial or full success
    message = "All images uploaded successfully" if not errors else "Some images failed to upload"
    
    return make_api_response(ResponseTypes.CREATED, data={
        "images": uploaded_data,
        "errors": errors 
    }, message=message)