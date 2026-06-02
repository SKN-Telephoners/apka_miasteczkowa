from flask import Blueprint, request, current_app, jsonify
from backend.extensions import limiter
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required, get_current_user
from backend.constants import Constants
from backend.picture_helpers import validate_and_process_image, upload_to_s3
import cloudinary.uploader
import magic
import os

pictures_bp = Blueprint("pictures", __name__, url_prefix="/api/pictures")

'''
Input: Form-Data { "file": <File_Binary>, "tags": <str>, "type": <str: "profile"/"event"> }
Action: Validates, compresses, and uploads a single image to S3.
Data sent to the frontend: {"picture_url": <str>, "cloud_id": <str>, "public_id": <str>, "tags": [<str>]}
Output: 201 Created
'''
@pictures_bp.route("/upload", methods=["POST"])
@jwt_required()
@limiter.limit("600 per minute")
def upload_file():
    if 'file' not in request.files:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="No file provided")

    user_id = get_current_user()
    file = request.files['file']
    #frontend needs to send us type (event/profile) of a picture or do this in tags
    image_type = request.form.get('type', 'event') 
    
    # Get manual tags from the request body
    # We expect a comma-separated string from the frontend, e.g., "sunset, vacation, 2024"
    manual_tags = request.form.get('tags', '') 

    processed_file, error = validate_and_process_image(file, image_type)
    if error:
        current_app.logger.warning(f"WARNING: /upload_file, error: {error}")
        return make_api_response(ResponseTypes.BAD_REQUEST, message=error)

    if image_type == "profile":
        folder = "profiles"
    else:
        folder = "events"

    s3_key = upload_to_s3(processed_file, folder)

    if not s3_key:
        current_app.logger.error(f"ERROR: /upload_file, picture upload to s3 failed")
        return make_api_response(ResponseTypes.SERVER_ERROR, message="Upload to S3 failed")

    full_url = f"{current_app.config['S3_LOCATION']}{s3_key}"

    return make_api_response(ResponseTypes.CREATED, data={
        "picture_url": full_url,
        "cloud_id": s3_key
    })

'''
Input: Form-Data { "files": [<File_Binary>, ...], "tags": <str> } (Supports up to 5 files simultaneously).
Action: It iterates through the file list, uploading each to Cloudinary. It tracks successes and failures individually for each file
Data sent to the frontend: {
"pictures": [{
    "picture_url": <str>, 
    "cloud_id": <str>, 
    "public_id": <str>}],
"errors": [{"filename": <str>, "error": <str>}], 
"message": <str>}
Output: 201 Created (or 400/500 on error)
'''
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

        processed_file, error = validate_and_process_image(file, "event")
        if error:
            errors.append({"filename": file.filename, "error": error})
            continue

        s3_key = upload_to_s3(processed_file, "events")
        if s3_key:
            uploaded_data.append({
                "picture_url": f"{current_app.config['S3_LOCATION']}{s3_key}",
                "cloud_id": s3_key,
                "public_id": s3_key
            })
        else:
            errors.append({"filename": file.filename, "error": "S3 Upload failed"})

    # If all uploads failed
    if not uploaded_data and errors:
        current_app.logger.error(f"ERROR: /upload_multiple_files, s3 upload error for all files: {errors}")
        return make_api_response(ResponseTypes.SERVER_ERROR, message="Failed to upload pictures", data={"errors": errors})

    # Return partial or full success
    message = "All pictures uploaded successfully" if not errors else "Some pictures failed to upload"
    
    current_app.logger.info(f"INFO: /upload_multiple_files, success in uploading files for user: {user_id.user_id}")
    return make_api_response(ResponseTypes.CREATED, data={
        "pictures": uploaded_data,
        "errors": errors 
    }, message=message)