# File: app/services/speech_to_text.py

import speech_recognition as sr
import logging
#from app.core import settings  # adjust import if needed
from app.core.config import get_settings
settings = get_settings()

def listen_command():
    recognizer = sr.Recognizer()
    device_index = settings.MIC_DEVICE_INDEX

    try:
        with sr.Microphone(device_index=device_index) as source:
            logging.info("Listening for voice command...")
            recognizer.adjust_for_ambient_noise(source)
            #audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            except sr.WaitTimeoutError:
                print("Listening timed out while waiting for phrase to start")
                return None
            
    except AssertionError as ae:
        logging.error(f"Mic setup error: {ae}")
        return ""
    except Exception as e:
        logging.error(f"Unexpected error during STT recording: {e}")
        return ""

    try:
        logging.info("Converting speech to text...")
        text = recognizer.recognize_google(audio)
        logging.info(f"Recognized: {text}")
        return text
    except sr.UnknownValueError:
        logging.warning("Could not understand the audio.")
    except sr.RequestError as e:
        logging.error(f"Speech recognition service error: {e}")

    return ""
