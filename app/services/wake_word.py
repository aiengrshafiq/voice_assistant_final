import os
import struct
import pvporcupine
import pyaudio
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

class WakeWordEngine:
    """A class to manage the Porcupine wake word engine lifecycle."""

    def __init__(self):
        self._porcupine = None
        self._pa = None
        self._stream = None
        try:
            logger.info("Initializing Porcupine Wake Word Engine...")
            keyword_path = os.path.join(
                os.path.dirname(__file__),
                "..", "..", "models", "porcupine", f"{settings.WAKE_WORD}_raspberry-pi.ppn"
            )

            if not os.path.exists(keyword_path):
                 # Added a check for the custom model file
                 logger.error(f"Wake word model file not found at {keyword_path}")
                 raise FileNotFoundError(f"Could not find a .ppn file for wake word '{settings.WAKE_WORD}'")

            # This initialization now happens only once.
            self._porcupine = pvporcupine.create(
                access_key=settings.PORCUPINE_ACCESS_KEY,
                keyword_paths=[os.path.abspath(keyword_path)]
            )
            
            self._pa = pyaudio.PyAudio()
            self._stream = self._pa.open(
                rate=self._porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                input_device_index=settings.MIC_DEVICE_INDEX,
                frames_per_buffer=self._porcupine.frame_length,
            )
            logger.info("✅ Porcupine Engine initialized successfully.")

        except Exception as e:
            logger.exception(f"Failed to initialize Porcupine Engine: {e}")
            # Re-raise the exception to stop the application from starting in a bad state
            raise

    def listen(self):
        """
        Listens for a single utterance of the wake word from the audio stream.
        This is a blocking function.
        """
        if not all([self._porcupine, self._pa, self._stream]):
            logger.error("Wake Word Engine is not initialized. Cannot listen.")
            return

        logger.info(f"Listening for wake word '{settings.WAKE_WORD}'...")
        while True:
            pcm = self._stream.read(self._porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * self._porcupine.frame_length, pcm)
            result = self._porcupine.process(pcm)

            if result >= 0:
                logger.info("Wake word detected!")
                return # Exit the function upon detection

    def release(self):
        """Releases all resources used by the engine."""
        logger.info("Releasing Porcupine Engine resources...")
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        if self._pa:
            self._pa.terminate()
        if self._porcupine:
            self._porcupine.delete()
        logger.info("Porcupine resources released.")