from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from app.services.text_to_speech import speak
from app.core.logger import get_logger
from app.services.notifier import send_email_notification
from threading import Thread

logger = get_logger(__name__)
scheduler = BackgroundScheduler()
scheduler.start()

def schedule_reminder(message: str, delay_minutes: int = None, time_str: str = None):
    if delay_minutes is not None:
        trigger_time = datetime.now() + timedelta(minutes=delay_minutes)
    elif time_str:
        today = datetime.now().date()
        try:
            trigger_time = datetime.combine(today, datetime.strptime(time_str, "%H:%M").time())
            if trigger_time < datetime.now():
                trigger_time += timedelta(days=1)  # if past time today, schedule for tomorrow
        except Exception as e:
            logger.error(f"Invalid time format: {e}")
            return "Invalid time format. Please use HH:MM."
    else:
        return "Please specify a reminder time."

    scheduler.add_job(
        func=deliver_reminder,
        trigger='date',
        run_date=trigger_time,
        args=[message],
        id=f"reminder_{trigger_time.timestamp()}"
    )
    logger.info(f"Scheduled reminder at {trigger_time}: {message}")
    return f"Reminder set for {trigger_time.strftime('%I:%M %p')}."

def deliver_reminder(message: str):
    def _task():
        logger.info(f"Delivering reminder: {message}")
        speak(f"Reminder: {message}")
        send_email_notification(subject="Reminder Alert", html_content=f"<p>{message}</p>")

    # Run the actual task in a thread to avoid blocking
    Thread(target=_task).start()

# def deliver_reminder(message: str):
#     logger.info(f"Delivering reminder: {message}")
#     speak(f"Reminder: {message}")
#     send_email_notification(subject="Reminder Alert", html_content=f"<p>{message}</p>")
#     return "Reminder delivered."
    
