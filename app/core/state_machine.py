# app/core/state_machine.py
import asyncio
from enum import Enum, auto
from app.core.logger import get_logger
from app.core.session import session_manager
from app.services.action_dispatcher import dispatch_action
from app.services.speech_service import speak, speak_translation, stt_service, confirm_action
from app.services.intent_recognizer import detect_intent_with_context, is_confirmed
from app.services.wake_word import WakeWordEngine
from app.services.translator_service import translator_service

logger = get_logger(__name__)

class AssistantState(Enum):
    IDLE = auto(); LISTENING = auto(); PROCESSING = auto(); EXECUTING = auto()
    AWAITING_INFORMATION = auto(); AWAITING_CONFIRMATION = auto(); TRANSLATING = auto()

class VoiceAssistantStateMachine:
    def __init__(self):
        self.wake_word_engine = WakeWordEngine()
        self.state = AssistantState.IDLE
        self.nlu_result: dict | None = None

    def run(self):
        logger.info("V3.1 State Machine started. Initial state: IDLE")
        try: asyncio.run(self._main_loop())
        finally: self.wake_word_engine.release()

    async def _main_loop(self):
        while True:
            try:
                if self.state == AssistantState.IDLE: await self._handle_idle_state()
                elif self.state == AssistantState.LISTENING: await self._handle_listening_state()
                elif self.state == AssistantState.PROCESSING: await self._handle_processing_state()
                elif self.state == AssistantState.AWAITING_INFORMATION: await self._handle_awaiting_information_state()
                elif self.state == AssistantState.AWAITING_CONFIRMATION: await self._handle_awaiting_confirmation_state()
                elif self.state == AssistantState.EXECUTING: await self._handle_executing_state()
                elif self.state == AssistantState.TRANSLATING: await self._handle_translating_state()
            except Exception as e:
                logger.exception(f"A critical error occurred: {e}")
                await asyncio.to_thread(speak, "A critical error occurred.")
                self._reset_conversation(); self.state = AssistantState.IDLE

    def _reset_conversation(self):
        self.nlu_result = None
        session_manager.clear_context()

    async def _handle_idle_state(self):
        self._reset_conversation()
        await asyncio.to_thread(self.wake_word_engine.listen)
        await asyncio.to_thread(speak, "Yes, sir?")
        self.state = AssistantState.LISTENING

    async def _handle_listening_state(self):
        command = await stt_service.listen()
        if command:
            self.nlu_result = await detect_intent_with_context(command, session_manager.get_formatted_history())
            self.state = AssistantState.PROCESSING
        else:
            self.state = AssistantState.IDLE

    async def _handle_processing_state(self):
        session_manager.add_to_context(self.nlu_result)
        
        if self.nlu_result.get('intent') == 'start_translation':
            self.state = AssistantState.TRANSLATING
        elif self.nlu_result.get('missing_entities'):
            self.state = AssistantState.AWAITING_INFORMATION
        elif self.nlu_result.get('action_type') == 'QUERY':
            self.state = AssistantState.EXECUTING
        elif self.nlu_result.get('action_type') == 'ACTION':
            self.state = AssistantState.AWAITING_CONFIRMATION
        else:
            await asyncio.to_thread(speak, "I'm not sure how to help with that, but you can ask me to do things like check your calendar or take a note. For a full list of my abilities, just say, 'what can you do?'")
            self.state = AssistantState.IDLE

    async def _handle_awaiting_information_state(self):
        prompt = self.nlu_result.get('response_suggestion', "I need more information.")
        await asyncio.to_thread(speak, prompt)
        self.state = AssistantState.LISTENING

    async def _handle_awaiting_confirmation_state(self):
        prompt = self.nlu_result.get('response_suggestion', "Should I proceed?")
        full_prompt = f"{prompt} Please say confirm, or cancel."
        await asyncio.to_thread(speak, full_prompt)
        
        confirmation_command = await stt_service.listen()
        if await is_confirmed(confirmation_command):
            self.state = AssistantState.EXECUTING
        else:
            await asyncio.to_thread(speak, "Understood. Cancelling.")
            self.state = AssistantState.IDLE

    async def _handle_executing_state(self):
        result = await dispatch_action(self.nlu_result, session_manager.access_level)
        message = result.get("message", "An unknown error occurred.")
        if message: # Don't speak if the message is empty
            await asyncio.to_thread(speak, message)
        
        if result.get("status") == "conflict":
            self.state = AssistantState.AWAITING_CONFIRMATION
        else:
            self.state = AssistantState.IDLE

    async def _handle_translating_state(self):
        await asyncio.to_thread(speak, "Translation mode activated. Say 'stop translation' to exit.")
        while self.state == AssistantState.TRANSLATING:
            text_to_translate = await stt_service.listen(timeout=30)
            if not text_to_translate: continue
            
            if "stop translation" in text_to_translate.lower():
                await asyncio.to_thread(speak, "Exiting translation mode.")
                self.state = AssistantState.IDLE
                break
            
            source_lang = translator_service.detect_language(text_to_translate)
            target_lang = 'ar' if (source_lang and 'en' in source_lang) else 'en'
            translated_text = translator_service.translate(text_to_translate, target_lang)
            
            if translated_text:
                # THE FIX 2/2: Call the premium speak_translation function here.
                await asyncio.to_thread(speak_translation, translated_text, lang=target_lang)
            else:
                await asyncio.to_thread(speak, "Sorry, I could not get a translation.")