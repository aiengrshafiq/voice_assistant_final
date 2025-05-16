import pyttsx3
import subprocess
import os
from app.core.logger import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

engine = pyttsx3.init()
engine.setProperty('rate', 160)
engine.setProperty('volume', 1.0)

OUTPUT_FILE = "output.wav"

def speak(text: str):
    try:
        logger.info(f"Assistant: {text}")
        engine.save_to_file(text, OUTPUT_FILE)
        engine.runAndWait()

        # Play using specified speaker device
        #subprocess.run(["aplay", "-D", settings.SPEAKER_DEVICE, OUTPUT_FILE], check=True)
        subprocess.run(["paplay", "--device=" + settings.SPEAKER_DEVICE, OUTPUT_FILE], check=True)

    except subprocess.CalledProcessError as e:
        logger.error(f"Playback error: {e}")
    except Exception as e:
        logger.exception("Text-to-speech failed.")
