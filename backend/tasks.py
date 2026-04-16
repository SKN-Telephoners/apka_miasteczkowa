from celery import shared_task
from flask_mail import Message
from backend.extensions import mail, db
from backend.models.notification import Notification, NotificationTag
from flask import current_app

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