from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from thefuzz import process
from app.core.logger import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

class SlackService:
    """Service for interacting with the Slack API."""
    
    def __init__(self):
        self.client = WebClient(token=settings.SLACK_BOT_TOKEN)
        self._user_cache = None
        if "YOUR_SLACK_BOT_TOKEN" in settings.SLACK_BOT_TOKEN:
            logger.warning("Slack token seems to be a placeholder. The service may not work.")
        else:
            self._prime_user_cache()

    def _prime_user_cache(self):
        """Fetches and caches the list of users from Slack."""
        logger.info("Priming Slack user cache...")
        try:
            response = self.client.users_list()
            # Create a mapping of display names to user IDs for non-bot, non-deleted users
            self._user_cache = {
                user['profile']['real_name_normalized']: user['id']
                for user in response['members']
                if not user.get('is_bot') and not user.get('deleted') and user['profile'].get('real_name_normalized')
            }
            logger.info(f"Successfully cached {len(self._user_cache)} Slack users.")
        except SlackApiError as e:
            logger.error(f"Failed to fetch Slack users for cache: {e.response['error']}")
            self._user_cache = {} # Ensure cache is not None


    def summon_person(self, target_name: str) -> str:
        """Finds a user with fuzzy matching and sends them a DM."""
        if not self._user_cache:
            return "I'm sorry, I couldn't connect to Slack to find any users."

        best_match = process.extractOne(target_name, self._user_cache.keys(), score_cutoff=80)

        if not best_match:
            logger.warning(f"Could not find a confident match for '{target_name}' in Slack.")
            return f"I couldn't find anyone named '{target_name}' on Slack. Should I try a different name?"

        matched_name, score = best_match
        user_id = self._user_cache[matched_name]
        logger.info(f"Found match for '{target_name}': '{matched_name}' (Score: {score}) with ID: {user_id}")

        try:
            #message = f"Hi {matched_name.split()[0]}, the CEO is requesting your presence in the office."
            message = f"Hi <@{user_id}>, the CEO is requesting your presence in the office."
            logger.info(f"Attempting to send Slack DM to user ID: {user_id}")

            # --- THE FIX: Changed from .chat.postMessage to .chat_postMessage ---
            response = self.client.chat_postMessage(channel=user_id, text=message,link_names=True)
            
            if response["ok"]:
                logger.info("✅ Slack message sent successfully.")
                return f"Okay, I've sent a message to {matched_name} on Slack."
            else:
                error_reason = response.get("error", "unknown_error")
                logger.error(f"Slack API returned an error: '{error_reason}'")
                return f"I found {matched_name}, but I ran into a Slack error: {error_reason.replace('_', ' ')}."

        except SlackApiError as e:
            logger.error(f"A SlackApiError occurred when sending DM to {user_id}: {e.response['error']}")
            return f"I found {matched_name}, but I ran into an API error while trying to send the message."
        except Exception as e:
            logger.exception(f"An unexpected error occurred in summon_person: {e}")
            return "An unexpected error occurred while trying to contact Slack."

# Create a single instance of the service
slack_service = SlackService()