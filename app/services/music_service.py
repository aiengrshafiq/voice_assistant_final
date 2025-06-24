import requests
from app.core.logger import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

# --- MUSIC CONFIGURATION ---
MUSIC_ASSISTANT_PLAYER_ID = "media_player.music_assistant_office_apple_tv" # <-- CONFIRM THIS ID
# ---

class MusicService:
    """Service for controlling music playback via the Music Assistant integration."""

    def __init__(self):
        self.base_url = settings.HOME_ASSISTANT_URL
        self.headers = {
            "Authorization": f"Bearer {settings.HOME_ASSISTANT_TOKEN}",
            "Content-Type": "application/json",
        }

    def _call_service(self, domain: str, service: str, service_data: dict) -> bool:
        """Helper to make a generic service call to Home Assistant."""
        api_url = f"{self.base_url}/api/services/{domain}/{service}"
        try:
            response = requests.post(api_url, headers=self.headers, json=service_data, timeout=10)
            response.raise_for_status()
            logger.info(f"Successfully called HA service '{domain}.{service}' with data: {service_data}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call Home Assistant API: {e}")
            return False

    def play_playlist(self, playlist_name: str) -> str:
        """Tells Music Assistant to play a specific Apple Music playlist by name."""
        clean_playlist_name = playlist_name.replace("my ", "").strip()
        logger.info(f"Attempting to play playlist '{clean_playlist_name}' on '{MUSIC_ASSISTANT_PLAYER_ID}'")
        service_data = {
            "entity_id": MUSIC_ASSISTANT_PLAYER_ID,
            "media_content_id": f"library://playlist/{clean_playlist_name}",
            "media_content_type": "playlist",
        }
        if self._call_service("media_player", "play_media", service_data):
            return f"Okay, playing your {clean_playlist_name} playlist."
        else:
            return f"I had trouble sending the play command to Music Assistant for the playlist {clean_playlist_name}."

    # --- NEW FUNCTION ---
    def play_song(self, song_title: str) -> str:
        """Tells Music Assistant to play a specific song by title."""
        logger.info(f"Attempting to play song '{song_title}' on '{MUSIC_ASSISTANT_PLAYER_ID}'")
        
        # This URI format tells Music Assistant to search its library for a matching track.
        service_data = {
            "entity_id": MUSIC_ASSISTANT_PLAYER_ID,
            "media_content_id": f"library://track/{song_title}",
            "media_content_type": "track",
        }
        if self._call_service("media_player", "play_media", service_data):
            return f"Now playing {song_title}."
        else:
            return f"I'm sorry, I had trouble playing the song {song_title}."

    # --- NEW FUNCTION ---
    def stop_music(self) -> str:
        """Stops any playback on the Music Assistant player."""
        logger.info(f"Attempting to stop playback on '{MUSIC_ASSISTANT_PLAYER_ID}'")
        if self._call_service("media_player", "media_stop", {"entity_id": MUSIC_ASSISTANT_PLAYER_ID}):
            return "Playback stopped."
        else:
            return "Sorry, I couldn't stop the music."

    def pause(self) -> str:
        """Pauses the Music Assistant player."""
        if self._call_service("media_player", "media_pause", {"entity_id": MUSIC_ASSISTANT_PLAYER_ID}):
            return "Playback paused."
        else:
            return "Sorry, I couldn't pause the music."

    def resume(self) -> str:
        """Resumes the Music Assistant player."""
        if self._call_service("media_player", "media_play", {"entity_id": MUSIC_ASSISTANT_PLAYER_ID}):
            return "Resuming playback."
        else:
            return "Sorry, I couldn't resume the music."

# Create a single instance of the service
music_service = MusicService()