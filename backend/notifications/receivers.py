from .signals import *
from backend.models.notification import NotificationTag
from backend.tasks import create_notification_task

"""Events"""
@event_new_participant.connect
def handle_event_new_participant(sender, **kwargs):
    participant_id = kwargs.get('participant_id')
    participant_username = kwargs.get('participant_username')
    creator_id = kwargs.get('creator_id')
    event_id = kwargs.get('event_id')
    event_name = kwargs.get('event_name')

    payload = {
        "participant_id": str(participant_id),
        "participant_name": participant_username,
        "event_id": str(event_id),
        "event_name": event_name,
    }

    create_notification_task.delay(
        user_id=str(creator_id),
        notification_tag_value=NotificationTag.event_new_participant.value,
        payload=payload
    )

@event_new_comment.connect
def handle_event_new_comment(sender, **kwargs):
    commenter_id = kwargs.get('commenter_id')
    commenter_name = kwargs.get('commenter_name')
    creator_id = kwargs.get('creator_id')
    event_id = kwargs.get('event_id')
    event_name = kwargs.get('event_name')

    if str(commenter_id) == str(creator_id):
        return

    payload = {
        "commenter_id": str(commenter_id),
        "commenter_name": commenter_name,
        "event_id": str(event_id),
        "event_name": event_name,
    }

    create_notification_task.delay(
        user_id=str(creator_id),
        notification_tag_value=NotificationTag.event_new_comment.value,
        payload=payload
    )

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
    }

    create_notification_task.delay(
        user_id = str(to_user_id),
        notification_tag_value = NotificationTag.invite_created.value,
        payload = payload
    )

@invite_status_update.connect
def handle_invite_status_update(sender, **kwargs):
    invite_id = kwargs.get('invite_id')
    inviter_id = kwargs.get('inviter_id')
    invitee_id = kwargs.get('invitee_id')
    invitee_username = kwargs.get('invitee_username')
    event_id = kwargs.get('event_id')
    event_name = kwargs.get('event_name')
    status = kwargs.get('status') # "accepted" or "declined"

    payload = {
        "invite_id": str(invite_id),
        "invitee_id": str(invitee_id),
        "invitee_name": invitee_username,
        "event_id": str(event_id),
        "event_name": event_name,
        "status": status,
    }

    create_notification_task.delay(
        user_id=str(inviter_id),
        notification_tag_value=NotificationTag.invite_status_update.value,
        payload=payload
    )

"""Participation"""
@joined_event_updated.connect
def handle_joined_event_updated(sender, **kwargs):
    event_id = kwargs.get('event_id')
    event_name = kwargs.get('event_name')
    participant_ids = kwargs.get('participant_ids', []) #list of user IDs

    payload = {
        "event_id": str(event_id),
        "event_name": event_name,
    }

    #loop through all participants and queue a notification for each
    for user_id in participant_ids:
        create_notification_task.delay(
            user_id=str(user_id),
            notification_tag_value=NotificationTag.joined_event_updated.value,
            payload=payload
        )

@joined_event_deleted.connect
def handle_joined_event_deleted(sender, **kwargs):
    event_name = kwargs.get('event_name')
    creator_username = kwargs.get('creator_username')
    participant_ids = kwargs.get('participant_ids', [])

    payload = {
        "event_name": event_name,
        "creator_name": creator_username,
    }

    #loop through all participants and queue a notification for each
    for user_id in participant_ids:
        create_notification_task.delay(
            user_id=str(user_id),
            notification_tag_value=NotificationTag.joined_event_deleted.value,
            payload=payload
        )

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
    }

    create_notification_task.delay(
        user_id = str(to_user_id),
        notification_tag_value = NotificationTag.friend_request_created.value, 
        payload = payload
    )

@friend_request_accepted.connect
def handle_friend_request_accepted(sender, **kwargs):
    accepter_id = kwargs.get('accepter_id')
    accepter_name = kwargs.get('accepter_name')
    original_sender_id = kwargs.get('sender_id')

    payload = {
        "friend_id": str(accepter_id),
        "friend_name": accepter_name,
    }

    create_notification_task.delay(
        user_id=str(original_sender_id),
        notification_tag_value=NotificationTag.friend_request_accepted.value,
        payload=payload
    )

@friend_new_public_event.connect
def handle_friend_new_public_event(sender, **kwargs):
    creator_id = kwargs.get('creator_id')
    creator_name = kwargs.get('creator_name')
    event_id = kwargs.get('event_id')
    event_name = kwargs.get('event_name')
    friend_ids = kwargs.get('friend_ids', [])

    payload = {
        "creator_id": str(creator_id),
        "creator_name": creator_name,
        "event_id": str(event_id),
        "event_name": event_name,
    }

    for f_id in friend_ids:
        create_notification_task.delay(
            user_id=str(f_id),
            notification_tag_value=NotificationTag.friend_new_public_event.value,
            payload=payload
        )

@friend_new_private_event.connect
def handle_friend_new_private_event(sender, **kwargs):
    creator_id = kwargs.get('creator_id')
    creator_name = kwargs.get('creator_name')
    event_id = kwargs.get('event_id')
    event_name = kwargs.get('event_name')
    shared_with_ids = kwargs.get('shared_with_ids', [])

    payload = {
        "creator_id": str(creator_id),
        "creator_name": creator_name,
        "event_id": str(event_id),
        "event_name": event_name,
    }

    for f_id in shared_with_ids:
        create_notification_task.delay(
            user_id=str(f_id),
            notification_tag_value=NotificationTag.friend_new_private_event.value,
            payload=payload
        )

"""Comments"""
@comment_reply_created.connect
def handle_comment_reply_created(sender, **kwargs):
    replier_id = kwargs.get('replier_id')
    replier_name = kwargs.get('replier_name')
    parent_author_id = kwargs.get('parent_author_id')
    event_id = kwargs.get('event_id')
    event_name = kwargs.get('event_name')

    if str(replier_id) == str(parent_author_id):
        return

    payload = {
        "replier_id": str(replier_id),
        "replier_name": replier_name,
        "event_id": str(event_id),
        "event_name": event_name,
    }

    create_notification_task.delay(
        user_id=str(parent_author_id),
        notification_tag_value=NotificationTag.comment_reply_created.value,
        payload=payload
    )