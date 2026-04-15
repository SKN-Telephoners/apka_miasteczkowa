from signals import friend_request_created
from backend.models import NotificationType
from backend.tasks import create_notification_task

@friend_request_created.connect
def handle_friend_request_notification(sender, **kwargs):
    from_user = kwargs.get('from_user')
    to_user = kwargs.get('to_user')
    request_id = kwargs.get('request_id')

    payload = {
        "friend_request_id": str(request_id),
        "sender_id": str(from_user.user_id),
        "sender_name": from_user.username,
        "message": f"{from_user.username} sent you a friend request."
    }

    create_notification_task.delay(
        user_id = str(to_user.user_id),
        notification_type_value = NotificationType.friend_request_incoming.value,
        payload = payload
    )