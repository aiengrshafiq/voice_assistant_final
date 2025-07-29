# app/core/state_machine.py
import asyncio
from enum import Enum, auto
from app.core.logger import get_logger
from app.core.session import session_manager
from app.services.action_dispatcher import dispatch_action
from app.services.speech_service import speak, stt_service, confirm_action
from app.services.intent_recognizer import detect_intent_with_context
from app.services.wake_word import WakeWordEngine

logger = get_logger(__name__)

class AssistantState(Enum):
    IDLE = auto(); LISTENING = auto(); PROCESSING = auto(); EXECUTING = auto()
    AWAITING_INFORMATION = auto(); AWAITING_CONFIRMATION = auto()

class VoiceAssistantStateMachine:
    def __init__(self):
        self.wake_word_engine = WakeWordEngine()
        self.state = AssistantState.IDLE
        self.current_command: str | None = None
        self.nlu_result: dict | None = None
        self.in_progress_command: dict | None = None

    def run(self):
        logger.info("V3 State Machine started. Initial state: IDLE")
        try:
            asyncio.run(self._main_loop())
        finally:
            self.wake_word_engine.release()

    async def _main_loop(self):
        while True:
            try:
                if self.state == AssistantState.IDLE: await self._handle_idle_state()
                elif self.state == AssistantState.LISTENING: await self._handle_listening_state()
                elif self.state == AssistantState.PROCESSING: await self._handle_processing_state()
                elif self.state == AssistantState.AWAITING_INFORMATION: await self._handle_awaiting_information_state()
                elif self.state == AssistantState.AWAITING_CONFIRMATION: await self._handle_awaiting_confirmation_state()
                elif self.state == AssistantState.EXECUTING: await self._handle_executing_state()
            except Exception as e:
                logger.exception(f"A critical error occurred: {e}")
                await asyncio.to_thread(speak, "A critical error occurred.")
                self._reset_conversation(); self.state = AssistantState.IDLE

    def _reset_conversation(self):
        self.current_command = None; self.nlu_result = None; self.in_progress_command = None
        session_manager.clear_context()

    async def _handle_idle_state(self):
        self._reset_conversation()
        await asyncio.to_thread(self.wake_word_engine.listen)
        await asyncio.to_thread(speak, "Yes, sir?")
        self.state = AssistantState.LISTENING

    async def _handle_listening_state(self):
        command = await stt_service.listen()
        if command:
            self.current_command = command
            self.state = AssistantState.PROCESSING
        else:
            self.state = AssistantState.IDLE

    async def _handle_processing_state(self):
        history = session_manager.get_formatted_history()
        if self.in_progress_command: history.insert(0, self.in_progress_command)
        self.nlu_result = await detect_intent_with_context(self.current_command, history)
        
        session_manager.add_to_context(self.nlu_result)
        action_type = self.nlu_result.get('action_type')

        if self.nlu_result.get('missing_entities'):
            self.in_progress_command = self.nlu_result
            self.state = AssistantState.AWAITING_INFORMATION
        elif action_type == 'QUERY':
            self.state = AssistantState.EXECUTING
        elif action_type == 'ACTION':
            self.state = AssistantState.AWAITING_CONFIRMATION
        else:
            await asyncio.to_thread(speak, "I'm sorry, I'm not sure how to help with that.")
            self.state = AssistantState.IDLE

    async def _handle_awaiting_information_state(self):
        prompt = self.in_progress_command.get('response_suggestion', "I need more information.")
        await asyncio.to_thread(speak, prompt)
        self.state = AssistantState.LISTENING

    async def _handle_awaiting_confirmation_state(self):
        # THE FIX: Create a clearer, more robust confirmation prompt.
        base_prompt = self.nlu_result.get('response_suggestion', "Should I proceed?")
        full_prompt = f"{base_prompt} Please say confirm, or cancel."
        
        await asyncio.to_thread(speak, full_prompt)
        
        if await confirm_action():
            self.state = AssistantState.EXECUTING
        else:
            await asyncio.to_thread(speak, "Understood. Cancelling.")
            self.state = AssistantState.IDLE

    async def _handle_executing_state(self):
        result = await dispatch_action(self.nlu_result, session_manager.access_level)
        message = result.get("message", "An unknown error occurred.")
        await asyncio.to_thread(speak, message)
        if result.get("status") == "conflict":
            self.state = AssistantState.AWAITING_CONFIRMATION
        else:
            self.state = AssistantState.IDLE