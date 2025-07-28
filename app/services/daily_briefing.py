# app/services/daily_briefing.py
# V3: Import from the new unified speech service and updated calendar service
from app.services.speech_service import speak
from app.services.calendar_service import calendar_service
# You would also import your weather service here
# from app.utils.weather import get_current_weather

logger = get_logger(__name__)

def deliver_daily_briefing(**kwargs) -> dict:
    """V3: Delivers the daily briefing and returns a result dictionary."""
    try:
        speak("Good morning, sir. Here is your daily briefing.")

        # 1. Calendar
        events_result = calendar_service.get_upcoming_events()
        speak(events_result.get("message", "I couldn't fetch your calendar events."))

        # 2. Weather (Example)
        # weather = get_current_weather()
        # speak(weather)
        
        final_message = "That concludes your briefing. Have a productive day."
        speak(final_message)
        return {"status": "success", "message": final_message}
    except Exception as e:
        logger.exception("Failed to deliver daily briefing.")
        return {"status": "error", "message": "I'm sorry, I ran into an error while preparing your briefing."}