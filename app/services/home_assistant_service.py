import requests
from app.core.logger import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

# --- Mapping from abstract concepts to specific Home Assistant entity IDs ---
# This is where you configure the assistant to know your specific setup.
SCENE_MAP = {
    "tired": "scene.office_tired_mode",
    "focus": "scene.office_focus_mode",
    "energized": "scene.office_energized_mode",
    "end of day": "scene.office_shutdown"
}
# ---

class HomeAssistantService:
    """Service for interacting with the Home Assistant API."""

    def __init__(self):
        self.base_url = settings.HOME_ASSISTANT_URL
        self.headers = {
            "Authorization": f"Bearer {settings.HOME_ASSISTANT_TOKEN}",
            "Content-Type": "application/json",
        }
        if "YOUR_HA_TOKEN" in settings.HOME_ASSISTANT_TOKEN:
            logger.warning("Home Assistant token seems to be a placeholder. The service may not work.")

    def _call_service(self, domain: str, service: str, service_data: dict) -> bool:
        """Helper to make a generic service call to Home Assistant."""
        api_url = f"{self.base_url}/api/services/{domain}/{service}"
        try:
            response = requests.post(api_url, headers=self.headers, json=service_data, timeout=5)
            response.raise_for_status()  # Raises an exception for 4xx/5xx errors
            logger.info(f"Successfully called HA service '{domain}.{service}' with data: {service_data}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call Home Assistant API: {e}")
            return False

    def trigger_scene_by_name(self, scene_name: str) -> str:
        """Triggers a scene based on a mapped name (e.g., 'focus')."""
        scene_entity_id = SCENE_MAP.get(scene_name.lower())

        if not scene_entity_id:
            logger.warning(f"No scene found in SCENE_MAP for the name: '{scene_name}'")
            return f"I don't have a scene called '{scene_name}' configured."
        
        if self._call_service("scene", "turn_on", {"entity_id": scene_entity_id}):
            return f"Okay, I've activated the {scene_name} scene."
        else:
            return "Sorry, I had trouble activating that scene in Home Assistant."

    # --- NEW FUNCTION FOR LIGHTS ---
    def control_entity_state(self, entity_id: str, state: str) -> str:
        """
        Controls any entity that supports turn_on/turn_off services (lights, switches, fans, etc.).
        It intelligently determines the correct service domain from the entity_id.
        """
        if not entity_id or '.' not in entity_id:
            return "I was given an invalid device ID to control."

        # Intelligently determine the domain (e.g., 'light', 'switch') from the entity_id
        domain = entity_id.split('.')[0]
        
        # Check if the domain is valid for this type of action
        if domain not in ['light', 'switch', 'fan']:
            return f"I don't know how to turn a '{domain}' device on or off."

        service = "turn_on" if state == "on" else "turn_off"
        service_data = {"entity_id": entity_id}
        
        if self._call_service(domain, service, service_data):
            return f"Okay, the device is now {state}."
        else:
            return "I had trouble controlling that device."

    # --- NEW FUNCTION FOR CLIMATE ---
    def set_thermostat(self, entity_id: str, temperature: int) -> str:
        """Sets the temperature for a climate entity."""
        service_data = {"entity_id": entity_id, "temperature": temperature}
        if self._call_service("climate", "set_temperature", service_data):
            return f"Okay, I've set the temperature to {temperature} degrees."
        else:
            return "I had trouble setting the thermostat."

# Create a single instance of the service
ha_service = HomeAssistantService()