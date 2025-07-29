# app/services/action_dispatcher.py
import asyncio
from app.core.logger import get_logger
from app.services.slack_service import slack_service
from app.services.home_assistant_service import ha_service
from app.services.music_service import music_service
from app.services.calendar_service import calendar_service
from app.services.time_service import time_service
from app.services.daily_briefing import deliver_daily_briefing

logger = get_logger(__name__)

ACTION_MAP = {
    "summon_person": slack_service.summon_person,
    "get_calendar_events": calendar_service.get_upcoming_events,
    "schedule_meeting": calendar_service.create_event,
    "get_current_time": time_service.get_current_time,
    "daily_briefing": deliver_daily_briefing,
    "set_mood": ha_service.trigger_scene_by_name,
    "control_device": ha_service.control_entity_state,
    "set_thermostat": ha_service.set_thermostat,
    "play_music": music_service.play_music,
}

async def dispatch_action(nlu_result: dict, access_level: str) -> dict:
    intent = nlu_result.get('intent')
    entities = nlu_result.get('entities', {})
    logger.info(f"Dispatching action for intent: '{intent}' with entities: {entities}")

    action_handler = ACTION_MAP.get(intent)
    if not action_handler:
        return {"status": "failed", "message": "I understand the intent, but I don't know how to do that."}
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, lambda: action_handler(**entities))
        return result if isinstance(result, dict) else {"status": "success", "message": result}
    except Exception as e:
        logger.exception(f"Error executing action for intent '{intent}': {e}")
        return {"status": "error", "message": "I ran into an error performing that action."}