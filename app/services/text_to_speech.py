import requests
import subprocess
import os
from gtts import gTTS
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

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
        logger.error("[TTS] ElevenLabs API key not configured. Cannot speak translation.")
        # We don't fall back to gTTS here, as this function is exclusive.
        return
        
    try:
        voice_map = {
            "en": settings.ELEVENLABS_VOICE_ID_EN,
            "ar": settings.ELEVENLABS_VOICE_ID_AR,
        }
        voice_id = voice_map.get(lang, settings.ELEVENLABS_VOICE_ID_EN)
        
        logger.info(f"[ElevenLabs] Streaming translation ({lang}) for voice ID {voice_id}: {text}")

        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream",
            headers={
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": settings.ELEVENLABS_API_KEY
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": { "stability": 0.5, "similarity_boost": 0.75 }
            },
            stream=True
        )
        response.raise_for_status()

        player_process = subprocess.Popen(
            ["mpg123", "-q", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for chunk in response.iter_content(chunk_size=4096):
            if chunk:
                player_process.stdin.write(chunk)
        player_process.stdin.close()
        player_process.wait()

    except Exception as e:
        logger.exception(f"[TTS] ElevenLabs streaming failed for translation: {e}")

# --- PUBLIC FUNCTIONS ---

def speak(text: str, lang: str = "en"):
    """
    Standard system TTS function. ALWAYS uses gTTS for consistency.
    """
    _speak_gtts(text, lang)

def speak_translation(text: str, lang: str = "en"):
    """
    Premium TTS function for translations. ALWAYS uses ElevenLabs.
    """
    _speak_elevenlabs(text, lang)