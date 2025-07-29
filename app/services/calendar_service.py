# app/services/calendar_service.py
import datetime as dt
import os.path
import humanize
from pendulum import parse as pendulum_parse, from_format
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.core.logger import get_logger

logger = get_logger(__name__)
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def format_datetime_for_speech(iso_string):
    if not iso_string: return "an unspecified time"
    try:
        dt_obj = pendulum_parse(iso_string)
        return humanize.naturaltime(dt_obj)
    except Exception: return "an unspecified time"

class CalendarService:
    def __init__(self):
        self.creds = self._get_credentials()

    def _get_credentials(self) -> Credentials | None:
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try: creds.refresh(Request())
                except Exception:
                    if os.path.exists("token.json"): os.remove("token.json")
                    return self._initiate_auth_flow()
            else: creds = self._initiate_auth_flow()
            if creds:
                with open("token.json", "w") as token: token.write(creds.to_json())
        return creds

    def _initiate_auth_flow(self) -> Credentials | None:
        if not os.path.exists("credentials.json"):
            logger.critical("FATAL: 'credentials.json' not found.")
            return None
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        return flow.run_local_server(port=0)

    def get_upcoming_events(self, **kwargs) -> dict:
        if not self.creds: return {"status": "error", "message": "Calendar authentication failed."}
        try:
            service = build("calendar", "v3", credentials=self.creds)
            now = dt.datetime.utcnow().isoformat() + "Z"
            events_result = service.events().list(calendarId="primary", timeMin=now, maxResults=5, singleEvents=True, orderBy="startTime").execute()
            events = events_result.get("items", [])
            if not events: return {"status": "success", "message": "Your calendar is clear."}
            response_str = "Here are your next few events: "
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                friendly_time = format_datetime_for_speech(start)
                response_str += f"{event['summary']} {friendly_time}. "
            return {"status": "success", "message": response_str}
        except Exception as e:
            logger.error(f"Google Calendar API error: {e}")
            return {"status": "error", "message": "I couldn't fetch your calendar events."}

    def create_event(self, summary: str, start_time: str, end_time: str = None, attendees: str = None, **kwargs) -> dict:
        """Siri-like behavior: Creates an event and handles a missing end_time."""
        if not self.creds: return {"status": "error", "message": "Authentication failed."}
        
        try:
            service = build("calendar", "v3", credentials=self.creds)
            
            event_summary = summary
            if attendees and summary: event_summary = f"{summary} with {attendees}"
            elif attendees and not summary: event_summary = f"Meeting with {attendees}"

            # THE FIX: If end_time is missing, calculate a default 30-minute duration.
            if not end_time:
                start_dt = pendulum_parse(start_time)
                end_dt = start_dt.add(minutes=30)
                end_time = end_dt.to_iso8601_string()
                logger.info(f"End time not provided. Defaulting to {end_time}")

            event_body = {
                "summary": event_summary,
                "start": {"dateTime": start_time, "timeZone": "Asia/Dubai"},
                "end": {"dateTime": end_time, "timeZone": "Asia/Dubai"},
            }
            
            service.events().insert(calendarId="primary", body=event_body).execute()
            
            friendly_time = format_datetime_for_speech(start_time)
            return {"status": "success", "message": f"Done. I've scheduled '{event_summary}' for {friendly_time}."}
        
        except HttpError as e:
            logger.exception(f"Failed to create calendar event due to API error: {e}")
            return {"status": "error", "message": "I ran into a Google Calendar API error."}

calendar_service = CalendarService()