from .signals import *
from backend.models.notification import NotificationTag
from backend.tasks import create_notification_task

print("REVCEIVERS FILE LOADED")

"""Events"""
#event_new_invite = app_signals.signal('event-new-invite')
#event_new_participant = app_signals.signal('event-new-participant')
#event_new_comment = app_signals.signal("event-new-comment")

"""Invites"""
@invite_created.connect
def handle_invite_created_notification(sender, **kwargs):
    from_user_id = kwargs.get('from_user_id')
    from_user_username = kwargs.get('from_user_username')
    to_user_id = kwargs.get('to_user_id')
    invite_id = kwargs.get('invite_id')
    event_id = kwargs.get('event_id')
    event_name = kwargs.get('event_name')

    payload = {
        "invite_id": str(invite_id),
        "sender_id": str(from_user_id),
        "sender_name": from_user_username,
        "event_id": str(event_id),
        "event_name": event_name,
        "message": f"{from_user_username} invited you to an event {event_name}."
    }

    create_notification_task.delay(
        user_id = str(to_user_id),
        notification_tag_value = NotificationTag.invite_created.value,
        payload = payload
    )

#invite_status_update = app_signals.signal('invite-status-update')

"""Participation"""
#joined_event_changed = app_signals.signal('joined-event-changed')

"""Friends"""
@friend_request_created.connect
def handle_friend_request_notification(sender, **kwargs):
    from_user_id = kwargs.get('from_user_id')
    from_user_username = kwargs.get('from_user_username')
    to_user_id = kwargs.get('to_user_id')
    request_id = kwargs.get('request_id')

    payload = {
        "friend_request_id": str(request_id),
        "sender_id": str(from_user_id),
        "sender_name": from_user_username,
        "message": f"{from_user_username} sent you a friend request."
    }

    create_notification_task.delay(
        user_id = str(to_user_id),
        notification_tag_value = NotificationTag.friend_request_created.value, 
        payload = payload
    )

#friend_request_accepted = app_signals.signal('friend-request-accepted')
#friend_new_public_event= app_signals.signal('friend-new-public-event')
#friend_new_private_event = app_signals.signal('friend-new-private-event')

"""Comments"""
#comment_reply_created = app_signals.signal('comment-reply-created')




