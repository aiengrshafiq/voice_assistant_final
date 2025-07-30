# app/services/speech_service.py
import asyncio
import os
import subprocess
import speech_recognition as sr
from gtts import gTTS
import requests
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# --- TTS: Your Proven V2 Logic ---
def _speak_gtts(text: str, lang: str):
    """Internal function to speak using gTTS."""
    try:
        logger.info(f"[gTTS] Speaking ({lang}): {text}")
        tts = gTTS(text=text, lang=lang)
        filename = "/tmp/speak_gtts.mp3"
        tts.save(filename)
        subprocess.run(["mpg123", "-q", filename], check=True)
        os.remove(filename)
    except Exception:
        logger.exception("[TTS] gTTS fallback failed.")

def _speak_elevenlabs(text: str, lang: str):
    """Internal function to speak using ElevenLabs streaming."""
    if not settings.ELEVENLABS_API_KEY:
        logger.error("[TTS] ElevenLabs API key not configured.")
        return
    try:
        voice_map = {"en": settings.ELEVENLABS_VOICE_ID_EN, "ar": settings.ELEVENLABS_VOICE_ID_AR}
        voice_id = voice_map.get(lang, settings.ELEVENLABS_VOICE_ID_EN)
        logger.info(f"[ElevenLabs] Streaming translation ({lang}) for voice ID {voice_id}: {text}")
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream",
            headers={"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": settings.ELEVENLABS_API_KEY},
            json={"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}},
            stream=True
        )
        response.raise_for_status()
        player_process = subprocess.Popen(["mpg123", "-q", "-"], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for chunk in response.iter_content(chunk_size=4096):
            if chunk: player_process.stdin.write(chunk)
        player_process.stdin.close()
        player_process.wait()
    except Exception as e:
        logger.exception(f"[TTS] ElevenLabs streaming failed: {e}")

def speak(text: str, lang: str = "en"):
    """Standard system TTS function. ALWAYS uses gTTS."""
    _speak_gtts(text, lang)

def speak_translation(text: str, lang: str = "en"):
    """Premium TTS function for translations. ALWAYS uses ElevenLabs."""
    _speak_elevenlabs(text, lang)


# --- STT: Your Proven V2 Logic ---
class SpeechToText:
    """Uses the robust speech_recognition library."""
    def __init__(self):
        self.recognizer = sr.Recognizer()

    async def listen(self, timeout=7.0):
        try:
            with sr.Microphone(device_index=settings.MIC_DEVICE_INDEX) as source:
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                logger.info("Listening for command...")
                audio = await asyncio.to_thread(self.recognizer.listen, source, timeout=timeout, phrase_time_limit=10)
                
                logger.info("Recognizing speech with Google Speech Recognition...")
                text = await asyncio.to_thread(self.recognizer.recognize_google, audio)
                logger.info(f"[STT] Transcript received: '{text}'")
                return text.lower()
        except sr.WaitTimeoutError:
            logger.warning("STT listening timed out.")
            return None
        except sr.UnknownValueError:
            logger.warning("Google Speech Recognition could not understand the audio.")
            return None
        except Exception as e:
            logger.error(f"An error occurred during STT: {e}")
            return None

stt_service = SpeechToText()

async def confirm_action(timeout=5.0):
    response = await stt_service.listen(timeout=timeout)
    return response and any(word in response.lower() for word in ["yes", "yeah", "confirm", "correct"])