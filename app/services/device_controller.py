import requests
from app.core.config import get_settings
from app.core.logger import get_logger

from app.services.calendar_manager import add_event,get_todays_events
from app.services.reminder_service import schedule_reminder


logger = get_logger(__name__)
settings = get_settings()

HEADERS = {
    "Authorization": f"Bearer {settings.HOME_ASSISTANT_TOKEN}",
    "Content-Type": "application/json"
}

DOMAIN_MAP = {
    "light": "light",
    "plug": "switch",
    "thermostat": "climate",
    "speaker": "media_player",
    "tv": "media_player"
}

SERVICE_MAP = {
    "turn_on_light": ("light", "turn_on"),
    "turn_off_light": ("light", "turn_off"),
    "turn_on_plug": ("switch", "turn_on"),
    "turn_off_plug": ("switch", "turn_off"),
    "turn_on_speaker": ("media_player", "turn_on"),
    "turn_off_speaker": ("media_player", "turn_off"),
    "set_thermostat": ("climate", "set_temperature")
}

ENTITY_MAP = {
    # Examples (customize based on your HA setup)
    "hallway light": "light.hallway",
    "kitchen plug": "switch.kitchen",
    "living room speaker": "media_player.living_room",
    "ac": "climate.main_room",
    "speaker": "media_player.office",
    "tv": "media_player.living_room_tv",
    "entertainment room": "climate.entertainment_room",
    "hall": "climate.hall",
    "left pathway": "climate.left_pathway",
    "meeting room": "climate.meeting_room",
    "pantry area": "climate.pantry_area"
}

COMMON_INTENTS = {
    "get_schedule", "create_event", "get_schedules", "add_event"
}

def call_service(domain, service, payload, intent ):
    url = f"{settings.HOME_ASSISTANT_URL}/api/services/{domain}/{service}"
    logger.info(f"Calling: {url} with {payload}")
    response = requests.post(url, json=payload, headers=HEADERS)

    if response.status_code == 200:
        return f"{intent.replace('_', ' ').capitalize()} successful."
    else:
        logger.error(f"Home Assistant error: {response.text}")
        return "Failed to complete the action."


def execute_common_action(intent: str, parameters: dict) -> str:
    try:
        if intent == "get_schedule":
            logger.warning(f"get_schedule called {intent} ")
            return get_todays_events()

        elif intent == "create_event" or intent == "add_event":
            summary = parameters.get("summary")
            start = parameters.get("start_time")
            end = parameters.get("end_time")
            if not all([summary, start, end]):
                return "Please mention the event title and time clearly."
            logger.warning(f"Adding event {summary} for {start} and {end}")
            return add_event(summary, start, end)
        
        elif intent == "set_reminder":
            message = parameters.get("message", "your reminder")
            delay = parameters.get("delay_minutes")
            time_str = parameters.get("time")
            return schedule_reminder(message, delay_minutes=delay, time_str=time_str)


    except Exception as e:
        logger.exception("Common intent execution failed.")
        return "Something went wrong while execusting the common action."



def execute_device_action(intent: str, parameters: dict) -> str:
    try:
        logger.debug(f"Intent received: {intent}")
        logger.debug(f"Checking against COMMON_INTENTS: {COMMON_INTENTS}")
        intent = intent.strip().lower()
        if intent in COMMON_INTENTS:
            result = execute_common_action(intent, parameters)
            return result or "Task completed."
           


        if intent not in SERVICE_MAP:
            logger.warning(f"Unsupported intent: {intent}")
            return "Unsupported action."

        domain, service = SERVICE_MAP[intent]
        entity_name = parameters.get("device", "speaker") or parameters.get("room") or parameters.get("target")

        if not entity_name:
            logger.warning("No device or room specified.")
            return "I didn't catch which device to control."

        entity_key = entity_name.lower().strip()
        entity_id = ENTITY_MAP.get(entity_key)

        if not entity_id:
            logger.warning(f"Entity not mapped: {entity_key}")
            return f"I don’t know how to control {entity_name}."

        payload = {"entity_id": entity_id}

        if intent == "set_thermostat":
            
            temperature = parameters.get("temperature")
            room = parameters.get("room")
            if not room or not temperature:
                return "Please specify both room and temperature."
        
        
            if temperature:
                payload["temperature"] = temperature
            
            logger.warning(f"Setting Thermostate Now for {domain} and {service}")
            call_service(domain, service, payload, intent )

            

        elif intent == "turn_on_speaker":
            logger.warning(f"Turning Speaker On Now for {domain} and media_start")
            if domain == "media_player":
                return call_service(domain, "media_start", payload , intent)
            return call_service(domain, "turn_on", payload , intent)

        elif intent == "turn_off_speaker":
            logger.warning(f"Turning Speaker Off Now for {domain} and media_stop")
            if domain == "media_player":
                return call_service(domain, "media_stop", payload , intent)
            return call_service(domain, "turn_off", payload , intent)

        
            
            
            
    
        

    except Exception as e:
        logger.exception("Device control failed.")
        return "Something went wrong controlling the device."
