# File: app/services/speech_to_text.py

import speech_recognition as sr
import numpy as np
from app.core.logger import get_logger
from app.core.config import get_settings
from app.services.feedback_manager import feedback

# --- Setup ---
settings = get_settings()
logger = get_logger(__name__)

# This sample rate is optimal for Resemblyzer and many STT engines.
SAMPLE_RATE = 16000

# --- CONSTANTS ---
RETRY_ATTEMPTS = 2 # The initial try + 1 retry

def _capture_audio(recognizer: sr.Recognizer, source: sr.Microphone, timeout: int | None, phrase_time_limit: int | None) -> sr.AudioData | None:
    """
    A helper function to capture audio from the microphone with proper error handling.

    Args:
        recognizer: The SpeechRecognition recognizer instance.
        source: The microphone audio source.
        timeout: How long to wait for a phrase to start.
        phrase_time_limit: The maximum length of a phrase.

    Returns:
        An AudioData object if successful, otherwise None.
    """
    logger.info("🎤 Adjusting for ambient noise...")
    recognizer.adjust_for_ambient_noise(source, duration=0.5)
    logger.info("🎤 Listening...")

    try:
        return recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
    except sr.WaitTimeoutError:
        logger.warning("⏱️  Listening timed out while waiting for phrase to start.")
        return None
    except Exception as e:
        logger.exception(f"❌ An unexpected error occurred during audio capture: {e}")
        return None

def listen_for_verification(duration: int = 3) -> np.ndarray | None:
    """
    Records audio from the microphone for a fixed duration for voice verification.
    This function does NOT perform speech-to-text.

    Args:
        duration (int): The number of seconds to record.

    Returns:
        A numpy array of the audio waveform, normalized for Resemblyzer.
        Returns None if no audio could be captured.
    """
    recognizer = sr.Recognizer()
    microphone = sr.Microphone(device_index=settings.MIC_DEVICE_INDEX, sample_rate=SAMPLE_RATE)

    with microphone as source:
        logger.info(f"Capturing {duration}s of audio for voice verification...")
        
        # We use listen's timeout and phrase_time_limit to enforce the duration
        audio_data = _capture_audio(recognizer, source, timeout=duration, phrase_time_limit=duration)

    if not audio_data:
        logger.error("Verification failed: No audio was captured.")
        return None

    try:
        # Convert the raw audio data to a numpy array
        raw_data = audio_data.get_raw_data(convert_rate=SAMPLE_RATE, convert_width=2)
        audio_array = np.frombuffer(raw_data, dtype=np.int16)

        # Normalize the audio to floating point values between -1 and 1, as required by Resemblyzer
        return audio_array.astype(np.float32) / 32768.0
    except Exception as e:
        logger.exception(f"❌ Failed to process audio data for verification: {e}")
        return None
        
def listen_command(timeout: int = 5, phrase_time_limit: int = 10) -> str | None:
    """
    Listens for a voice command with retry logic and converts it to text.
    """
    recognizer = sr.Recognizer()
    microphone = sr.Microphone(device_index=settings.MIC_DEVICE_INDEX, sample_rate=SAMPLE_RATE)

    for attempt in range(RETRY_ATTEMPTS):
        with microphone as source:
            if attempt > 0:
                feedback.confirm("I'm sorry, I didn't hear anything. Please say that again.")
            
            # --- THE FIX: Pass the arguments to the capture function ---
            audio_data = _capture_audio(recognizer, source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        if not audio_data:
            continue
        
        # ... (the rest of the function is exactly the same) ...
        try:
            logger.info("🧠 Converting speech to text via Google STT...")
            text = recognizer.recognize_google(audio_data, language=settings.USER_LANGUAGE)
            logger.info(f"✅ Recognized: '{text}'")
            return text.lower()
        except sr.UnknownValueError:
            logger.warning("🤷 Google STT could not understand the audio.")
        except sr.RequestError as e:
            logger.error(f"🚨 Could not request results from Google STT service; {e}")
            feedback.error("I'm having trouble connecting to the speech service.")
            return None
        except Exception as e:
            logger.exception(f"❌ An unexpected error occurred during speech-to-text conversion: {e}")
            return None
    
    logger.warning("All STT retry attempts failed.")
    return None
# def listen_command() -> str | None:
#     """
#     Listens for a voice command with retry logic and converts it to text.
#     """
#     recognizer = sr.Recognizer()
#     microphone = sr.Microphone(device_index=settings.MIC_DEVICE_INDEX, sample_rate=SAMPLE_RATE)

#     for attempt in range(RETRY_ATTEMPTS):
#         with microphone as source:
#             # On retry, give a prompt
#             if attempt > 0:
#                 feedback.confirm("I'm sorry, I didn't hear anything. Please say that again.")
            
#             audio_data = _capture_audio(recognizer, source, timeout=5, phrase_time_limit=10)

#         if not audio_data:
#             # If _capture_audio timed out, loop to the next attempt
#             continue

#         try:
#             logger.info("🧠 Converting speech to text via Google STT...")
#             text = recognizer.recognize_google(audio_data, language=settings.USER_LANGUAGE)
#             logger.info(f"✅ Recognized: '{text}'")
#             return text.lower() # Return successfully recognized text
#         except sr.UnknownValueError:
#             logger.warning("🤷 Google STT could not understand the audio.")
#             # This counts as a failed attempt, so we loop to retry
#         except sr.RequestError as e:
#             logger.error(f"🚨 Could not request results from Google STT service; {e}")
#             feedback.error("I'm having trouble connecting to the speech service.")
#             return None # A network error is not worth retrying, so we exit
#         except Exception as e:
#             logger.exception(f"❌ An unexpected error occurred during speech-to-text conversion: {e}")
#             return None
    
#     # If all retry attempts fail
#     logger.warning("All STT retry attempts failed.")
#     return None
    


def confirm_action() -> bool:
    """Listens for a 'yes' or 'no' confirmation."""
    logger.info("Awaiting 'yes' or 'no' confirmation...")
    command = listen_command() # We can reuse listen_command for this
    if command and "yes" in command.lower():
        return True
    return False