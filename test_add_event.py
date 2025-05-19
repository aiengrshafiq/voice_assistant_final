from app.services.calendar_manager import add_event
import datetime

start = datetime.datetime.now() + datetime.timedelta(minutes=5)
end = start + datetime.timedelta(minutes=30)

start_str = start.isoformat()
end_str = end.isoformat()

result = add_event("Test Meeting", start_str, end_str)
print("➕", result)
