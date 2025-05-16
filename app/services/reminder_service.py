from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from app.services.text_to_speech import speak
from app.core.logger import get_logger
from app.services.notifier import send_email_notification

logger = get_logger(__name__)
scheduler = BackgroundScheduler()
scheduler.start()

def schedule_reminder(message: str, delay_minutes: int = 1):
    trigger_time = datetime.now() + timedelta(minutes=delay_minutes)
    scheduler.add_job(
        func=deliver_reminder,
        trigger='date',
        run_date=trigger_time,
        args=[message],
        id=f"reminder_{trigger_time.timestamp()}"
    )
    logger.info(f"Scheduled reminder at {trigger_time}: {message}")
    return f"Reminder set in {delay_minutes} minute(s)."

def deliver_reminder(message: str):
    logger.info(f"Delivering reminder: {message}")
    speak(f"Reminder: {message}")
    send_email_notification(subject="Reminder Alert", html_content=f"<p>{message}</p>")
