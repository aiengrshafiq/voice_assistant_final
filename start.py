# start.py
import os
from app.core.logger import get_logger
from app.core.config import get_settings
from app.core.state_machine import VoiceAssistantStateMachine

logger = get_logger(__name__)

def pre_run_checks():
    """Performs critical pre-run checks for settings and model files."""
    settings = get_settings()
    logger.info("Performing V3 pre-run checks...")

    # Check for OpenAI API Key
    if not settings.OPENAI_API_KEY or "YOUR_KEY" in settings.OPENAI_API_KEY:
        logger.critical("FATAL: OPENAI_API_KEY is not configured in your .env file.")
        exit(1)
        
    # Check for Deepgram API Key
    if not settings.DEEPGRAM_API_KEY or "YOUR_KEY" in settings.DEEPGRAM_API_KEY:
        logger.critical("FATAL: DEEPGRAM_API_KEY is not configured in your .env file.")
        exit(1)

    # Check for TTS model
    if not os.path.exists("models/tts/en_US-lessac-medium.onnx"):
         logger.warning("TTS voice model not found. TTS will fall back to printing.")

    # Check for voice enrollment if auth is enabled
    if settings.AUTH_ENABLED:
        embedding_path = "models/embeddings/ceo_voice_embedding.npy"
        if not os.path.exists(embedding_path):
            logger.critical("FATAL: Voice Auth is enabled, but no embedding was found.")
            logger.critical("Run: python3 scripts/enroll_voice.py")
            exit(1)
    else:
        logger.info("Voice authentication is DISABLED via config.")
    
    logger.info("✅ Pre-run checks passed.")

def main():
    """Initializes and runs the V3 voice assistant state machine."""
    pre_run_checks()
    
    try:
        logger.info("Starting V3 Voice Assistant...")
        assistant = VoiceAssistantStateMachine()
        assistant.run() # This now calls asyncio.run() internally
    except Exception as e:
        logger.critical(f"Failed to initialize the Voice Assistant: {e}")
        exit(1)

if __name__ == "__main__":
    main()