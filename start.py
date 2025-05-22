from app.services.wake_word import listen_for_wake_word
from app.pipelines.assistant_runner import run_voice_assistant
#from app.services.scheduler import schedule_daily_briefing
#from app.utils.db import init_note_db
import subprocess
from app.core.logger import get_logger
from app.core.config import get_settings
settings = get_settings()

logger = get_logger(__name__)

import sounddevice as sd
def log_audio_devices():
    logger.info("Available audio input devices:")
    for i, dev in enumerate(sd.query_devices()):
        if dev['max_input_channels'] > 0:
            logger.info(f"Device {i}: {dev['name']} (Inputs: {dev['max_input_channels']})")


def main():
    logger.info("Starting voice assistant...")
    #log_audio_devices()
    #uncomment below if you want automatic daily briefing
    #schedule_daily_briefing()
    #init_note_db()
    # Run voice authentication before launching assistant
    if settings.AUTH_ENABLED:
        if subprocess.call(["python3", "scripts/voice_auth_startup.py"]) != 0:
            exit(1)
    else:
        logger.info("Voice authentication is DISABLED via config.")

    listen_for_wake_word(callback=run_voice_assistant)

if __name__ == "__main__":
    main()
