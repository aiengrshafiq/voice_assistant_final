from playsound import playsound
from pathlib import Path
from app.services.text_to_speech import speak
from app.core.logger import get_logger

logger = get_logger(__name__)

class FeedbackManager:
    """Manages all audio feedback for the assistant (sounds and speech)."""

    def __init__(self):
        self.sounds_path = Path(__file__).parent.parent.parent / "resources" / "sounds"
        self._acknowledge_sound = self.sounds_path / "acknowledge.wav"
        self._error_sound = self.sounds_path / "error.wav"

    def _play_sound(self, sound_path: Path):
        """Plays a sound file if it exists."""
        if not sound_path.exists():
            logger.warning(f"Sound file not found: {sound_path}. Cannot play sound.")
            return
        try:
            # Using block=False to make it non-blocking so the assistant can continue
            playsound(str(sound_path), block=False)
        except Exception as e:
            logger.error(f"Could not play sound {sound_path}: {e}")

    def acknowledge(self):
        """Plays a simple, non-verbal acknowledgement sound. Used for high-confidence actions."""
        logger.info("[Feedback] Acknowledging with a chime.")
        self._play_sound(self._acknowledge_sound)

    def confirm(self, text: str):
        """Speaks a confirmation message. Used when user confirmation is needed."""
        logger.info(f"[Feedback] Confirming with voice: '{text}'")
        speak(text)

    def error(self, text: str = "An error occurred."):
        """Plays an error sound and speaks an error message."""
        logger.info(f"[Feedback] Reporting error with sound and voice: '{text}'")
        self._play_sound(self._error_sound)
        speak(text)
    
    def success(self, text: str):
        """Speaks a success message."""
        logger.info(f"[Feedback] Reporting success with voice: '{text}'")
        speak(text)

# Create a single, global instance to be used across the application
feedback = FeedbackManager()