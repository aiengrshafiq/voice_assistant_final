# app/services/reminder_service.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from threading import Thread
from app.core.logger import get_logger
from app.services.notifier import send_email_notification
# V3: Import from the new unified speech service
from app.services.speech_service import speak

logger = get_logger(__name__)
scheduler = BackgroundScheduler(daemon=True)
scheduler.start()

def deliver_reminder(message: str):
    """The function that gets executed when a reminder is due."""
    def _task():
        logger.info(f"Delivering reminder: {message}")
        speak(f"Reminder: {message}")
        send_email_notification(subject="Jarvis Reminder", html_content=f"<p>{message}</p>")
    Thread(target=_task).start()

def schedule_reminder(message: str, delay_minutes: int = None, time_str: str = None, **kwargs) -> dict:
    """V3: Schedules a reminder and returns a result dictionary."""
    try:
        if delay_minutes is not None:
            trigger_time = datetime.now() + timedelta(minutes=int(delay_minutes))
        elif time_str:
            today = datetime.now().date()
            trigger_time = datetime.combine(today, datetime.strptime(time_str, "%H:%M").time())
            if trigger_time < datetime.now():
                trigger_time += timedelta(days=1)
        else:
            return {"status": "failed", "message": "Please specify when to set the reminder."}

        scheduler.add_job(
            func=deliver_reminder,
            trigger='date',
            run_date=trigger_time,
            args=[message],
            id=f"reminder_{trigger_time.timestamp()}"
        )
        friendly_time = trigger_time.strftime('%I:%M %p')
        logger.info(f"Scheduled reminder at {trigger_time}: {message}")
        return {"status": "success", "message": f"Reminder set for {friendly_time}."}
    except Exception as e:
        logger.error(f"Invalid time format or scheduling error: {e}")
        return {"status": "error", "message": "Sorry, I couldn't set that reminder. The time format seems to be invalid."}