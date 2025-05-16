import os
import sys

# Suppress ALSA warnings
sys.stderr = open(os.devnull, 'w')

from app.services.wake_word import listen_for_wake_word
from app.pipelines.assistant_runner import run_voice_assistant
from app.core.logger import get_logger

logger = get_logger(__name__)

def main():
    logger.info("Starting voice assistant...")
    listen_for_wake_word(callback=run_voice_assistant)

if __name__ == "__main__":
    main()
