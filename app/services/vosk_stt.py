# app/services/vosk_stt.py
import os
import queue
import sounddevice as sd
import json
from vosk import Model, KaldiRecognizer
from app.core.logger import get_logger
from app.core.config import get_settings
import time
import traceback

logger = get_logger(__name__)
settings = get_settings()

samplerate = 16000
blocksize = 8000
channels = 1
dtype = 'int16'
q = queue.Queue()

# Load Vosk model
model_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "models", "vosk-model-small-en-us-0.15"
)
model = Model(model_path)

def callback(indata, frames, time, status):
    if status:
        logger.warning(f"SoundDevice status: {status}")
    q.put(bytes(indata))

def get_input_device_index(preferred_index):
    try:
        dev = sd.query_devices(preferred_index, 'input')
        logger.info(f"Using preferred input device {preferred_index}: {dev['name']}")
        return preferred_index
    except Exception as e:
        logger.warning(f"Configured input device failed: {e}")
        # fallback to first valid device
        for i, d in enumerate(sd.query_devices()):
            if d['max_input_channels'] > 0:
                logger.info(f"Fallback to device {i}: {d['name']}")
                return i
        raise RuntimeError("No valid input device found.")

def listen_yes_no(timeout=5):
    try:
        device_index = get_input_device_index(settings.MIC_DEVICE_INDEX)
        sd._terminate()  # Force reset if stuck
        sd._initialize()
        with sd.RawInputStream(
            samplerate=samplerate,
            blocksize=blocksize,
            dtype=dtype,
            channels=channels,
            callback=callback,
            device=device_index
        ):
            rec = KaldiRecognizer(model, samplerate)
            logger.info("🎤 Listening for yes/no (Vosk)...")
            for _ in range(int(timeout * 1000 / 50)):
                try:
                    data = q.get(timeout=1)
                except queue.Empty:
                    logger.warning("No audio input received (queue empty).")
                    continue
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").strip().lower()
                    if text:
                        logger.info(f"Vosk recognized: '{text}'")
                        return text
                time.sleep(0.01)
    except Exception as e:
        logger.error(f"Vosk STT failed: {str(e)}")
        logger.debug(traceback.format_exc())
    return ""
