# app/services/wake_word.py
import os
import struct
import pvporcupine
import pyaudio
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

class WakeWordEngine:
    """Manages Porcupine with its own dedicated audio stream."""
    def __init__(self):
        try:
            keyword_path = os.path.join("models", "porcupine", f"{settings.WAKE_WORD}_raspberry-pi.ppn")
            self._porcupine = pvporcupine.create(
                access_key=settings.PORCUPINE_ACCESS_KEY,
                keyword_paths=[os.path.abspath(keyword_path)],
                sensitivities=[0.4]
            )
            self._pa = pyaudio.PyAudio()
            self._stream = self._pa.open(
                rate=self._porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                input_device_index=settings.MIC_DEVICE_INDEX,
                frames_per_buffer=self._porcupine.frame_length
            )
            logger.info("✅ Porcupine Engine initialized.")
        except Exception as e:
            logger.exception(f"Failed to initialize Porcupine Engine: {e}")
            raise

    def listen(self):
        logger.info(f"Listening for wake word '{settings.WAKE_WORD}'...")
        while True:
            pcm_data = self._stream.read(self._porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * self._porcupine.frame_length, pcm_data)
            result = self._porcupine.process(pcm)
            if result >= 0:
                logger.info("Wake word detected!")
                return

    def release(self):
        if hasattr(self, '_stream') and self._stream is not None:
            self._stream.stop_stream(); self._stream.close()
        if hasattr(self, '_pa') and self._pa is not None:
            self._pa.terminate()
        if hasattr(self, '_porcupine') and self._porcupine is not None:
            self._porcupine.delete()