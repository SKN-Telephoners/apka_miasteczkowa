from celery import shared_task
from flask_mail import Message
from backend.extensions import mail
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