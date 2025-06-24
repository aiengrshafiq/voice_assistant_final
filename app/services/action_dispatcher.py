from app.core.logger import get_logger
from app.services.slack_service import slack_service
from app.services.home_assistant_service import ha_service
from app.services.music_service import music_service
from app.services.calendar_service import calendar_service
from app.utils.entity_map import get_entity_id

logger = get_logger(__name__)

# This ACTION_MAP is the heart of the dispatcher.
# It maps an 'intent' string from the NLU to a specific service function.
ACTION_MAP = {
    "summon_person": lambda result: slack_service.summon_person(result.get('target')),
    "set_mood": lambda result: ha_service.trigger_scene_by_name(result.get('target')),
    # Add more intents and their corresponding actions here in the future
    # e.g., "set_reminder": lambda result: calendar_service.set_reminder(...)

    # Music Commands
    "play_playlist": lambda result: music_service.play_playlist(result.get('target')),
    "play_song": lambda result: music_service.play_song(result.get('target')),
    "stop_music": lambda result: music_service.stop_music(),
    "pause_music": lambda result: music_service.pause(),
    "resume_music": lambda result: music_service.resume(),

    # Calendar
    "get_calendar_events": lambda result: calendar_service.get_upcoming_events(),
    "schedule_meeting": lambda result: calendar_service.create_event(
        summary=result.get('target'),
        start_time=result.get('modifiers', {}).get('start_time'),
        end_time=result.get('modifiers', {}).get('end_time'),
        description=result.get('modifiers', {}).get('description')
    ),
   

    # --- MODIFICATION: Device actions now look up the entity_id ---
    "control_device_state": lambda result: ha_service.control_entity_state(
        entity_id=get_entity_id(result.get('target')),
        state=result.get('modifiers', {}).get('state')
    ),
    "set_thermostat": lambda result: ha_service.set_thermostat(
        entity_id=get_entity_id(result.get('target')),
        temperature=result.get('modifiers', {}).get('temperature')
    ),
}

def dispatch_action(nlu_result: dict) -> str:
    """
    Looks at the NLU result, validates it, and calls the appropriate service function.
    """
    intent = nlu_result.get('intent')
    target = nlu_result.get('target')
    logger.info(f"Dispatching action for intent: '{intent}' with target: '{target}'")

    if not intent:
        return "I'm not sure what you want me to do. The intent is missing."

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
    action_function = ACTION_MAP.get(intent)

    if action_function:
        try:
            return action_function(nlu_result)
        except Exception as e:
            logger.exception(f"An error occurred while executing action for intent '{intent}': {e}")
            return "I ran into an unexpected error while trying to perform that action."
    else:
        logger.warning(f"No action defined for the intent: '{intent}'")
        return f"I understand you want to '{intent.replace('_', ' ')}', but I don't know how to do that yet."