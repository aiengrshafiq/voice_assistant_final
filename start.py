from app.services.wake_word import listen_for_wake_word
from app.pipelines.assistant_runner import run_voice_assistant
#from app.services.scheduler import schedule_daily_briefing
#from app.utils.db import init_note_db
from app.core.logger import get_logger

logger = get_logger(__name__)

import sounddevice as sd
def log_audio_devices():
    logger.info("Available audio input devices:")
    for i, dev in enumerate(sd.query_devices()):
        if dev['max_input_channels'] > 0:
            logger.info(f"Device {i}: {dev['name']} (Inputs: {dev['max_input_channels']})")


def main():
    logger.info("Starting voice assistant...")
    log_audio_devices()
    #uncomment below if you want automatic daily briefing
    #schedule_daily_briefing()
    #init_note_db()
    listen_for_wake_word(callback=run_voice_assistant)

if __name__ == "__main__":
    main()
