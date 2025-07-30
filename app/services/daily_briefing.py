# app/services/daily_briefing.py
from app.services.speech_service import speak
from app.services.calendar_service import calendar_service
from app.core.logger import get_logger
# from app.utils.weather import get_current_weather # Add this back when you have it

logger = get_logger(__name__)

def deliver_daily_briefing(**kwargs) -> dict:
    """Delivers the daily briefing by calling other services."""
    try:
        speak("Good morning, sir. Here is your daily briefing.")
        
        # 1. Calendar
        events_result = calendar_service.get_upcoming_events()
        speak(events_result.get("message", "I couldn't fetch your calendar events."))

        # 2. Weather (Example)
        # weather_report = get_current_weather()
        # speak(weather_report)
        
        final_message = "That concludes your briefing. Have a productive day."
        speak(final_message)
        return {"status": "success", "message": ""} # Message is already spoken
    except Exception as e:
        logger.exception("Failed to deliver daily briefing.")
        return {"status": "error", "message": "I ran into an error preparing your briefing."}