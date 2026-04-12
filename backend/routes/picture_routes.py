from flask import Blueprint, request, current_app, jsonify
from backend.extensions import limiter
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required
import cloudinary.uploader
import cloudinary

pictures_bp = Blueprint("pictures", __name__, url_prefix="/api/pictures")


def _is_cloudinary_configured() -> bool:
    cfg = cloudinary.config()
    return bool(cfg.cloud_name and cfg.api_key and cfg.api_secret)


def _extract_public_id(upload_response: dict) -> str | None:
    return upload_response.get("public_id") or upload_response.get("cloud_id")


def _extract_secure_url(upload_response: dict) -> str | None:
    eager = upload_response.get("eager") or []
    if eager and isinstance(eager[0], dict):
        return eager[0].get("secure_url")

    return upload_response.get("secure_url")

@pictures_bp.route("/upload", methods=["POST"])
@jwt_required()
@limiter.limit("600 per minute")
def upload_file():
    if not _is_cloudinary_configured():
        return make_api_response(
            ResponseTypes.SERVER_ERROR,
            message="Cloudinary is not configured on backend. Set CLOUDINARY_URL or CLOUDINARY_CLOUD_NAME/CLOUDINARY_API_KEY/CLOUDINARY_API_SECRET.",
        )

    file = request.files.get('file')
    if file is None:
        files = request.files.getlist('files')
        if len(files) == 0:
            files = request.files.getlist('files[]')
        file = files[0] if len(files) > 0 else None

    if file is None:
        current_app.logger.warning(f"upload: no multipart file found; keys={list(request.files.keys())}")
        return make_api_response(ResponseTypes.BAD_REQUEST, message="No file provided")
    
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

        public_id = _extract_public_id(response)
        picture_url = _extract_secure_url(response)

        return make_api_response(ResponseTypes.CREATED, data={
            "picture_url": picture_url,
            "cloud_id": public_id,
            "public_id": public_id,
            "clout_id": public_id,
            "tags": response.get('tags', [])
        }, message="Picture uploaded and tagged successfully") # Returns the tags as a Python list

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@pictures_bp.route("/upload-batch", methods=["POST"])
@jwt_required()
@limiter.limit("100 per minute")
def upload_multiple_files():
    if not _is_cloudinary_configured():
        return make_api_response(
            ResponseTypes.SERVER_ERROR,
            message="Cloudinary is not configured on backend. Set CLOUDINARY_URL or CLOUDINARY_CLOUD_NAME/CLOUDINARY_API_KEY/CLOUDINARY_API_SECRET.",
        )

    files = request.files.getlist('files')
    if len(files) == 0:
        files = request.files.getlist('files[]')
    if len(files) == 0 and 'file' in request.files:
        files = [request.files['file']]

    if len(files) == 0:
        current_app.logger.warning(f"upload-batch: no multipart files found; keys={list(request.files.keys())}")
        return make_api_response(ResponseTypes.BAD_REQUEST, message="No files provided")
    
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

            public_id = _extract_public_id(response)
            
            uploaded_data.append({
                "picture_url": _extract_secure_url(response),
                "cloud_id": public_id,
                "public_id": public_id
            })

        except Exception as e:
            current_app.logger.error(f"Cloudinary upload error for {file.filename}: {e}")
            errors.append({"filename": file.filename, "error": str(e)})

    # If all uploads failed
    if not uploaded_data and errors:
        return make_api_response(ResponseTypes.SERVER_ERROR, message="Failed to upload pictures", data={"errors": errors})

    # Return partial or full success
    message = "All pictures uploaded successfully" if not errors else "Some pictures failed to upload"
    
    return make_api_response(ResponseTypes.CREATED, data={
        "pictures": uploaded_data,
        "errors": errors 
    }, message=message)