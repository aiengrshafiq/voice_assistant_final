import requests
from app.core.config import get_settings
from app.core.logger import get_logger

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
    "speaker": "media_player"
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
    "ac": "climate.main_room"
}

def execute_device_action(intent: str, parameters: dict) -> str:
    try:
        if intent not in SERVICE_MAP:
            logger.warning(f"Unsupported intent: {intent}")
            return "Unsupported action."

        domain, service = SERVICE_MAP[intent]
        entity_name = parameters.get("device") or parameters.get("room") or parameters.get("target")

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
            if temperature:
                payload["temperature"] = temperature

        url = f"{settings.HOME_ASSISTANT_URL}/api/services/{domain}/{service}"
        logger.info(f"Calling: {url} with {payload}")
        response = requests.post(url, json=payload, headers=HEADERS)

        if response.status_code == 200:
            return f"{intent.replace('_', ' ').capitalize()} successful."
        else:
            logger.error(f"Home Assistant error: {response.text}")
            return "Failed to complete the action."

    except Exception as e:
        logger.exception("Device control failed.")
        return "Something went wrong controlling the device."
