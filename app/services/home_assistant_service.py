# app/services/home_assistant_service.py
import requests
from app.core.logger import get_logger
from app.core.config import get_settings
from app.utils.entity_map import get_entity_id

logger = get_logger(__name__)
settings = get_settings()

class HomeAssistantService:
    """V3.1: Unified service for all Home Assistant API interactions."""

    def __init__(self):
        self.base_url = settings.HOME_ASSISTANT_URL
        self.headers = {
            "Authorization": f"Bearer {settings.HOME_ASSISTANT_TOKEN}",
            "Content-Type": "application/json",
        }
        if "YOUR_HA_TOKEN" in settings.HOME_ASSISTANT_TOKEN:
            logger.warning("Home Assistant token is a placeholder.")

    def _call_service(self, domain: str, service: str, service_data: dict) -> bool:
        api_url = f"{self.base_url}/api/services/{domain}/{service}"
        try:
            response = requests.post(api_url, headers=self.headers, json=service_data, timeout=5)
            response.raise_for_status()
            logger.info(f"Successfully called HA service '{domain}.{service}'")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call Home Assistant API: {e}")
            return False

    def trigger_scene_by_name(self, scene_name: str, **kwargs) -> dict:
        scene_entity_id = get_entity_id(scene_name)
        if not scene_entity_id:
            return {"status": "failed", "message": f"I don't have a scene called '{scene_name}'."}
        
        if self._call_service("scene", "turn_on", {"entity_id": scene_entity_id}):
            return {"status": "success", "message": f"Okay, I've activated the {scene_name} scene."}
        else:
            return {"status": "error", "message": "I had trouble activating that scene."}

    def control_entity_state(self, device_name: str, state: str, **kwargs) -> dict:
        entity_id = get_entity_id(device_name)
        if not entity_id:
            return {"status": "failed", "message": f"I don't know about a device called '{device_name}'."}

        domain = entity_id.split('.')[0]
        if domain not in ['light', 'switch', 'fan', 'input_boolean']:
            return {"status": "failed", "message": f"I can't turn a '{domain}' on or off."}

        service = "turn_on" if state == "on" else "turn_off"
        
        if self._call_service(domain, service, {"entity_id": entity_id}):
            return {"status": "success", "message": f"Okay, the {device_name} is now {state}."}
        else:
            return {"status": "error", "message": f"I had trouble controlling the {device_name}."}

    def set_thermostat(self, temperature: int, device_name: str = None, location: str = None, **kwargs) -> dict:
        """Sets the temperature, defaulting to the Meeting Room if not specified."""
        
        target_device = device_name or location
        informing_message = ""

        # --- THE FIX: Intelligent Defaulting Logic ---
        if not target_device:
            # If no device/location is specified by the user, apply the defaults.
            entity_id = "climate.meeting_room"
            target_device = "Meeting Room"
            # Prepare a message to inform the user about the default action.
            informing_message = f"No location specified, setting the {target_device} thermostat. "
            logger.info("No thermostat specified, defaulting to Meeting Room.")
        else:
            # If a device IS specified, use the normal lookup logic.
            entity_id = get_entity_id(target_device)
            if not entity_id or 'climate' not in entity_id:
                 return {"status": "failed", "message": f"I can't find a thermostat called '{target_device}'."}
        # --- END OF FIX ---

        service_data = {"entity_id": entity_id, "temperature": temperature}
        if self._call_service("climate", "set_temperature", service_data):
            success_message = f"Okay, I've set the temperature to {temperature} degrees."
            # Prepend the informing message if it exists
            full_message = informing_message + success_message
            return {"status": "success", "message": full_message}
        else:
            return {"status": "error", "message": "I had trouble setting the thermostat."}

ha_service = HomeAssistantService()