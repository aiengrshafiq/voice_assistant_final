from app.core.logger import get_logger
from app.core.config import get_settings
from app.core.state_machine import VoiceAssistantStateMachine
import os

logger = get_logger(__name__)

def pre_run_checks():
    """Performs critical pre-run checks for settings and model files."""
    settings = get_settings()
    logger.info("Performing pre-run checks...")

    # Check for OpenAI API Key
    if not settings.OPENAI_API_KEY or "YOUR_KEY" in settings.OPENAI_API_KEY:
        logger.critical("FATAL: OPENAI_API_KEY is not configured in your .env file.")
        exit(1)

    # Check for voice enrollment if auth is enabled
    if settings.AUTH_ENABLED:
        embedding_path = "models/embeddings/ceo_voice_embedding.npy"
        if not os.path.exists(embedding_path):
            logger.critical("FATAL: Voice Authentication is enabled, but no voice embedding was found.")
            logger.critical("Please run the enrollment script first: python3 scripts/enroll_voice.py")
            exit(1)
    else:
        logger.info("Voice authentication is DISABLED via config.")
    
    logger.info("✅ Pre-run checks passed.")

def main():
    """Initializes and runs the voice assistant state machine."""
    pre_run_checks()
    
    try:
        logger.info("Starting voice assistant...")
        assistant = VoiceAssistantStateMachine()
        assistant.run()
    except Exception as e:
        # This will catch initialization errors (like a bad Picovoice key)
        logger.critical(f"Failed to initialize the Voice Assistant: {e}")
        exit(1)

if __name__ == "__main__":
    #Just confirming that git has my latest changes before translator module
    main()