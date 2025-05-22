import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sounddevice as sd
import soundfile as sf
from app.services.voice_auth import verify_voice
from app.services.text_to_speech import speak
from app.core.config import get_settings
from app.core.logger import get_logger
from app.core.session import set_verified_user

logger = get_logger(__name__)
settings = get_settings()

TEMP_FILE = "latest_voice.wav"
SAMPLE_RATE = 16000
DURATION = 3

def record_voice(filename: str, duration=DURATION, samplerate=SAMPLE_RATE):
    try:
        logger.info("[VoiceAuth] Recording voice for verification...")
        speak("Please say your name for verification.")
        audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
        sd.wait()
        sf.write(filename, audio, samplerate)
        logger.info("[VoiceAuth] Voice recording complete.")
        return True
    except Exception as e:
        logger.exception("[VoiceAuth] Failed to record voice.")
        return False

def authenticate_user():
    if not record_voice(TEMP_FILE):
        speak("Voice recording failed.")
        return False

    allowed_labels = settings.AUTHORIZED_VOICE_LABELS.split(",")
    result = verify_voice(TEMP_FILE, allowed_labels=allowed_labels)

    if result:
        #set_verified_user(result['label']) # disable it for now
        speak(f"Welcome, {result['label']}.")
        logger.info(f"[VoiceAuth] Verified user: {result['label']} with score {result['score']}")
        return True
    else:
        speak("Voice not recognized or unauthorized.")
        logger.warning("[VoiceAuth] Authentication failed.")
        return False

if __name__ == "__main__":
    success = authenticate_user()
    exit(0 if success else 1)
