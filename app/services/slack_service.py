# app/services/slack_service.py
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
    def __init__(self):
        self.client = WebClient(token=settings.SLACK_BOT_TOKEN)
        self.cache_path = Path("slack_users.json")
        self.cache_ttl_seconds = 7 * 24 * 60 * 60 # One week
        self._user_cache = self._load_users_from_cache()

    def _load_users_from_cache(self) -> dict:
        # This internal logic can remain the same
        if self.cache_path.exists():
            if time.time() - self.cache_path.stat().st_mtime < self.cache_ttl_seconds:
                with open(self.cache_path, 'r') as f: return json.load(f)
        return self._fetch_and_save_users_from_api()

    def _fetch_and_save_users_from_api(self) -> dict:
        # This internal logic can remain the same
        if "YOUR_SLACK_BOT_TOKEN" in settings.SLACK_BOT_TOKEN:
            logger.warning("Slack token is a placeholder. Skipping user fetch.")
            return {}
        try:
            response = self.client.users_list()
            user_map = {
                user['profile']['real_name_normalized']: user['id']
                for user in response['members']
                if not user.get('is_bot') and not user.get('deleted') and user['profile'].get('real_name_normalized')
            }
            with open(self.cache_path, 'w') as f: json.dump(user_map, f)
            logger.info(f"Successfully cached {len(user_map)} Slack users.")
            return user_map
        except SlackApiError as e:
            logger.error(f"Failed to fetch Slack users for cache: {e.response['error']}")
            return {}

    def summon_person(self, person_name: str, **kwargs) -> dict:
        """V3: Finds a user and sends a DM, returning a standardized dictionary."""
        if not self._user_cache:
            return {"status": "error", "message": "I couldn't access the Slack user list."}

        best_match = process.extractOne(person_name, self._user_cache.keys(), score_cutoff=80)
        if not best_match:
            logger.warning(f"No confident match for '{person_name}' in Slack.")
            return {"status": "failed", "message": f"I couldn't find anyone named '{person_name}' on Slack."}

        matched_name, user_id = best_match[0], self._user_cache[best_match[0]]
        logger.info(f"Found match for '{person_name}': '{matched_name}' with ID: {user_id}")

        try:
            conv_response = self.client.conversations_open(users=user_id)
            channel_id = conv_response["channel"]["id"]
            
            message = f"Hi <@{user_id}>, the CEO is requesting your presence in the office."
            self.client.chat_postMessage(channel=channel_id, text=message)
            
            logger.info("✅ Slack message sent successfully.")
            return {"status": "success", "message": f"Okay, I've sent a message to {matched_name} on Slack."}
        
        except SlackApiError as e:
            error_msg = e.response['error'].replace('_', ' ')
            logger.error(f"A SlackApiError occurred: {error_msg}")
            return {"status": "error", "message": f"I ran into a Slack API error: {error_msg}"}
        except Exception as e:
            logger.exception(f"Unexpected error in summon_person: {e}")
            return {"status": "error", "message": "An unexpected error occurred with Slack."}

slack_service = SlackService()