from app.core.logger import get_logger
from app.core.config import get_settings
from app.services.speech_to_text import listen_command
from app.services.text_to_speech import speak
from app.services.intent_recognizer import detect_intent
from app.services.device_controller import execute_device_action
from app.services.confirmation import confirm_action
from app.core.session import get_verified_user

logger = get_logger(__name__)
settings = get_settings()

def run_voice_assistant():
    try:
        # disable it for now
        # user = get_verified_user()
        # if not user:
        #     speak("You are not authorized to use the assistant.")
        #     return

        speak("Voice assistant initialized. How can I help you today?")
        while True:
            command = listen_command()
            if not command:
                continue

            logger.info(f"Recognized command: {command}")
            speak(f"You said: {command}")

            intent, parameters = detect_intent(command)

            logger.info(f"Detected intent is {intent}")

            if intent == "unsupported":
                speak("I'm not sure how to help with that. I can assist with lights, thermostat, reminders, and more.")
                continue

            if not intent:
                speak("Sorry, I didn’t understand your request.")
                continue

            speak(f"I understood you want to: {intent.replace('_', ' ')}. Shall I proceed?")
            if confirm_action():
                result = execute_device_action(intent, parameters)
                speak(result or "Task completed.")
            else:
                speak("Okay, I’ve cancelled that.")

    except KeyboardInterrupt:
        logger.info("Voice assistant shutdown by user.")
        speak("Shutting down. Goodbye!")

    except Exception as e:
        logger.exception("Unexpected error in assistant loop")
        speak("An error occurred. Please check the logs.")
