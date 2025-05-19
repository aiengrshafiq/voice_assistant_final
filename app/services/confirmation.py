from app.services.vosk_stt import listen_yes_no
from app.services.text_to_speech import speak
from app.core.logger import get_logger

logger = get_logger(__name__)

YES_KEYWORDS = {"yes", "go ahead", "sure", "okay", "do it","this"}
NO_KEYWORDS = {"no", "cancel", "stop", "never mind"}

def confirm_action(retries=2) -> bool:
    for _ in range(retries):
        speak("Please confirm. Say yes to continue or no to cancel.")
        response = listen_yes_no()
        if not response:
            speak("I didn't catch that.")
            continue

        response = response.lower()
        logger.info(f"User said: {response}")

        if any(word in response for word in YES_KEYWORDS):
            return True
        if any(word in response for word in NO_KEYWORDS):
            return False

        speak("Please respond with yes or no.")
    return False
