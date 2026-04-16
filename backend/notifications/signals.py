from blinker import Namespace

app_signals = Namespace()

"""Events"""
event_new_invite = app_signals.signal('event-new-invite')
event_new_participant = app_signals.signal('event-new-participant')
event_new_comment = app_signals.signal("event-new-comment")

"""Invites"""
invite_created = app_signals.signal('invite-created')
invite_status_update = app_signals.signal('invite-status-update')

"""Participation"""
joined_event_changed = app_signals.signal('joined-event-changed')

"""Friends"""
friend_request_created = app_signals.signal('friend-request-created')
friend_request_accepted = app_signals.signal('friend-request-accepted')
friend_new_public_event= app_signals.signal('friend-new-public-event')
friend_new_private_event = app_signals.signal('friend-new-private-event')

"""Comments"""
comment_reply_created = app_signals.signal('comment-reply-created')