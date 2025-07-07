import simpleaudio as sa
from pathlib import Path
import threading
from app.services.text_to_speech import speak
from app.core.logger import get_logger

logger = get_logger(__name__)

class FeedbackManager:
    """Manages all audio feedback for the assistant (sounds and speech)."""

    def __init__(self):
        self.sounds_path = Path(__file__).parent.parent.parent / "resources" / "sounds"
        self._acknowledge_sound_path = self.sounds_path / "acknowledge.wav"
        self._error_sound_path = self.sounds_path / "error.wav"

    def _play_sound(self, sound_path: Path):
        """Plays a sound file using simpleaudio in a non-blocking thread."""
        if not sound_path.exists():
            logger.warning(f"Sound file not found: {sound_path}. Cannot play sound.")
            return
        
        def play_task():
            try:
                wave_obj = sa.WaveObject.from_wave_file(str(sound_path))
                play_obj = wave_obj.play()
                play_obj.wait_done()
            except Exception as e:
                logger.error(f"Could not play sound {sound_path} with simpleaudio: {e}")

        # Run playback in a separate thread so it doesn't block the main application
        thread = threading.Thread(target=play_task)
        thread.start()

    def acknowledge(self):
        """Plays a simple, non-verbal acknowledgement sound."""
        logger.info("[Feedback] Acknowledging with a chime.")
        self._play_sound(self._acknowledge_sound_path)

    def confirm(self, text: str):
        """Speaks a confirmation message."""
        logger.info(f"[Feedback] Confirming with voice: '{text}'")
        speak(text)

    def error(self, text: str = "An error occurred."):
        """Plays an error sound and speaks an error message."""
        logger.info(f"[Feedback] Reporting error with sound and voice: '{text}'")
        self._play_sound(self._error_sound_path)
        speak(text)
    
    def success(self, text: str):
        """Speaks a success message."""
        logger.info(f"[Feedback] Reporting success with voice: '{text}'")
        speak(text)

# Create a single, global instance
feedback = FeedbackManager()