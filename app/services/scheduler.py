from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, time as dtime
from app.services.daily_briefing import deliver_daily_briefing

scheduler = BackgroundScheduler()
scheduler.start()

def schedule_daily_briefing():
    scheduler.add_job(
        deliver_daily_briefing,
        trigger='cron',
        hour=8, minute=0, id="daily_briefing_job", replace_existing=True
    )
