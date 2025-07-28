# app/services/calendar_service.py
import datetime as dt
import os.path
import humanize
from pendulum import parse as pendulum_parse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.core.logger import get_logger

logger = get_logger(__name__)
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def format_datetime_for_speech(iso_string):
    """Converts ISO datetime string to a human-friendly format."""
    if not iso_string: return "an unspecified time"
    try:
        dt_obj = pendulum_parse(iso_string)
        return humanize.naturaltime(dt_obj)
    except Exception:
        return "an unspecified time"

class CalendarService:
    def __init__(self):
        self.creds = self._get_credentials()

    def _get_credentials(self) -> Credentials | None:
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("Google Calendar token has expired. Refreshing...")
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh token: {e}. Re-authenticating.")
                    if os.path.exists("token.json"): os.remove("token.json")
                    return self._initiate_auth_flow()
            else:
                creds = self._initiate_auth_flow()
            if creds:
                with open("token.json", "w") as token:
                    token.write(creds.to_json())
                logger.info("Google Calendar token saved successfully.")
        return creds

    def _initiate_auth_flow(self) -> Credentials | None:
        if not os.path.exists("credentials.json"):
            logger.critical("FATAL: 'credentials.json' not found.")
            return None
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        return flow.run_local_server(port=0)

    def get_upcoming_events(self, count: int = 5) -> dict:
        if not self.creds:
            return {"status": "error", "message": "Calendar authentication failed."}
        try:
            service = build("calendar", "v3", credentials=self.creds)
            now = dt.datetime.utcnow().isoformat() + "Z"
            events_result = service.events().list(
                calendarId="primary", timeMin=now, maxResults=count,
                singleEvents=True, orderBy="startTime"
            ).execute()
            events = events_result.get("items", [])
            if not events:
                return {"status": "success", "message": "Your calendar is clear."}
            
            response_str = "Here are your next few events: "
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                friendly_time = format_datetime_for_speech(start)
                response_str += f"{event['summary']} {friendly_time}. "
            return {"status": "success", "message": response_str}
        except HttpError as error:
            logger.error(f"Google Calendar API error: {error}")
            return {"status": "error", "message": "I couldn't fetch your calendar events."}

    def create_event(self, summary: str, start_time: str, end_time: str, **kwargs) -> dict:
        """
        V3: Creates an event after checking for conflicts and returns a result dictionary.
        """
        if not self.creds:
            return {"status": "error", "message": "Authentication failed."}
        
        try:
            service = build("calendar", "v3", credentials=self.creds)

            # 1. Check for conflicting events
            events_result = service.events().list(
                calendarId='primary', timeMin=start_time, timeMax=end_time, singleEvents=True
            ).execute()
            conflicting_events = [e for e in events_result.get('items', []) if e.get('status') != 'cancelled']

            if conflicting_events:
                conflict = conflicting_events[0]
                conflict_summary = conflict['summary']
                conflict_time = format_datetime_for_speech(conflict['start'].get('dateTime'))
                message = f"Sir, that time conflicts with '{conflict_summary}' which is {conflict_time}. Should I schedule this new meeting anyway?"
                return {"status": "conflict", "message": message}

            # 2. No conflicts, create the event
            event_body = {
                "summary": summary,
                "start": {"dateTime": start_time, "timeZone": "Asia/Dubai"},
                "end": {"dateTime": end_time, "timeZone": "Asia/Dubai"},
            }
            created_event = service.events().insert(calendarId="primary", body=event_body).execute()
            logger.info(f"Event created: {created_event.get('htmlLink')}")
            
            # 3. Return a rich success message
            friendly_time = format_datetime_for_speech(start_time)
            return {
                "status": "success",
                "message": f"Done. I've scheduled '{summary}' for {friendly_time}."
            }
        except Exception as e:
            logger.exception(f"Failed to create calendar event: {e}")
            return {"status": "error", "message": "I ran into an API error while creating the event."}

calendar_service = CalendarService()