import datetime as dt
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.core.logger import get_logger

logger = get_logger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

class CalendarService:
    """Service for interacting with the Google Calendar API."""

    def __init__(self):
        self.creds = self._get_credentials()

    def _get_credentials(self) -> Credentials | None:
        """
        Handles the OAuth2 flow to get valid user credentials.
        If a 'token.json' exists, it's loaded. Otherwise, it initiates
        a browser-based authentication flow and saves the new token.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens.
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("Google Calendar token has expired. Refreshing...")
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh token: {e}. Please re-authenticate.")
                    os.remove("token.json") # Remove bad token
                    return self._initiate_auth_flow()
            else:
                logger.info("No valid Google Calendar token found. Initiating authentication.")
                creds = self._initiate_auth_flow()
            
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())
            logger.info("Google Calendar token has been saved successfully.")
        
        return creds

    def _initiate_auth_flow(self) -> Credentials | None:
        """Runs the interactive console-based auth flow."""
        if not os.path.exists("credentials.json"):
            logger.critical("FATAL: 'credentials.json' not found. Cannot authenticate with Google Calendar.")
            return None
            
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        # The user will be prompted to open a URL in their browser and paste back a code.
        creds = flow.run_local_server(port=0) 
        return creds

    def get_upcoming_events(self, count: int = 5) -> str:
        """Gets the next 'count' events from the primary calendar."""
        if not self.creds:
            return "I'm sorry, I couldn't access the calendar due to an authentication issue."
            
        try:
            service = build("calendar", "v3", credentials=self.creds)
            now = dt.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
            
            logger.info(f"Fetching next {count} upcoming events.")
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=count,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

            if not events:
                return "You have no upcoming events."

            response_str = "Here are your next few events: "
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                # You can format the date/time here to be more user-friendly
                response_str += f"{event['summary']} at {start}. "
            return response_str

        except HttpError as error:
            logger.error(f"An error occurred with Google Calendar API: {error}")
            return "Sorry, I ran into an error trying to fetch your calendar events."

    def create_event(self, summary: str, start_time: str, end_time: str, description: str | None = None) -> str:
        """Creates a new event on the primary calendar."""
        if not self.creds:
            return "I'm sorry, I couldn't create the event due to an authentication issue."

        try:
            service = build("calendar", "v3", credentials=self.creds)
            event = {
                "summary": summary,
                "description": description,
                "start": {"dateTime": start_time, "timeZone": "Asia/Dubai"}, # Set to your CEO's timezone
                "end": {"dateTime": end_time, "timeZone": "Asia/Dubai"},
            }
            
            logger.info(f"Creating calendar event: {summary}")
            created_event = service.events().insert(calendarId="primary", body=event).execute()
            logger.info(f"Event created successfully: {created_event.get('htmlLink')}")
            
            return f"Okay, I've scheduled '{summary}' on your calendar."

        except Exception as e:
            logger.exception(f"Failed to create calendar event: {e}")
            return "I'm sorry, I was unable to create that calendar event."

# Create a single instance
calendar_service = CalendarService()