from app.services.text_to_speech import speak
from app.services.calendar_manager import get_todays_events
from app.utils.weather import get_current_weather
from app.core.logger import get_logger

logger = get_logger(__name__)

def deliver_daily_briefing():
    try:
        speak("Good morning. Here’s your daily briefing.")

        # 1. Calendar
        events = get_todays_events()
        speak(events)

        # 2. Weather
        weather = get_current_weather()
        speak(weather)

        # You can expand here to include:
        # - Smart alerts
        # - Reminders due
        # - Notifications

        speak("That concludes your briefing. Have a productive day!")

    except Exception as e:
        logger.exception("Failed to deliver daily briefing.")
        speak("I'm sorry, I couldn't complete the briefing.")
