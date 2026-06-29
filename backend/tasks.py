from celery import shared_task
from flask_mail import Message
from backend.extensions import mail, db
from backend.models.notification import Notification, NotificationTag
from backend.models.event import Pictures
from backend.models.user import User
from backend.constants import Constants
from backend.picture_helpers import get_r2_client
from backend.helpers import invalidate_event_cache
from flask import current_app
import boto3



'''
Input: subject: <str>, recipient: <str>, body: <str>
Action: Sends an email via the configured SMTP server in the background.
Output: None
'''
@shared_task(ignore_result=True)
def send_email_async(subject, recipient, body):
    try:
        msg = Message(
            subject=subject,
            recipients=[recipient],
            body=body
        )
        mail.send(msg)
        current_app.logger.error(f"Async email sent to: {recipient}")
    except Exception as e:
        current_app.logger.error(f"Failed to sent async email: {e}")
        

'''
Input: user_id: <uuid>, notification_tag_value: <str>, payload: <JSONB/Dict>
Action: Creates a database record in the Notifications table asynchronously.
Output: None
'''
@shared_task
def create_notification_task(user_id, notification_tag_value, payload):
    notification_tag = NotificationTag(notification_tag_value)
    
    notification = Notification(
        user_id=user_id,
        tag=notification_tag,
        payload=payload
    )
    
    db.session.add(notification)
    db.session.commit()

'''
Input: image_key: <str>
Action: Downloads the image from R2, sends it to AWS Rekognition for safety analysis, and updates the event picture status in the database.
Output: None
'''
@shared_task(ignore_result=True)
def verify_event_image_task(image_key):
    r2 = get_r2_client()
    try:
        r2_obj = r2.get_object(Bucket=current_app.config["BUCKET_EVENTS"], Key=image_key)
        image_bytes = r2_obj['Body'].read()

        rekognition = boto3.client(
            'rekognition',
            aws_access_key_id=current_app.config["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=current_app.config["AWS_SECRET_ACCESS_KEY"],
            region_name=current_app.config["AWS_REGION"]
        )
        
        response = rekognition.detect_moderation_labels(
            Image={'Bytes': image_bytes},
            MinConfidence=Constants.MIN_CONFIDENCE_REKOGITION
        )

        picture = Pictures.query.filter_by(cloud_id=image_key).first()
        if not picture:
            return

        if not response['ModerationLabels']:
            picture.image_status = "approved"
        else:
            picture.image_status = "rejected"
            current_app.logger.warning(f"Event picture {image_key} rejected: {response['ModerationLabels']}")
            delete_from_r2_task.delay(image_key, "event") #automatic deletion
        
        db.session.commit()
        invalidate_event_cache(str(picture.event_id))

    except Exception as e:
        current_app.logger.error(f"Async Event Picture Verification Error: {e}")
        db.session.rollback()

'''
Input: user_id: <uuid/str>, image_key: <str>
Action: Downloads the image from R2, sends it to AWS Rekognition for safety analysis, and updates the user profile picture status in the database.
Output: None
'''
@shared_task(ignore_result=True)
def verify_profile_image_task(user_id, image_key):
    r2 = get_r2_client()
    try:
        r2_obj = r2.get_object(Bucket=current_app.config["BUCKET_PROFILES"], Key=image_key)
        image_bytes = r2_obj['Body'].read()

        rekognition = boto3.client(
            'rekognition',
            aws_access_key_id=current_app.config["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=current_app.config["AWS_SECRET_ACCESS_KEY"],
            region_name=current_app.config["AWS_REGION"]
        )
        
        response = rekognition.detect_moderation_labels(
            Image={'Bytes': image_bytes},
            MinConfidence=Constants.MIN_CONFIDENCE_REKOGITION
        )

        user = db.session.get(User, user_id)
        if not user:
            return

        if not response['ModerationLabels']:
            user.image_status = "approved"
        else:
            user.image_status = "rejected"
            current_app.logger.warning(f"Profile picture of user {user_id} rejected: {response['ModerationLabels']}")
            delete_from_r2_task.delay(image_key, "profile") #automatic deletion
        
        db.session.commit()
        
    except Exception as e:
        current_app.logger.error(f"Async Profile Picture Verification Error: {e}")
        db.session.rollback()

'''
Input: image_key: <str>, image_type: <str> ("profile" or "event")
Action: Connects to Cloudflare R2 and deletes the object from the specified bucket in the background.
Output: None
'''
@shared_task(ignore_result=True)
def delete_from_r2_task(image_key, image_type="event"):

    r2 = get_r2_client()
    
    bucket_name = (
        current_app.config["BUCKET_PROFILES"] 
        if image_type == "profile" 
        else current_app.config["BUCKET_EVENTS"]
    )
    
    try:
        r2.delete_object(Bucket=bucket_name, Key=image_key)
    except Exception as e:
        current_app.logger.error(f"R2 Delete Error: {e}")