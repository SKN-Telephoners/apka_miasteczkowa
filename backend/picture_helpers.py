import magic
import io
import uuid
from PIL import Image
from flask import current_app
from backend.constants import Constants
from app import s3


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

        if image_type == "profile":
            current_app.logger.info(f"INFO: validate_and_process_image, compressed a profile picture")
            target_size = (400, 400)
            quality = 70 
        else:
            current_app.logger.info(f"INFO: validate_and_process_image, compressed an event picture")
            target_size = (1920, 1080)
            quality = 85 

        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        current_app.logger.info(f"INFO: validate_and_process_image, picture saved successfully")
        output.seek(0)
        return output, None
    except Exception as e:
        current_app.logger.error(f"ERROR: validate_and_process_image, exception occured: {e}")
        return None, f"Error in file processing: {str(e)}"


'''
Input: file_data: <BytesIO>, folder: <str>
Action: Connects to AWS S3 using boto3, generates a unique filename with UUID, and uploads the binary stream.
Output: <str:s3_key> (the unique path to the file) or None on failure.
'''
def upload_to_s3(file_data, folder="events"):
    filename = f"{folder}/{uuid.uuid4().hex}.jpg"
    try:
        s3.upload_fileobj(
            file_data,
            current_app.config["AWS_S3_BUCKET_NAME"],
            filename,
            ExtraArgs={"ContentType": "image/jpeg"}
        )
        current_app.logger.info(f"INFO: upload_to_s3, succsessfully uploaded picture to s3: {filename}")
        return filename
    except Exception as e:
        current_app.logger.error(f"ERROR: upload_to_s3, exception occured: {e}")
        current_app.logger.error(f"S3 Upload Error: {e}")
        return None


'''
Input: file_key: <str>
Action: Deletes an object from the configured S3 bucket using its unique key.
Output: None
'''
def delete_from_s3(file_key):
    if not file_key: return
    try:
        s3.delete_object(Bucket=current_app.config["AWS_S3_BUCKET_NAME"], Key=file_key)
        current_app.logger.info(f"INFO: delete_from_s3, succsessfully deleted picture from s3")
    except Exception as e:
        current_app.logger.error(f"ERROR: delete_from_s3, exception occured: {e}")