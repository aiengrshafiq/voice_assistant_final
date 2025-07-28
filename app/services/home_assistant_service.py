# app/services/home_assistant_service.py
import requests
from app.core.logger import get_logger
from app.core.config import get_settings
from app.utils.entity_map import get_entity_id # We will still use this utility

logger = get_logger(__name__)
settings = get_settings()

class HomeAssistantService:
    """V3: Unified service for all Home Assistant API interactions."""

    def __init__(self):
        self.base_url = settings.HOME_ASSISTANT_URL
        self.headers = {
            "Authorization": f"Bearer {settings.HOME_ASSISTANT_TOKEN}",
            "Content-Type": "application/json",
        }
        if "YOUR_HA_TOKEN" in settings.HOME_ASSISTANT_TOKEN:
            logger.warning("Home Assistant token is a placeholder. Service may not work.")

    def _call_service(self, domain: str, service: str, service_data: dict) -> bool:
        """Helper to make a generic service call to Home Assistant."""
        api_url = f"{self.base_url}/api/services/{domain}/{service}"
        try:
            response = requests.post(api_url, headers=self.headers, json=service_data, timeout=5)
            response.raise_for_status()
            logger.info(f"Successfully called HA service '{domain}.{service}' with data: {service_data}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call Home Assistant API: {e}")
            return False

    def trigger_scene_by_name(self, scene_name: str, **kwargs) -> dict:
        """Triggers a scene and returns a V3-compliant dictionary."""
        # This uses the entity map now for consistency
        scene_entity_id = get_entity_id(scene_name)
        if not scene_entity_id:
            return {"status": "failed", "message": f"I don't have a scene called '{scene_name}' configured."}
        
        if self._call_service("scene", "turn_on", {"entity_id": scene_entity_id}):
            return {"status": "success", "message": f"Okay, I've activated the {scene_name} scene."}
        else:
            return {"status": "error", "message": "Sorry, I had trouble activating that scene."}

    def control_entity_state(self, device_name: str, state: str, **kwargs) -> dict:
        """Controls any entity that supports turn_on/turn_off services."""
        entity_id = get_entity_id(device_name)
        if not entity_id:
            return {"status": "failed", "message": f"I don't know about a device called '{device_name}'."}

        domain = entity_id.split('.')[0]
        if domain not in ['light', 'switch', 'fan', 'input_boolean']:
            return {"status": "failed", "message": f"I don't know how to turn a '{domain}' device on or off."}

        service = "turn_on" if state == "on" else "turn_off"
        
        if self._call_service(domain, service, {"entity_id": entity_id}):
            return {"status": "success", "message": f"Okay, the {device_name} is now {state}."}
        else:
            return {"status": "error", "message": f"I had trouble controlling the {device_name}."}

    def set_thermostat(self, device_name: str, temperature: int, **kwargs) -> dict:
        """Sets the temperature for a climate entity."""
        entity_id = get_entity_id(device_name)
        if not entity_id or 'climate' not in entity_id:
             return {"status": "failed", "message": f"I can't find a thermostat called '{device_name}'."}

        service_data = {"entity_id": entity_id, "temperature": temperature}
        if self._call_service("climate", "set_temperature", service_data):
            return {"status": "success", "message": f"Okay, I've set the {device_name} to {temperature} degrees."}
        else:
            return {"status": "error", "message": "I had trouble setting the thermostat."}

ha_service = HomeAssistantService()