from app.services.speech_to_text import listen_command
from app.services.text_to_speech import speak
from app.core.logger import get_logger

logger = get_logger(__name__)

YES_KEYWORDS = {"yes", "go ahead", "sure", "okay", "do it"}
NO_KEYWORDS = {"no", "cancel", "stop", "never mind"}

def confirm_action(retries=2) -> bool:
    for _ in range(retries):
        speak("Please confirm. Say yes to continue or no to cancel.")
        response = listen_command(timeout=4)

        if not response:
            continue

        response = response.lower()
        logger.info(f"User confirmation: {response}")

        if any(keyword in response for keyword in YES_KEYWORDS):
            return True
        if any(keyword in response for keyword in NO_KEYWORDS):
            return False

        speak("Sorry, I didn't catch that.")
    return False
