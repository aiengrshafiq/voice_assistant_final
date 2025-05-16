import os
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.core.logger import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    creds = None
    token_path = "token.json"
    creds_path = settings.GOOGLE_CREDENTIALS_PATH

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    elif os.path.exists(creds_path):
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    if not creds or not creds.valid:
        logger.error("Google credentials are missing or invalid.")
        return None

    return build('calendar', 'v3', credentials=creds)

def get_todays_events():
    try:
        service = get_calendar_service()
        if not service:
            return "Unable to access calendar."

        now = datetime.datetime.utcnow().isoformat() + 'Z'
        end = (datetime.datetime.utcnow() + datetime.timedelta(hours=18)).isoformat() + 'Z'

        events_result = service.events().list(
            calendarId='primary', timeMin=now, timeMax=end,
            maxResults=10, singleEvents=True, orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if not events:
            return "You have no events scheduled for today."

        summaries = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            time_str = datetime.datetime.fromisoformat(start).strftime('%I:%M %p')
            summaries.append(f"{time_str} - {event['summary']}")

        return "Here's your schedule: " + "; ".join(summaries)

    except Exception as e:
        logger.exception("Failed to fetch calendar events.")
        return "There was a problem checking your calendar."

def add_event(summary: str, start_time: str, end_time: str):
    try:
        service = get_calendar_service()
        if not service:
            return "Unable to access calendar."

        event = {
            'summary': summary,
            'start': {'dateTime': start_time, 'timeZone': 'Asia/Dubai'},
            'end': {'dateTime': end_time, 'timeZone': 'Asia/Dubai'},
        }

        service.events().insert(calendarId='primary', body=event).execute()
        return "Event added to your calendar."

    except Exception as e:
        logger.exception("Failed to create calendar event.")
        return "There was a problem adding the event."
