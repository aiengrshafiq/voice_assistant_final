import json
import time
from pathlib import Path
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from thefuzz import process
from app.core.logger import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

class SlackService:
    """
    Service for interacting with the Slack API, featuring a robust,
    file-based local cache to prevent API rate-limiting.
    """
    
    def __init__(self):
        self.client = WebClient(token=settings.SLACK_BOT_TOKEN)
        self.cache_path = Path("slack_users.json")
        # --- Cache Time-To-Live set to one week (in seconds) ---
        self.cache_ttl_seconds = 7 * 24 * 60 * 60
        self._user_cache = self._load_users_from_cache()

    def _load_users_from_cache(self) -> dict:
        """
        Loads the user list from a local JSON file. If the file is missing
        or older than the TTL, it fetches a fresh list from the API.
        """
        if self.cache_path.exists():
            # Check if the cache file is within the one-week TTL
            if time.time() - self.cache_path.stat().st_mtime < self.cache_ttl_seconds:
                logger.info("Loading Slack users from fresh local cache.")
                with open(self.cache_path, 'r') as f:
                    return json.load(f)

        logger.info("Local Slack user cache is stale or missing. Fetching from API.")
        return self._fetch_and_save_users_from_api()

    def _fetch_and_save_users_from_api(self) -> dict:
        """Fetches the full user list from the Slack API and saves it to a local file."""
        if "YOUR_SLACK_BOT_TOKEN" in settings.SLACK_BOT_TOKEN:
            logger.warning("Slack token seems to be a placeholder. Skipping user fetch.")
            return {}
        
        try:
            logger.info("Priming Slack user cache from API...")
            response = self.client.users_list()
            user_map = {
                user['profile']['real_name_normalized']: user['id']
                for user in response['members']
                if not user.get('is_bot') and not user.get('deleted') and user['profile'].get('real_name_normalized')
            }
            # Save the new user list to the cache file
            with open(self.cache_path, 'w') as f:
                json.dump(user_map, f)
            logger.info(f"Successfully cached {len(user_map)} Slack users to {self.cache_path}.")
            return user_map
        except SlackApiError as e:
            # Handle rate limiting gracefully by using the old cache if it exists
            if e.response.get("error") == "ratelimited":
                logger.error("Slack API rate limit hit. Will use stale cache if available, or fail gracefully.")
                if self.cache_path.exists():
                    with open(self.cache_path, 'r') as f:
                        return json.load(f)
            else:
                 logger.error(f"Failed to fetch Slack users for cache: {e.response['error']}")
            return {} # Return empty dict on critical failure

    def summon_person(self, target_name: str) -> str:
        """Finds a user with fuzzy matching and sends them a DM using the robust conversations.open method."""
        if not self._user_cache:
            return "I'm sorry, I couldn't access the Slack user list. Please check the connection."

        best_match = process.extractOne(target_name, self._user_cache.keys(), score_cutoff=80)

        if not best_match:
            logger.warning(f"Could not find a confident match for '{target_name}' in Slack.")
            return f"I couldn't find anyone named '{target_name}' on Slack. Should I try a different name?"

        matched_name, score = best_match
        user_id = self._user_cache[matched_name]
        logger.info(f"Found match for '{target_name}': '{matched_name}' (Score: {score}) with ID: {user_id}")

        try:
            # Step 1: Open a direct message channel with the user
            logger.info(f"Opening DM channel with user {user_id}...")
            conversation_response = self.client.conversations_open(users=user_id)
            if not conversation_response["ok"]:
                error_reason = conversation_response.get("error", "unknown error")
                logger.error(f"Failed to open DM channel with {user_id}: {error_reason}")
                return f"I found {matched_name}, but couldn't open a direct message with them."
            
            channel_id = conversation_response["channel"]["id"]
            logger.info(f"Successfully opened DM channel: {channel_id}")

            # Step 2: Post the message to the newly opened channel with a mention
            message = f"Hi <@{user_id}>, the CEO is requesting your presence in the office."
            logger.info(f"Attempting to send Slack DM to channel ID: {channel_id}")
            message_response = self.client.chat_postMessage(
                channel=channel_id, 
                text=message,
                link_names=True
            )
            
            if message_response["ok"]:
                logger.info("✅ Slack message sent successfully to DM channel.")
                return f"Okay, I've sent a message to {matched_name} on Slack."
            else:
                error_reason = message_response.get("error", "unknown_error")
                logger.error(f"Slack API returned an error on chat.postMessage: '{error_reason}'")
                return f"I found {matched_name}, but I ran into a Slack error: {error_reason.replace('_', ' ')}."

        except SlackApiError as e:
            logger.error(f"A SlackApiError occurred: {e.response['error']}")
            return f"I ran into a Slack API error while trying to send the message: {e.response['error'].replace('_', ' ')}"
        except Exception as e:
            logger.exception(f"An unexpected error occurred in summon_person: {e}")
            return "An unexpected error occurred while trying to contact Slack."

# Create a single instance of the service to be imported by other modules
slack_service = SlackService()