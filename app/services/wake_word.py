# app/services/wake_word.py
import os
import struct
import pvporcupine
from app.core.config import get_settings
from app.core.logger import get_logger
from app.services.audio_stream_service import AudioStreamService

logger = get_logger(__name__)
settings = get_settings()

class WakeWordEngine:
    def __init__(self, audio_stream: AudioStreamService):
        try:
            keyword_path = os.path.join("models", "porcupine", f"{settings.WAKE_WORD}_raspberry-pi.ppn")
            self._porcupine = pvporcupine.create(
                access_key=settings.PORCUPINE_ACCESS_KEY,
                keyword_paths=[os.path.abspath(keyword_path)],
                sensitivities=[0.6]  # Adjust sensitivity as needed
            )
            self.audio_stream = audio_stream
            logger.info("✅ Porcupine Engine initialized.")
        except Exception as e:
            logger.exception(f"Failed to initialize Porcupine Engine: {e}")
            raise

    def listen(self):
        logger.info(f"Listening for wake word '{settings.WAKE_WORD}'...")
        while True:
            pcm_data = self.audio_stream.read(self._porcupine.frame_length)
            if len(pcm_data) == self._porcupine.frame_length * 2:
                pcm = struct.unpack_from("h" * self._porcupine.frame_length, pcm_data)
                if self._porcupine.process(pcm) >= 0:
                    logger.info("Wake word detected!")
                    return

    def release(self):
        if self._porcupine:
            self._porcupine.delete()