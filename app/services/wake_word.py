import os
import struct
import pvporcupine
import pyaudio
from app.core.config import get_settings
from app.core.logger import get_logger


logger = get_logger(__name__)
settings = get_settings()

def listen_for_wake_word(callback):
    keyword_path = os.path.join(
        os.path.dirname(__file__),
        "..", "..", "models", "porcupine", "jarvis_raspberry-pi.ppn"
    )

    porcupine = pvporcupine.create(
        access_key=settings.PORCUPINE_ACCESS_KEY,
        keyword_paths=[os.path.abspath(keyword_path)]
    )

    pa = pyaudio.PyAudio()

    logger.info("Listening for wake word 'Jarvis'...")

    try:
        while True:
            stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                input_device_index=settings.MIC_DEVICE_INDEX,
                frames_per_buffer=porcupine.frame_length,
            )

            try:
                while True:
                    pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
                    pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
                    result = porcupine.process(pcm)

                    if result >= 0:
                        logger.info("Wake word detected!")
                        stream.stop_stream()
                        stream.close()
                        callback()
                        import time
                        time.sleep(0.5)
                        logger.info("Returned from callback. Restarting wake word listener...")
                        break

            except Exception as e:
                logger.exception(f"Error in stream loop: {e}")
                stream.stop_stream()
                stream.close()

    except KeyboardInterrupt:
        logger.warning("Wake word listener interrupted.")

    finally:
        pa.terminate()
        porcupine.delete()
