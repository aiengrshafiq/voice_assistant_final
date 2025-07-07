from enum import Enum, auto
import time

from app.core.logger import get_logger
from app.core.config import get_settings
from app.core.session import session_manager
from app.services.wake_word import WakeWordEngine
# --- Import the new NLU service ---
from app.services.intent_recognizer import detect_intent_with_context
from app.services.speech_to_text import listen_for_verification, listen_command, confirm_action
from app.services.text_to_speech import speak, speak_translation
from app.services.action_dispatcher import dispatch_action
from app.services.feedback_manager import feedback
from app.services.translator_service import translator_service

logger = get_logger(__name__)
settings = get_settings()

class AssistantState(Enum):
    IDLE = auto()
    WOKE_UP = auto()
    AUTHENTICATING = auto()
    LISTENING = auto()
    # --- NEW STATES ---
    PROCESSING = auto()
    AWAITING_CONFIRMATION = auto()
    EXECUTING = auto()
    TRANSLATING = auto()

class VoiceAssistantStateMachine:
    def __init__(self):
        self.state = AssistantState.IDLE
        self.wake_word_engine = WakeWordEngine()
        # --- NEW: Temp storage for data between states ---
        self.current_command: str | None = None
        self.nlu_result: dict | None = None

    def run(self):
        logger.info("State machine started. Initial state: IDLE")
        while True:
            try:
                # --- ADDED The new state handlers to the main loop ---
                if self.state == AssistantState.IDLE: self._handle_idle_state()
                elif self.state == AssistantState.WOKE_UP: self._handle_woke_up_state()
                elif self.state == AssistantState.AUTHENTICATING: self._handle_authenticating_state()
                elif self.state == AssistantState.LISTENING: self._handle_listening_state()
                elif self.state == AssistantState.PROCESSING: self._handle_processing_state()
                elif self.state == AssistantState.AWAITING_CONFIRMATION: self._handle_awaiting_confirmation_state()
                elif self.state == AssistantState.EXECUTING: self._handle_executing_state()
                elif self.state == AssistantState.TRANSLATING: self._handle_translating_state()
                
                time.sleep(0.1)

            except KeyboardInterrupt:
                # ... (this part remains the same)
                logger.warning("Shutdown signal received. Exiting state machine.")
                speak("Shutting down. Goodbye!")
                self.wake_word_engine.release()
                break
            except Exception:
                # ... (this part remains the same)
                logger.exception("An unhandled error occurred in the state machine loop.")
                feedback.error("A critical error occurred. Please check the logs. Restarting.")
                self.state = AssistantState.IDLE

    # --- IDLE and WOKE_UP states are unchanged ---
    def _handle_idle_state(self):
        self.wake_word_engine.listen()
        self.state = AssistantState.WOKE_UP

    def _handle_woke_up_state(self):
        #speak("Yes?")
        # --- MODIFICATION: Use a chime instead of voice ---
        feedback.acknowledge()
        if settings.AUTH_ENABLED: self.state = AssistantState.AUTHENTICATING
        else: self.state = AssistantState.LISTENING

    # --- AUTHENTICATING state is unchanged ---
    def _handle_authenticating_state(self):
        """Records a short audio clip and verifies the user's voice."""
        logger.info("State: AUTHENTICATING. Awaiting voice sample for verification.")

        # --- ADD THIS LINE ---
        feedback.confirm("Please say a short phrase for voice verification.")
        audio_data = listen_for_verification(duration=3) 
        if audio_data is None:
            self.state = AssistantState.IDLE
            return
        if session_manager.verify_voice(audio_data):
            #speak("Identity confirmed.")
            # --- MODIFICATION: Use feedback.success ---
            feedback.success("Identity confirmed.")
            self.state = AssistantState.LISTENING
        else:
            feedback.error("I'm sorry, I don't recognize your voice.")
            self.state = AssistantState.IDLE

    # --- LISTENING state is now simpler ---
    def _handle_listening_state(self):
        """Listens for a command and transitions to PROCESSING."""
        logger.info("State: LISTENING. Ready for user command.")
        # --- MODIFICATION: Use feedback.confirm ---
        feedback.confirm("How can I help you?")
        command = listen_command()

        if command:
            self.current_command = command
            self.state = AssistantState.PROCESSING
        else:
            logger.warning("No command heard. Returning to IDLE state.")
            #speak("I didn't catch that. Going back to sleep.")
            self.state = AssistantState.IDLE
    
    # --- NEW: PROCESSING state with confidence logic ---
    def _handle_processing_state(self):
        """Processes the command using NLU and routes based on confidence."""
        logger.info(f"State: PROCESSING. Analyzing command: '{self.current_command}'")
        history = session_manager.get_formatted_history()
        self.nlu_result = detect_intent_with_context(self.current_command, history)
        
        confidence = self.nlu_result.get('confidence', 0.0)
        intent = self.nlu_result.get('intent', 'unknown')

        # --- NEW: Handle state-changing meta-commands before the dispatcher ---
        if intent == 'start_translation':
            logger.info("Transitioning to TRANSLATING state.")
            self.state = AssistantState.TRANSLATING
            return # Exit early, no need to dispatch

        # Add to context only if intent is valid and not a meta-command
        if intent not in ['unknown', 'unsupported', 'nlu_error', 'start_translation']:
            session_manager.add_to_context(self.nlu_result)

        # Confidence-based routing
        if confidence >= 0.9:
            logger.info(f"High confidence ({confidence:.2f}). Executing directly.")
            self.state = AssistantState.EXECUTING
        elif 0.7 <= confidence < 0.9:
            logger.info(f"Medium confidence ({confidence:.2f}). Asking for confirmation.")
            self.state = AssistantState.AWAITING_CONFIRMATION
        else:
            logger.warning(f"Low confidence ({confidence:.2f}) or unsupported intent. Re-prompting.")
            if intent == 'unsupported':
                feedback.confirm("I'm not sure how to help with that. Please try rephrasing your request.")
            else:
                feedback.confirm("I'm not quite sure what you mean. Could you say that again?")
            self.state = AssistantState.IDLE

    # --- NEW: AWAITING_CONFIRMATION state ---
    def _handle_awaiting_confirmation_state(self):
        """Asks the user to confirm an action."""
        logger.info("State: AWAITING_CONFIRMATION.")
        intent_phrase = self.nlu_result.get('intent', 'the action').replace('_', ' ')
        
        feedback.confirm(f"Just to be sure, you want me to {intent_phrase}. Is that correct?")
        
        if confirm_action(): # This should be a function in STT that listens for "yes" or "no"
            logger.info("User confirmed action.")
            self.state = AssistantState.EXECUTING
        else:
            logger.info("User denied action.")
            feedback.success("My mistake. Cancelling the action.")
            self.state = AssistantState.IDLE

  
    
    def _handle_executing_state(self):
        """Calls the action dispatcher and speaks the result."""
        logger.info(f"State: EXECUTING. Passing action to dispatcher: {self.nlu_result}")
        
        # Call the dispatcher with the NLU result
        result_message = dispatch_action(self.nlu_result)
        
        # Speak the result returned by the service
        #speak(result_message)
        if "Okay" in result_message or "Done" in result_message:
            feedback.acknowledge()
        else:
            feedback.success(result_message)
        logger.info(f"Action executed: {result_message}")
        

        # Reset for the next loop
        self.current_command = None
        self.nlu_result = None
        self.state = AssistantState.IDLE

    # --- NEW METHOD: The translator mode loop ---
    def _handle_translating_state(self):
        """Handles the continuous translation mode."""
        feedback.success("Translation mode activated. I will now translate between English and Arabic.")
        
        while True:
            # 1. Listen for any speech
            text_to_translate = listen_command(timeout=30) # Use a longer timeout

            if not text_to_translate:
                logger.info("No speech detected in translation mode.")
                continue

            # 2. Check for the exit command
            if "stop translation" in text_to_translate.lower():
                feedback.success("Exiting translation mode.")
                self.state = AssistantState.IDLE
                break # Exit the translation loop

            # 3. Detect language
            source_lang = translator_service.detect_language(text_to_translate)
            if not source_lang:
                feedback.error("Sorry, I couldn't determine the language.")
                continue

            # 4. Determine target language and translate
            if 'en' in source_lang:
                target_lang = 'ar'
            elif 'ar' in source_lang:
                target_lang = 'en'
            else:
                feedback.confirm("I can only translate between English and Arabic.")
                continue
            
            translated_text = translator_service.translate(text_to_translate, target_lang)

            # 5. Speak the translation in the target language's voice
            if translated_text:
                speak_translation(translated_text, lang=target_lang)
            else:
                feedback.error("Sorry, I was unable to get a translation.")