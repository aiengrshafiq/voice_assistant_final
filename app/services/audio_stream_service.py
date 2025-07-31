# app/services/audio_stream_service.py
import pyaudio
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

class AudioStreamService:
    """Manages the single, shared microphone stream using PyAudio."""
    def __init__(self, frame_length, sample_rate):
        self.frame_length = frame_length
        self.sample_rate = int(sample_rate)
        self._pa = pyaudio.PyAudio()
        self.stream = self._pa.open(
            rate=self.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=settings.MIC_DEVICE_INDEX,
            frames_per_buffer=self.frame_length,
        )
        logger.info("🎤 Central PyAudio Stream Initialized.")

    def read(self, num_frames):
        """Reads a chunk of audio data from the stream."""
        return self.stream.read(num_frames, exception_on_overflow=False)

    def release(self):
        """Stops and closes the audio stream."""
        if hasattr(self, 'stream') and self.stream.is_active():
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, '_pa'):
            self._pa.terminate()
        logger.info("🎤 Central PyAudio Stream Released.")