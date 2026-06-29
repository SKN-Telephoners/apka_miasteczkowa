from flask import Blueprint, request, current_app
from backend.models.event import Event, Event_visibility, Event_participants, Invites, InviteRequestStatus
from backend.models import Friendship
from backend.extensions import db, limiter
from backend.responses import ResponseTypes, make_api_response
from flask_jwt_extended import jwt_required, get_current_user
from backend.helpers import validate_uuid, sanitize_input, invalidate_event_cache
from zoneinfo import ZoneInfo
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, and_
from backend.notifications.signals import (
    invite_created, 
    event_new_participant, 
    invite_status_update
)

interaction_bp = Blueprint("interaction", __name__, url_prefix="/api/events")
local_tz = ZoneInfo("Europe/Warsaw")

'''
Input: URL Parameter <uuid:event_id>, Header { "Authorization": "Bearer <Access_Token>" }, JSON { "invited": <uuid> }
Action: Verifies the inviter and invited are friends. Checks privacy rules (only creators can invite for private events). Creates an invite record and triggers an async notification
Data sent to the frontend: {"message": "Invite created successfully"}
Output: 201 Created (or 404/400/403/409/500 on error)
'''
@interaction_bp.route("/invite/<event_id>", methods=["POST"])
@limiter.limit("100 per minute")
@jwt_required()
def invite_to_event(event_id):
    user = get_current_user()
    e_uuid = validate_uuid(event_id)
    u_uuid = validate_uuid(user.user_id)

    invite_data = request.get_json(silent=True)

    if not invite_data or "invited" not in invite_data:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Invited ID missing")

    i_uuid = validate_uuid(invite_data.get("invited"))

    if not e_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid Event ID")
    if not u_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid Inviter ID")
    if not i_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid Invited ID")
    
    if u_uuid == i_uuid:
        current_app.logger.warning(f"WARNING: /invite_to_event, user {user.user_id} tried to invite himself for an event")
        return make_api_response(ResponseTypes.BAD_REQUEST, message="You cannot invite yourself")
    
    event = db.session.get(Event, e_uuid)
    if event is None:
        current_app.logger.warning(f"WARNING: /invite_to_event, user {user.user_id} tried to send invite to a non existant event")
        return make_api_response(ResponseTypes.NOT_FOUND, message="This event does not exist")

    is_friend = db.session.query(Friendship).filter(
        or_(
            and_(Friendship.user_id == u_uuid, Friendship.friend_id == i_uuid),
            and_(Friendship.user_id == i_uuid, Friendship.friend_id == u_uuid)
        )
    ).first()

    if not is_friend: 
        current_app.logger.warning(f"WARNING: /invite_to_event, user {user.user_id} tried to invite a user that is not their friend")
        return make_api_response(ResponseTypes.FORBIDDEN, message="You can only invite your friends")
    
    if event.is_private:
        # na razie tylko autor ma możliwość zapraszania na swój event osoby, którym udostępnił do wyświetlania
        if event.creator_id != u_uuid:
            current_app.logger.warning(f"WARNING: /invite_to_event, user {user.user_id} tried to send invite for an event that is not his")
            return make_api_response(ResponseTypes.FORBIDDEN, message="Only creator of the private event can invite")
        
        has_visibility = db.session.query(Event_visibility).filter_by(event_id=e_uuid, shared_with=i_uuid).first()
        if not has_visibility:
            current_app.logger.warning(f"WARNING: /invite_to_event, user {user.user_id} tried to send invite to user that does not have priviledges to view this event")
            return make_api_response(ResponseTypes.FORBIDDEN, message=f"User does not have priviledges to view this event")

    is_already_participant = db.session.query(Event_participants).filter_by(event_id=e_uuid, user_id=i_uuid).first()
    if is_already_participant:
        return make_api_response(ResponseTypes.CONFLICT, message="User is already participating in this event")
        
    existing_invite = db.session.query(Invites).filter_by(event_id=e_uuid, inviter_id=u_uuid, invited_id=i_uuid).first()
    if existing_invite:
        current_app.logger.warning(f"WARNING: /invite_to_event, user {user.user_id} tried to send invite that already exists")
        return make_api_response(ResponseTypes.CONFLICT, message="Invite already sent")
        
    try:
        new_invite = Invites(
            event_id=e_uuid,
            inviter_id=u_uuid,
            invited_id=i_uuid,
            status=InviteRequestStatus.pending
        )
        db.session.add(new_invite)
        db.session.commit()
        
        invite_created.send(
            current_app._get_current_object(),
            from_user_id=u_uuid,
            from_user_username=user.username,
            to_user_id=i_uuid,
            invite_id=new_invite.invite_id,
            event_id=e_uuid,
            event_name=event.event_name
        )
        current_app.logger.info(f"INFO: /invite, user {u_uuid} invited user {i_uuid} to event {e_uuid}")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /invite, DB exception occured:")
        current_app.logger.exception(e, stack_info=True)
        return make_api_response(ResponseTypes.SERVER_ERROR)
    
    return make_api_response(ResponseTypes.CREATED, message="Invite created successfully")

'''
Input: URL Parameter <uuid:event_id>, Header { "Authorization": "Bearer <Access_Token>" }, JSON { "invited": <uuid> }
Action: Locates a specific invitation from the inviter to the invited user for the given event and deletes it
Data sent to the frontend: {"message": "Invite deleted successfully"}
Output: 200 OK (or 404/400/500 on error)
''' 
@interaction_bp.route("/delete_invite/<event_id>", methods=["DELETE"])
@limiter.limit("100 per minute")
@jwt_required()
def delete_invite(event_id):
    user = get_current_user()
    u_uuid = validate_uuid(user.user_id)
    e_uuid = validate_uuid(event_id)

    invite_data = request.get_json(silent=True)
    i_uuid = validate_uuid(invite_data.get("invited") if invite_data else None)

    if not u_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid inviter ID")
    if not e_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid event ID")
    if not i_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid invited ID")
    
    invite = db.session.query(Invites).filter_by(event_id=e_uuid, inviter_id=u_uuid, invited_id=i_uuid).first()
    if not invite:
        return make_api_response(ResponseTypes.NOT_FOUND, message=f"invitattion to event: {e_uuid} from: {u_uuid} to: {i_uuid} does not exist")
    
    try:
        db.session.delete(invite)
        db.session.commit()
        current_app.logger.info(f"INFO: /delete_invite, user {u_uuid} successfully deleted invite for user {i_uuid}")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /delete_invite, DB exception occured:")
        current_app.logger.exception(e, stack_info=True)
        return make_api_response(ResponseTypes.SERVER_ERROR)
    
    return make_api_response(ResponseTypes.SUCCESS, message="Invite deleted successfully")
    
'''
Input: URL Parameter <uuid:invite_id>, Header { "Authorization": "Bearer <Access_Token>" }, JSON { "status": "accepted" / "declined" }
Action: Updates the status of a received invite. If accepted, the user is added to the Event_participants table and the event's count is incremented
Data sent to the frontend: {"message": "Invite status changed successfully"}
Output: 200 OK (or 404/400/403/409/500 on error)
'''
@interaction_bp.route("/change_invite_status/<invite_id>", methods=["POST"])
@limiter.limit("100 per minute")
@jwt_required()
def change_invite_status(invite_id):
    user = get_current_user()
    u_uuid = validate_uuid(user.user_id)
    i_uuid = validate_uuid(invite_id)

    if not u_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid user ID")
    if not i_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid invite ID")
    
    invite = db.session.get(Invites, i_uuid)
    if invite is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="This invite does not exist")

    if invite.invited_id != u_uuid:
        current_app.logger.warning(f"WARNING: /change_invite_status, user {u_uuid} tried to change status of invite {invite_id} not meant for him")
        return make_api_response(ResponseTypes.FORBIDDEN, message="You can only change status of the invites meant to you")
    
    if invite.status != InviteRequestStatus.pending:
        return make_api_response(ResponseTypes.CONFLICT, message="This invite is already accepted/declined")
    
    invite_data = request.get_json(silent=True)
    new_status = sanitize_input(str(invite_data.get("status"))).lower()

    try:
        if new_status == "accepted":
            invite.status  = InviteRequestStatus.accepted
            already_in = db.session.query(Event_participants).filter_by(event_id=invite.event_id, user_id=u_uuid).first()
            if not already_in:
                participant = Event_participants(
                    event_id=invite.event_id,
                    user_id=u_uuid,
                )
                db.session.add(participant)
                event = db.session.get(Event, invite.event_id)
                if event:
                    event.participant_count = Event.participant_count + 1
            
                event_new_participant.send(
                current_app._get_current_object(),
                participant_id=user.user_id,
                participant_username=user.username,
                creator_id=event.creator_id,
                event_id=event.event_id,
                event_name=event.event_name
                )

            invite_status_update.send(
            current_app._get_current_object(),
            invite_id=invite.invite_id,
            inviter_id=invite.inviter_id,
            invitee_id=user.user_id,
            invitee_username=user.username,
            event_id=event.event_id,
            event_name=event.event_name,
            status="accepted"
            )
        elif new_status == "declined":
            invite.status = InviteRequestStatus.declined
            invite_status_update.send(
                current_app._get_current_object(),
                invite_id=invite.invite_id,
                inviter_id=invite.inviter_id,
                invitee_id=user.user_id,
                invitee_username=user.username,
                event_id=event.event_id,
                event_name=event.event_name,
                status="declined"
            )
        else:
            return make_api_response(ResponseTypes.INVALID_DATA, message="Incorrect status")
        db.session.commit()
        current_app.logger.info(f"INFO: /change_invite_status, user {u_uuid} successfully set status to {new_status} for invite {invite_id}")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /change_invite_status, DB exception occured:")
        current_app.logger.exception(e, stack_info=True)
        return make_api_response(ResponseTypes.SERVER_ERROR)
    
    return make_api_response(ResponseTypes.SUCCESS, message="Invite status changed successfully")

'''
Input: URL Parameter <uuid:event_id>
Action: Adds user as a participant to the event, increments participant_count, and invalidates cache
Data sent to the frontend: {"message": "Joined event successfully", "participant_count": <int>}
Output: 200 OK (or 400/403/404/409/500 on error)
'''
@interaction_bp.route("/join/<event_id>", methods=["POST"])
@limiter.limit("100 per minute")
@jwt_required()
def join_event(event_id):
    user = get_current_user()
    e_uuid = validate_uuid(event_id)

    if not e_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid Event ID")

    event = db.session.get(Event, e_uuid)
    if event is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="This event does not exist")

    if event.creator_id == user.user_id:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Creator is already participating")

    if event.is_private:
        has_access = db.session.query(Event_visibility).filter_by(event_id=e_uuid, shared_with=user.user_id).first()
        if not has_access:
            current_app.logger.warning(f"WARNING: /join, user {user.user_id} tried to join private event {event_id} without access")
            return make_api_response(ResponseTypes.FORBIDDEN, message="This event is private")

    existing = db.session.query(Event_participants).filter_by(event_id=e_uuid, user_id=user.user_id).first()
    if existing:
        return make_api_response(ResponseTypes.CONFLICT, message="You are already participating in this event")

    try:
        participant = Event_participants(event_id=e_uuid, user_id=user.user_id)
        db.session.add(participant)
        event.participant_count = Event.participant_count + 1
        db.session.commit()
        invalidate_event_cache(str(e_uuid))
        db.session.refresh(event)
        current_app.logger.info(f"INFO: /join, user {user.user_id} successfully joined event {event_id}")

        event_new_participant.send(
            current_app._get_current_object(),
            participant_id=user.user_id,
            participant_username=user.username,
            creator_id=event.creator_id,
            event_id=event.event_id,
            event_name=event.event_name
        )

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /join, DB exception occured:")
        current_app.logger.exception(e, stack_info=True)
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Joined event successfully", data={
        "participant_count": int(event.participant_count or 0),
    })

'''
Input: URL Parameter <uuid:event_id>, Header { "Authorization": "Bearer <Access_Token>" }
Action: Removes the user from the Event_participants table and decrements the event's participant_count. Creators are blocked from leaving their own events
Data sent to the frontend: {"message": "Left event successfully", "participant_count": <int>}
Output: 200 OK (or 404/400/500 on error)
'''
@interaction_bp.route("/leave/<event_id>", methods=["DELETE"])
@limiter.limit("100 per minute")
@jwt_required()
def leave_event(event_id):
    user = get_current_user()
    e_uuid = validate_uuid(event_id)

    if not e_uuid:
        return make_api_response(ResponseTypes.INVALID_DATA, message="Invalid Event ID")

    event = db.session.get(Event, e_uuid)
    if event is None:
        return make_api_response(ResponseTypes.NOT_FOUND, message="This event does not exist")

    if event.creator_id == user.user_id:
        current_app.logger.warning(f"WARNING: /leave_event, user {user.user_id} tried to leave their own event")
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Creator cannot leave their own event")

    participant = db.session.query(Event_participants).filter_by(event_id=e_uuid, user_id=user.user_id).first()
    if not participant:
        current_app.logger.warning(f"WARNING: /leave_event, user {user.user_id} tried to leave event which he is not participating in")
        return make_api_response(ResponseTypes.NOT_FOUND, message="You are not participating in this event")

    try:
        db.session.delete(participant)
        event.participant_count = Event.participant_count - 1
        db.session.commit()
        invalidate_event_cache(str(e_uuid))
        db.session.refresh(event)
        current_app.logger.info(f"INFO: /leave_event, user {user.user_id} successfully left event {event_id}")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"ERROR: /leave_event, DB exception occured:")
        current_app.logger.exception(e, stack_info=True)
        return make_api_response(ResponseTypes.SERVER_ERROR)

    return make_api_response(ResponseTypes.SUCCESS, message="Left event successfully", data={
        "participant_count": int(event.participant_count or 0),
    })