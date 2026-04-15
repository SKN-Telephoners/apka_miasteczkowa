from blinker import Namespace

app_signals = Namespace()

friend_request_created = app_signals.signal('friend-request-created')
event_invite_sent = app_signals.signal('event-invite-sent')