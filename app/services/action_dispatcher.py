import asyncio
from app.core.logger import get_logger
from app.services.slack_service import slack_service
from app.services.home_assistant_service import ha_service
from app.services.music_service import music_service
from app.services.calendar_service import calendar_service
from app.services.time_service import time_service
from app.utils.entity_map import get_entity_id

logger = get_logger(__name__)

# --- V3 ACTION_MAP ---
# This map is updated for the new NLU structure.
# We now use `**result.get('entities', {})` to pass the entire entities dictionary
# as keyword arguments to the handler functions. This is cleaner and more scalable.
ACTION_MAP = {
    # --- Private Actions (Requires Verified CEO Voice) ---
    # For testing, permissions are public. Revert to "private" for production.
    "summon_person": {
        "handler": lambda res: slack_service.summon_person(**res.get('entities', {})),
        "permission": "public"
    },
    "get_calendar_events": {
        "handler": lambda res: calendar_service.get_upcoming_events(),
        "permission": "public"
    },
    "schedule_meeting": {
        "handler": lambda res: calendar_service.create_event(**res.get('entities', {})),
        "permission": "public"
    },

    # --- Public Actions (Available in Guest Mode) ---
    "get_current_time": {
        "handler": lambda res: time_service.get_current_time(),
        "permission": "public"
    },
    "set_mood": {
        "handler": lambda res: ha_service.trigger_scene_by_name(**res.get('entities', {})),
        "permission": "public"
    },
    "control_device": {
        "handler": lambda res: ha_service.control_entity_state(**res.get('entities', {})),
        "permission": "public"
    },
    "set_thermostat": {
        "handler": lambda res: ha_service.set_thermostat(**res.get('entities', {})),
        "permission": "public"
    },
    "play_music": {
        "handler": lambda res: music_service.play_song(**res.get('entities', {})),
        "permission": "public"
    },
    "stop_music": {
        "handler": lambda res: music_service.stop_music(),
        "permission": "public"
    },
    "pause_music": {
        "handler": lambda res: music_service.pause(),
        "permission": "public"
    },
    "resume_music": {
        "handler": lambda res: music_service.resume(),
        "permission": "public"
    },
}


async def dispatch_action(nlu_result: dict, access_level: str) -> dict:
    """
    V3: Asynchronously dispatches actions based on NLU results.
    It now expects and returns a dictionary for richer communication with the state machine.
    """
    intent = nlu_result.get('intent')
    entities = nlu_result.get('entities', {})
    logger.info(f"Dispatching action for intent: '{intent}' with entities: {entities}")

    # Handle cases where NLU fails or intent is unsupported
    if not intent or intent in ['unsupported', 'user_frustrated']:
        message = nlu_result.get('response_suggestion', "I'm sorry, I can't help with that.")
        return {"status": "failed", "message": message}

    action_details = ACTION_MAP.get(intent)
    if not action_details:
        logger.warning(f"No action defined for intent: '{intent}'")
        return {"status": "failed", "message": f"I understand the intent is '{intent}', but I don't have a way to handle it."}

    # --- Security Check ---
    required_permission = action_details["permission"]
    if required_permission == "private" and access_level != "private":
        logger.warning(f"Permission denied for user with level '{access_level}' to access private intent '{intent}'.")
        return {"status": "unauthorized", "message": "I'm sorry, that is a private command that only the CEO can authorize."}

    # --- Execute Action Handler ---
    action_handler = action_details["handler"]
    if not action_handler:
        return {"status": "failed", "message": "Action handler not found."}

    try:
        # Run the synchronous handler in a separate thread to avoid blocking the asyncio event loop
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,  # Use the default thread pool executor
            lambda: action_handler(nlu_result)
        )

        # Standardize the response format. If a service returns a simple string, wrap it.
        if isinstance(result, str):
            return {"status": "success", "message": result}
        
        # If the service returns a dict (the new standard), return it directly
        if isinstance(result, dict):
            return result

        # Fallback for unexpected return types
        return {"status": "failed", "message": "The action returned an unexpected result type."}

    except Exception as e:
        logger.exception(f"An error occurred while executing action for intent '{intent}': {e}")
        return {"status": "error", "message": "I ran into an unexpected error while trying to perform that action."}