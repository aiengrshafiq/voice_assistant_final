import datetime
from app.core.logger import get_logger

logger = get_logger(__name__)

class TimeService:
    """A simple service to provide time-related information."""
    
    def get_current_time(self) -> str:
        """Returns the current time in a user-friendly format."""
        now = datetime.datetime.now()
        # Format: e.g., "3:45 PM"
        friendly_time = now.strftime("%I:%M %p").lstrip('0')
        logger.info(f"Providing current time: {friendly_time}")
        return f"The current time is {friendly_time}."

# Create a single instance
time_service = TimeService()