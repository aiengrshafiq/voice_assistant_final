from app.core.logger import get_logger
from app.services.slack_service import slack_service
from app.services.home_assistant_service import ha_service
from app.services.music_service import music_service
from app.services.calendar_service import calendar_service
from app.services.time_service import time_service
from app.utils.entity_map import get_entity_id

logger = get_logger(__name__)

# This ACTION_MAP is the heart of the dispatcher.
# Each action is now a dictionary with a handler and a required permission level.
ACTION_MAP = {
    # --- Private Actions (Requires Verified CEO Voice) ---
    "summon_person": {
        "handler": lambda result: slack_service.summon_person(result.get('target')),
        "permission": "private"
    },
    "get_calendar_events": {
        "handler": lambda result: calendar_service.get_upcoming_events(),
        "permission": "private"
    },
    "schedule_meeting": {
        "handler": lambda result: calendar_service.create_event(
            summary=result.get('target'),
            start_time=result.get('modifiers', {}).get('start_time'),
            end_time=result.get('modifiers', {}).get('end_time'),
            description=result.get('modifiers', {}).get('description')
        ),
        "permission": "private"
    },

    # --- Public Actions (Available in Guest Mode) ---
    "get_current_time":     {"handler": lambda res: time_service.get_current_time(), "permission": "public"},
    "set_mood": {
        "handler": lambda result: ha_service.trigger_scene_by_name(result.get('target')),
        "permission": "public"
    },
    "control_device_state": {
        "handler": lambda result: ha_service.control_entity_state(
            entity_id=get_entity_id(result.get('target')),
            state=result.get('modifiers', {}).get('state')
        ),
        "permission": "public"
    },
    "set_thermostat": {
        "handler": lambda result: ha_service.set_thermostat(
            entity_id=get_entity_id(result.get('target')),
            temperature=result.get('modifiers', {}).get('temperature')
        ),
        "permission": "public"
    },
    "play_playlist": {
        "handler": lambda result: music_service.play_playlist(result.get('target')),
        "permission": "public"
    },
    "play_song": {
        "handler": lambda result: music_service.play_song(result.get('target')),
        "permission": "public"
    },
    "stop_music": {
        "handler": lambda result: music_service.stop_music(),
        "permission": "public"
    },
    "pause_music": {
        "handler": lambda result: music_service.pause(),
        "permission": "public"
    },
    "resume_music": {
        "handler": lambda result: music_service.resume(),
        "permission": "public"
    },
    "get_current_time": {
        "handler": lambda result: time_service.get_current_time(),
        "permission": "public"
    },
}


def dispatch_action(nlu_result: dict, access_level: str) -> str:
    """
    Looks at the NLU result, validates it, and calls the appropriate service function.
    """
    intent = nlu_result.get('intent')
    target = nlu_result.get('target')
    logger.info(f"Dispatching action for intent: '{intent}' with target: '{target}'")

    if not intent:
        return "I'm not sure what you want me to do. The intent is missing."

    action_details = ACTION_MAP.get(intent)
    if not action_details:
        logger.warning(f"No action defined for the intent: '{intent}'")
        return f"I understand you want to '{intent.replace('_', ' ')}', but I don't know how to do that yet."

    # --- THE SECURITY CHECK ---
    required_permission = action_details["permission"]
    if required_permission == "private" and access_level != "private":
        logger.warning(f"Permission denied for user with level '{access_level}' to access private intent '{intent}'.")
        return "I'm sorry, but that is a private command that only the CEO can authorize."



    # --- NEW: Centralized check for device-related intents ---
    device_intents = ["control_device_state", "set_thermostat"]
    if intent in device_intents:
        if not target:
            return f"You need to specify which device you want to control."
        
        entity_id = get_entity_id(target)
        if not entity_id:
            logger.warning(f"No entity_id found in entity_map.py for target: '{target}'")
            return f"I don't know about a device called '{target}'. Please check the configuration."

    # --- The rest of the function proceeds as normal ---
    action_handler = action_details["handler"]

    if action_handler:
        try:
            return action_handler(nlu_result)
        except Exception as e:
            logger.exception(f"An error occurred while executing action for intent '{intent}': {e}")
            return "I ran into an unexpected error while trying to perform that action."
    else:
        logger.warning(f"No action defined for the intent: '{intent}'")
        return f"I understand you want to '{intent.replace('_', ' ')}', but I don't know how to do that yet."