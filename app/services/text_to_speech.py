import pyttsx3
import subprocess
import os
import uuid
from gtts import gTTS
from app.core.logger import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

# Initialize pyttsx3
engine = pyttsx3.init()
engine.setProperty('rate', 160)
engine.setProperty('volume', 1.0)

PYTTSX3_OUTPUT = "output.wav"

def speak_pyttsx3(text: str):
    try:
        logger.info(f"[pyttsx3] Assistant: {text}")
        engine.save_to_file(text, PYTTSX3_OUTPUT)
        engine.runAndWait()
        subprocess.run(["paplay", "--device=" + settings.SPEAKER_DEVICE, PYTTSX3_OUTPUT], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"[pyttsx3] Playback error: {e}")
    except Exception as e:
        logger.exception("[pyttsx3] Text-to-speech failed.")

def speak_gtts(text: str):
    try:
        logger.info(f"[gTTS] Assistant: {text}")
        filename = f"/tmp/speak_{uuid.uuid4()}.mp3"
        tts = gTTS(text)
        tts.save(filename)
        subprocess.run(["ffplay", "-nodisp", "-autoexit", filename], check=True)
        os.remove(filename)
    except Exception as e:
        logger.warning("[gTTS] Failed. Falling back to pyttsx3.")
        speak_pyttsx3(text)  # Fallback on error

def speak(text: str):
    """Universal speak function with fallback from gTTS to pyttsx3."""
    if settings.TTS_ENGINE.lower() == "gtts":
        speak_gtts(text)
    else:
        speak_pyttsx3(text)




# import pyttsx3
# import subprocess
# import os
# from app.core.logger import get_logger
# from app.core.config import get_settings

# logger = get_logger(__name__)
# settings = get_settings()

# engine = pyttsx3.init()
# engine.setProperty('rate', 160)
# engine.setProperty('volume', 1.0)

# OUTPUT_FILE = "output.wav"

# def speak(text: str):
#     try:
#         logger.info(f"Assistant: {text}")
#         engine.save_to_file(text, OUTPUT_FILE)
#         engine.runAndWait()

#         # Play using specified speaker device
#         subprocess.run(["paplay", "--device=" + settings.SPEAKER_DEVICE, OUTPUT_FILE], check=True)
        

#     except subprocess.CalledProcessError as e:
#         logger.error(f"Playback error: {e}")
#     except Exception as e:
#         logger.exception("Text-to-speech failed.")
