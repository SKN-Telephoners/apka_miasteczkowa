from backend.constants import Constants
from backend.helpers import sanitize_input
from cloudinary.utils import cloudinary_url
import json
from zoneinfo import ZoneInfo

local_tz = ZoneInfo("Europe/Warsaw")

'''
Input: raw_location: <str> / [<float:lng>, <float:lat>] / <json_str>
Action: Standardizes location data. It checks if the input is a coordinate pair, a JSON string of coordinates, or a plain text name. It validates that coordinates are within geographical ranges and returns a formatted string like "[lng,lat]" or a sanitized string
Data sent to the frontend: N/A (Internal use)
Output: tuple (<str:normalized_val> or None, <str:error_message> or None)
'''
def normalize_location_input(raw_location):
    if raw_location is None:
        return None, "Location is required"

    parsed_coords = None

    if isinstance(raw_location, (list, tuple)) and len(raw_location) == 2:
        parsed_coords = raw_location
    else:
        location_text = sanitize_input(str(raw_location)).strip()
        if not location_text:
            return None, "Location is required"

        try:
            parsed_json = json.loads(location_text)
            if isinstance(parsed_json, (list, tuple)) and len(parsed_json) == 2:
                parsed_coords = parsed_json
        except (TypeError, ValueError, json.JSONDecodeError):
            parsed_json = None

        if parsed_coords is None and "," in location_text and not location_text.startswith("["):
            parts = [p.strip() for p in location_text.split(",")]
            if len(parts) == 2:
                parsed_coords = parts

        if parsed_coords is None:
            if len(location_text) > Constants.MAX_LOCATION_LEN:
                return None, "Location name is too long"
            return location_text, None

    try:
        lng = float(parsed_coords[0])
        lat = float(parsed_coords[1])
    except (TypeError, ValueError):
        return None, "Invalid location coordinates format"

    if not (-180.0 <= lng <= 180.0 and -90.0 <= lat <= 90.0):
        return None, "Location coordinates are out of range"

    normalized = f"[{lng:.6f},{lat:.6f}]"
    if len(normalized) > Constants.MAX_LOCATION_LEN:
        return None, "Location name is too long"

    return normalized, None

'''
Input: raw_location: <str> / <list>
Action: Specifically attempts to extract numerical longitude and latitude from a database string or list
Data sent to the frontend: N/A (Internal use)
Output: [<float:lng>, <float:lat>] or None
'''
def parse_location_coordinates(raw_location):
    if raw_location is None:
        return None

    if isinstance(raw_location, (list, tuple)) and len(raw_location) == 2:
        candidate = raw_location
    else:
        location_text = str(raw_location).strip()
        if not location_text:
            return None

        try:
            candidate = json.loads(location_text)
        except (TypeError, ValueError, json.JSONDecodeError):
            return None

    if not isinstance(candidate, (list, tuple)) or len(candidate) != 2:
        return None

    try:
        lng = float(candidate[0])
        lat = float(candidate[1])
    except (TypeError, ValueError):
        return None

    if not (-180.0 <= lng <= 180.0 and -90.0 <= lat <= 90.0):
        return None

    return [lng, lat]


'''
Input: event: <Event_Model>, user_id: <uuid>, creator_lookup: <dict>, participating_event_ids: <set>
Action: Converts a database Event object into a comprehensive dictionary for the frontend. It calculates timezones (Europe/Warsaw), generates Cloudinary URLs for event pictures and the creator's profile picture, and sets flags for participation status
Data sent to the frontend: N/A (Internal use - returned to route)
Output: <dict:Serialized_Event_Object>
'''
def serialize_event_payload(event, user_id, creator_lookup, participating_event_ids):
    local_dt = event.date_and_time.astimezone(local_tz) if event.date_and_time else None
    creator = creator_lookup.get(str(event.creator_id))

    return {
        "id": str(event.event_id),
        "event_id": str(event.event_id),
        "name": event.event_name,
        "description": event.description,
        "date": local_dt.strftime("%d.%m.%Y") if local_dt else None,
        "time": local_dt.strftime("%H:%M") if local_dt else None,
        "location": event.location,
        "creator_id": str(event.creator_id),
        "pictures": [
            {
                "cloud_id": pic.cloud_id,
                "url": cloudinary_url(pic.cloud_id, secure=True)[0],
            }
            for pic in event.pictures
        ],
        "creator_username": creator.display_name if creator else None,
        "creator_profile_picture_url": cloudinary_url(creator.profile_picture, secure=True)[0] if creator and creator.profile_picture else None,
        "creator_academy": creator.academy if creator else None,
        "creator_faculty": creator.faculty if creator else None,
        "creator_course": creator.course if creator else None,
        "creator_year": creator.year if creator else None,
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "comment_count": int(event.comment_count or 0),
        "participant_count": int(event.participant_count or 0),
        "participation_count": int(event.participant_count or 0),
        "is_participating": event.creator_id == user_id or event.event_id in participating_event_ids,
        "is_joined": event.creator_id == user_id or event.event_id in participating_event_ids,
        "is_private": event.is_private,
        "location_coordinates": parse_location_coordinates(event.location),
    }