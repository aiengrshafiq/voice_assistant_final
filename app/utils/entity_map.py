# This file maps natural language targets to specific Home Assistant entity IDs.
# It keeps your Home Assistant configuration separate from your AI logic.

ENTITY_MAP = {
    # Lights
    "lights": "switch.ceo_room",
    "office lights": "switch.ceo_room", 
    "desk lamp": "switch.ceo_room",       

    # Climate
    "office thermostat": "climate.meeting_room", 
    "office ac": "climate.meeting_room",
    "room ac": "climate.meeting_room",    
    "ac": "climate.meeting_room",
    "temperature": "climate.meeting_room",    

    # Add other devices here as needed
}

def get_entity_id(natural_name: str) -> str | None:
    """
    Finds the entity_id for a given natural language name.
    Returns None if no matching entity is found.
    """
    return ENTITY_MAP.get(natural_name.lower())