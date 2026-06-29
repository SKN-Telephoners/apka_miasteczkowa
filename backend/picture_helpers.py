import boto3
import uuid
import io
from PIL import Image
from flask import current_app
import magic
from backend.constants import Constants

'''
Input: permission: <str> ("read" or "upload")
Action: Initializes boto3 client with defined keys based on required permissions
Output: boto3.client object
'''
def get_r2_client(permission="read"):
    if permission == "upload":
        access_key = current_app.config["CF_R2_ACCESS_KEY_ID_UPLOAD"]
        secret_key = current_app.config["CF_R2_SECRET_ACCESS_KEY_UPLOAD"]
    else:
        access_key = current_app.config["CF_R2_ACCESS_KEY_ID_READ"]
        secret_key = current_app.config["CF_R2_SECRET_ACCESS_KEY_READ"]

    return boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        endpoint_url=current_app.config["CF_R2_ENDPOINT_URL"],
        region_name="auto"
    )

'''
Input: file: <FileStorage>, image_type: <str> ("profile" or "event")
Action: Uses python-magic to verify the actual file signature (MIME type). Checks if the file size is within limits. 
        Converts the image to RGB, applies resizing (thumbnail) and compression (JPEG) using Pillow.
Output: tuple (<BytesIO:processed_data> or None, <str:error_message> or None)
'''
def validate_and_process_image(file, image_type="event"):
    
    header = file.read(2048)
    file.seek(0)
    mime = magic.from_buffer(header, mime=True)

    if mime not in Constants.ALLOWED_EXTENSIONS:
        current_app.logger.warning(f"WARNING: validate_and_process_image, someone tried to upload a file that is not a picture: {mime}")
        return None, f"Wrong file type: {mime}. Allowed: JPG, PNG, WEBP."

    file.seek(0, 2) 
    size = file.tell()
    file.seek(0) 

    if image_type == "profile":
        max_size = Constants.MAX_PROFILE_PIC_SIZE
    else:
        max_size = Constants.MAX_EVENT_PIC_SIZE

    if size > max_size:
        current_app.logger.warning(f"WARNING: validate_and_process_image, someone tried to upload a file that is too big: {size}")
        return None, f"File too big ({max_size // (1024 * 1024)}MB), max size is {max_size // (1024*1024)}MB."
    
    try:
        img = Image.open(file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Rozmiary zależne od typu
        if image_type == "profile":
            target_size = (400, 400)
            quality = 75
        else:
            target_size = (1920, 1080)
            quality = 85

        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        output.seek(0)
        return output, None
    except Exception as e:
        return None, str(e)

'''
Input: file_data: <BytesIO>, folder: <str>
Action: Connects to R2 Cloudflare using boto3, generates a unique filename with UUID, and uploads the binary stream.
Output: <str:s3_key> (the unique path to the file) or None on failure.
'''
def upload_to_r2(file_data, image_type="event"):
    s3 = get_r2_client(permission="upload")

    bucket_name = (
        current_app.config["BUCKET_PROFILES"] if image_type == "profile" else current_app.config["BUCKET_EVENTS"]
    )
    
    filename = f"{uuid.uuid4().hex}.jpg"
    
    try:
        s3.upload_fileobj(
            file_data,
            bucket_name,
            filename,
            ExtraArgs={"ContentType": "image/jpeg"}
        )
        return filename 
    except Exception as e:
        current_app.logger.error(f"R2 Upload Error: {e}")
        return None
