# app/services/action_dispatcher.py
import asyncio
from app.core.logger import get_logger
# Import ALL services
from app.services.calendar_service import calendar_service
from app.services.time_service import time_service
from app.services.daily_briefing import deliver_daily_briefing
from app.services.note_service import log_note, read_notes
from app.services.slack_service import slack_service
from app.services.home_assistant_service import ha_service
from app.services.music_service import music_service

logger = get_logger(__name__)

# This new function defines the assistant's capabilities
def list_capabilities(**kwargs) -> dict:
    capabilities = [
        "check your calendar",
        "schedule a new meeting",
        "get the current time",
        "give you a daily briefing",
        "take a note for you",
        "read your recent notes",
        "and start a real-time translation session.",
        "summon a person via Slack",
        "Home Assistant smart home control"

    ]
    message = "I can: " + ", ".join(capabilities)
    return {"status": "success", "message": message}

# The complete and final map of all assistant capabilities
ACTION_MAP = {
    # Calendar & Time
    "get_calendar_events": calendar_service.get_upcoming_events,
    "schedule_meeting": calendar_service.create_event,
    "get_current_time": time_service.get_current_time,
    
    # Productivity
    "daily_briefing": deliver_daily_briefing,
    "log_note": log_note,
    "read_notes": read_notes,
    
    # Communication
    "summon_person": slack_service.summon_person,

    "get_capabilities": list_capabilities,

    # Smart Home
    "set_mood": ha_service.trigger_scene_by_name,
    "control_device": ha_service.control_entity_state,
    "set_thermostat": ha_service.set_thermostat,

    # Media
    "play_music": music_service.play_music,
}

async def dispatch_action(nlu_result: dict, access_level: str) -> dict:
    intent = nlu_result.get('intent')
    entities = nlu_result.get('entities', {})
    logger.info(f"Dispatching action for intent: '{intent}' with entities: {entities}")

    action_handler = ACTION_MAP.get(intent)
    if not action_handler:
        return {"status": "failed", "message": "I understand the intent, but I don't have a way to handle that request."}
    
    try:
        loop = asyncio.get_running_loop()
        # The lambda function correctly passes the entities as keyword arguments
        result = await loop.run_in_executor(None, lambda: action_handler(**entities))
        
        # Standardize the response format
        return result if isinstance(result, dict) else {"status": "success", "message": result}
    except Exception as e:
        logger.exception(f"Error executing action for intent '{intent}': {e}")
        return {"status": "error", "message": "I ran into an unexpected error while performing that action."}