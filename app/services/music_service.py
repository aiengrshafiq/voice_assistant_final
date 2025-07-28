# app/services/music_service.py
import requests
from app.core.logger import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

MUSIC_ASSISTANT_PLAYER_ID = "media_player.music_assistant_office_apple_tv"

class MusicService:
    """V3: Service for controlling music via Music Assistant."""

    def __init__(self):
        self.base_url = settings.HOME_ASSISTANT_URL
        self.headers = {
            "Authorization": f"Bearer {settings.HOME_ASSISTANT_TOKEN}",
            "Content-Type": "application/json",
        }

    def _call_service(self, domain: str, service: str, service_data: dict) -> bool:
        api_url = f"{self.base_url}/api/services/{domain}/{service}"
        try:
            response = requests.post(api_url, headers=self.headers, json=service_data, timeout=10)
            response.raise_for_status()
            logger.info(f"Successfully called HA music service '{domain}.{service}'")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call Home Assistant API for music: {e}")
            return False

    def play_music(self, song_name: str = None, playlist_name: str = None, **kwargs) -> dict:
        """Plays a song or playlist by name."""
        if song_name:
            media_type = "track"
            media_id = song_name
            friendly_name = song_name
        elif playlist_name:
            media_type = "playlist"
            media_id = playlist_name
            friendly_name = f"the {playlist_name} playlist"
        else:
            return {"status": "failed", "message": "You need to specify a song or playlist."}

        logger.info(f"Attempting to play {media_type} '{media_id}'")
        service_data = {
            "entity_id": MUSIC_ASSISTANT_PLAYER_ID,
            "media_content_id": f"library://{media_type}/{media_id}",
            "media_content_type": media_type,
        }
        if self._call_service("media_player", "play_media", service_data):
            return {"status": "success", "message": f"Okay, playing {friendly_name}."}
        else:
            return {"status": "error", "message": f"I had trouble playing {friendly_name}."}

    def stop_music(self, **kwargs) -> dict:
        """Stops playback."""
        if self._call_service("media_player", "media_stop", {"entity_id": MUSIC_ASSISTANT_PLAYER_ID}):
            return {"status": "success", "message": "Okay."}
        else:
            return {"status": "error", "message": "I couldn't stop the music."}

    def pause(self, **kwargs) -> dict:
        """Pauses playback."""
        if self._call_service("media_player", "media_pause", {"entity_id": MUSIC_ASSISTANT_PLAYER_ID}):
            return {"status": "success", "message": "Paused."}
        else:
            return {"status": "error", "message": "I couldn't pause the music."}

    def resume(self, **kwargs) -> dict:
        """Resumes playback."""
        if self._call_service("media_player", "media_play", {"entity_id": MUSIC_ASSISTANT_PLAYER_ID}):
            return {"status": "success", "message": "Resuming."}
        else:
            return {"status": "error", "message": "I couldn't resume the music."}

music_service = MusicService()