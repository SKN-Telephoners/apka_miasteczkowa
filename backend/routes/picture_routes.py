from flask import Blueprint, request, current_app, jsonify
from backend.extensions import limiter
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required, get_current_user
import cloudinary.uploader

pictures_bp = Blueprint("pictures", __name__, url_prefix="/api/pictures")

@pictures_bp.route("/upload", methods=["POST"])
@jwt_required()
@limiter.limit("600 per minute")
def upload_file():
    if 'file' not in request.files:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="No file provided")

    user_id = get_current_user()
    file = request.files['file']
    
    # Get manual tags from the request body
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

        picture_url = response.get('eager')[0].get('secure_url') if response.get('eager') else response.get('secure_url')
        picture_id = response.get('public_id') or response.get('cloud_id')

        current_app.logger.info(f"INFO: /upload_file, success in uploading and tagging file for user: {user_id.user_id}")
        return make_api_response(ResponseTypes.CREATED, data={
            "picture_url": picture_url,
            "cloud_id": picture_id,
            "public_id": response.get('public_id'),
            "tags": response.get('tags', [])
        }, message="Picture uploaded and tagged successfully") # Returns the tags as a Python list

    except Exception as e:
        current_app.logger.error(f"ERROR: /upload_file, DB exception occured: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@pictures_bp.route("/upload-batch", methods=["POST"])
@jwt_required()
@limiter.limit("100 per minute")
def upload_multiple_files():
    if 'files' not in request.files:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="No files provided")

    files = request.files.getlist('files')
    user_id = get_current_user()
    
    if len(files) == 0:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="File list is empty")

    if len(files) > 5:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Maximum 5 pictures allowed per upload")

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

            picture_url = response.get('eager')[0].get('secure_url') if response.get('eager') else response.get('secure_url')
            picture_id = response.get('public_id') or response.get('cloud_id')
            
            uploaded_data.append({
                "picture_url": picture_url,
                "cloud_id": picture_id,
                "public_id": response.get('public_id')
            })

        except Exception as e:
            current_app.logger.error(f"ERROR: /upload_multiple_files, Cloudinary upload error for {file.filename}: {e}")
            errors.append({"filename": file.filename, "error": str(e)})

    # If all uploads failed
    if not uploaded_data and errors:
        current_app.logger.error(f"ERROR: /upload_multiple_files, Cloudinary upload error for all files: {e}")
        return make_api_response(ResponseTypes.SERVER_ERROR, message="Failed to upload pictures", data={"errors": errors})

    # Return partial or full success
    message = "All pictures uploaded successfully" if not errors else "Some pictures failed to upload"
    
    current_app.logger.info(f"INFO: /upload_multiple_files, success in uploading files for user: {user_id.user_id}")
    return make_api_response(ResponseTypes.CREATED, data={
        "pictures": uploaded_data,
        "errors": errors 
    }, message=message)