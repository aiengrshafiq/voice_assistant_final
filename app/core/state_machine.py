import asyncio
import time
from enum import Enum, auto

from app.core.config import get_settings
from app.core.logger import get_logger
from app.core.session import session_manager
from app.services.action_dispatcher import dispatch_action
# V3: Import the new unified speech service
from app.services.speech_service import speak, listen_command, confirm_action
from app.services.intent_recognizer import detect_intent_with_context
from app.services.wake_word import WakeWordEngine

logger = get_logger(__name__)
settings = get_settings()


class AssistantState(Enum):
    """Defines the possible states of the voice assistant for V3."""
    IDLE = auto()                     # Waiting for the wake word.
    LISTENING = auto()                # Actively listening for a user command.
    PROCESSING = auto()               # Analyzing the command with the NLU engine.
    EXECUTING = auto()                # Performing the requested action.
    AWAITING_INFORMATION = auto()     # Waiting for user to provide missing details (slot-filling).
    AWAITING_CONFIRMATION = auto()    # Waiting for a 'yes' or 'no' from the user.


class VoiceAssistantStateMachine:
    """
    Manages the state and conversational flow of the V3 voice assistant.
    This version is designed to be conversational, resilient, and intelligent.
    """

    def __init__(self):
        self.state = AssistantState.IDLE
        self.wake_word_engine = WakeWordEngine()
        # V3 Conversational State Tracking
        self.current_command: str | None = None
        self.nlu_result: dict | None = None
        self.in_progress_command: dict | None = None  # Stores partial commands for slot-filling

    def run(self):
        """Starts the main event loop for the state machine."""
        logger.info("V3 State Machine started. Initial state: IDLE")
        # For V3, we use asyncio to handle asynchronous operations like STT/TTS
        asyncio.run(self._main_loop())

    async def _main_loop(self):
        """The core asynchronous event loop."""
        try:
            while True:
                if self.state == AssistantState.IDLE:
                    await self._handle_idle_state()
                elif self.state == AssistantState.LISTENING:
                    await self._handle_listening_state()
                elif self.state == AssistantState.PROCESSING:
                    await self._handle_processing_state()
                elif self.state == AssistantState.AWAITING_INFORMATION:
                    await self._handle_awaiting_information_state()
                elif self.state == AssistantState.AWAITING_CONFIRMATION:
                    await self._handle_awaiting_confirmation_state()
                elif self.state == AssistantState.EXECUTING:
                    await self._handle_executing_state()
                
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            logger.warning("Shutdown signal received. Exiting state machine.")
            speak("Shutting down. Goodbye, sir.")
            self.wake_word_engine.release()
        except Exception as e:
            logger.exception("A critical error occurred in the state machine loop.")
            speak("A critical error occurred. Please check the logs. I will now restart.")
            self._reset_conversation()
            self.state = AssistantState.IDLE # Attempt to recover by going idle

    def _reset_conversation(self):
        """Clears all temporary conversational state."""
        logger.info("Resetting conversation context.")
        self.current_command = None
        self.nlu_result = None
        self.in_progress_command = None
        session_manager.clear_context()

    async def _handle_idle_state(self):
        """Waits for the wake word to be detected."""
        self._reset_conversation() # Ensure clean state before listening for wake word
        await asyncio.to_thread(self.wake_word_engine.listen) # Run blocking listen in a thread
        speak("Yes, sir?")
        self.state = AssistantState.LISTENING

    async def _handle_listening_state(self):
        """Listens for a command and transitions to processing."""
        logger.info("State: LISTENING. Ready for user command.")
        
        # We don't say "How can I help?" if we just asked a clarifying question
        if self.state != AssistantState.AWAITING_INFORMATION:
            # speak("How can I help?") # This can be made more dynamic later
            pass

        command = await listen_command()

        if command:
            self.current_command = command
            self.state = AssistantState.PROCESSING
        else:
            logger.warning("No command heard.")
            if self.in_progress_command:
                speak("Sorry, I didn't catch that.")
                self.state = AssistantState.LISTENING # Retry listening for the missing info
            else:
                speak("Going back to sleep.")
                self.state = AssistantState.IDLE # Only go idle if no conversation is active

    async def _handle_processing_state(self):
        """Processes the command using the NLU and routes to the next state."""
        logger.info(f"State: PROCESSING. Analyzing command: '{self.current_command}'")
        history = session_manager.get_formatted_history()

        if self.in_progress_command:
            history.insert(0, self.in_progress_command)

        self.nlu_result = await detect_intent_with_context(self.current_command, history)
        
        intent = self.nlu_result.get('intent', 'unsupported')
        confidence = self.nlu_result.get('confidence', 0.0)
        missing_entities = self.nlu_result.get('missing_entities', [])

        if intent == 'user_frustrated':
            speak(self.nlu_result.get('response_suggestion', "My apologies for the difficulty. Let's try again."))
            self._reset_conversation()
            self.state = AssistantState.LISTENING
            return

        # V3: New conversational logic
        if confidence < 0.65: # Stricter confidence threshold
            speak("I'm not quite sure what you mean. Could you rephrase that?")
            self._reset_conversation()
            self.state = AssistantState.LISTENING # CRITICAL: Return to LISTENING, not IDLE
        elif missing_entities:
            self.in_progress_command = self.nlu_result
            session_manager.add_to_context(self.nlu_result)
            self.state = AssistantState.AWAITING_INFORMATION
        else:
            session_manager.add_to_context(self.nlu_result)
            # Check for actions that require explicit confirmation
            if intent in ['schedule_meeting', 'summon_person']:
                 self.state = AssistantState.AWAITING_CONFIRMATION
            else:
                 self.state = AssistantState.EXECUTING


    async def _handle_awaiting_information_state(self):
        """Asks the user for missing information to fill slots."""
        logger.info("State: AWAITING_INFORMATION.")
        prompt = self.in_progress_command.get('response_suggestion', "I need a bit more information, sir.")
        speak(prompt)
        self.state = AssistantState.LISTENING

    async def _handle_awaiting_confirmation_state(self):
        """Asks the user for a 'yes' or 'no' confirmation before executing a critical action."""
        logger.info("State: AWAITING_CONFIRMATION.")
        
        # Use the smart suggestion from the new NLU prompt
        prompt = self.nlu_result.get('response_suggestion', "Should I proceed?")
        speak(prompt)
        
        if await confirm_action():
            logger.info("User confirmed action.")
            self.state = AssistantState.EXECUTING
        else:
            logger.info("User denied action.")
            speak("Understood. Cancelling the action.")
            self._reset_conversation()
            self.state = AssistantState.LISTENING # Go back to listening for a new command

    async def _handle_executing_state(self):
        """Calls the action dispatcher and speaks the result."""
        logger.info(f"State: EXECUTING. Passing action to dispatcher: {self.nlu_result}")
        
        result = await dispatch_action(
            nlu_result=self.nlu_result,
            access_level=session_manager.access_level 
        )

        # The new dispatcher returns a dict. We handle different statuses.
        if isinstance(result, dict):
            status = result.get("status")
            message = result.get("message", "An unexpected error occurred.")
            
            speak(message)

            if status == "conflict":
                # If there's a conflict, we need to ask the user what to do next.
                self.state = AssistantState.AWAITING_CONFIRMATION
                return # Skip the conversation reset for now
        else:
            # Fallback for older services that return a string
            speak(result)

        logger.info(f"Action executed. Result: {result}")
        self._reset_conversation()
        self.state = AssistantState.LISTENING # Ready for the next command