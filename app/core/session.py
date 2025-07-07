import numpy as np
from pathlib import Path
from collections import deque # Import deque
import json # Import json for formatting history
from resemblyzer import VoiceEncoder
from numpy.linalg import norm
from app.core.logger import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

class SessionManager:
    """Manages the user session, including voice authentication and context."""
    
    def __init__(self):
        self.encoder = VoiceEncoder()
        self.ceo_voice_embedding = self._load_embedding()
        self.current_user = None
        # --- NEW: Initialize a deque for short-term memory (last 5 interactions) ---
        self.access_level: str | None = None # Can be 'private', 'guest', or None
        self.context_stack = deque(maxlen=5)
        self.similarity_threshold = settings.VOICE_AUTH_THRESHOLD 

    def _load_embedding(self) -> np.ndarray | None:
        # ... (this function remains the same)
        embedding_path = Path("models/embeddings/ceo_voice_embedding.npy")
        if not embedding_path.exists():
            if settings.AUTH_ENABLED:
                logger.error("Voice authentication is ENABLED, but no voice embedding was found.")
                logger.error(f"Please run 'scripts/enroll_voice.py' to enroll the primary user.")
                raise FileNotFoundError("CEO voice embedding not found.")
            return None
        
        logger.info(f"Loading voice embedding from {embedding_path}")
        return np.load(embedding_path)

    # --- The verify_voice function is now simpler; it just returns True or False ---
    def verify_voice(self, audio_data: np.ndarray) -> bool:
        """Verifies a given audio snippet against the enrolled voice embedding."""
        if self.ceo_voice_embedding is None:
            logger.warning("Cannot verify voice, no embedding loaded.")
            return False
        try:
            # ... (similarity calculation logic) ...
            utterance_embedding = self.encoder.embed_utterance(audio_data)
            similarity = np.dot(self.ceo_voice_embedding, utterance_embedding) / \
                         (norm(self.ceo_voice_embedding) * norm(utterance_embedding))

            is_verified = similarity > self.similarity_threshold
            logger.info(f"Voice similarity score: {similarity:.2f}. Verified: {is_verified}")
            return is_verified
        except Exception as e:
            logger.exception(f"An error occurred during voice verification: {e}")
            return False

    # def verify_voice(self, audio_data: np.ndarray) -> bool:
    #     # ... (this function remains the same)
    #     if self.ceo_voice_embedding is None:
    #         logger.warning("Cannot verify voice, no embedding loaded.")
    #         return False

    #     try:
    #         utterance_embedding = self.encoder.embed_utterance(audio_data)
    #         similarity = np.dot(self.ceo_voice_embedding, utterance_embedding) / \
    #                      (norm(self.ceo_voice_embedding) * norm(utterance_embedding))
            
    #         logger.info(f"Voice similarity score: {similarity:.2f}")
            
    #         if similarity > self.similarity_threshold:
    #             self.current_user = "CEO"
    #             logger.info(f"Voice verified successfully for user: {self.current_user}")
    #             return True
    #         else:
    #             logger.warning("Voice verification failed. Similarity score below threshold.")
    #             self.current_user = None
    #             return False

    #     except Exception as e:
    #         logger.exception(f"An error occurred during voice embedding generation: {e}")
    #         return False

    # --- NEW: Method to add an interaction to the context stack ---
    def add_to_context(self, nlu_result: dict):
        """Adds a successful NLU result to the context stack."""
        logger.info(f"Adding to context: {nlu_result}")
        self.context_stack.append(nlu_result)

    # --- NEW: Method to get formatted history for the prompt ---
    def get_formatted_history(self) -> str:
        """Formats the context stack into a string for the LLM prompt."""
        if not self.context_stack:
            return "No history yet."
        
        history_str = ""
        # The deque stores items with the newest on the right. We iterate in reverse
        # to show the LLM the most recent items first.
        for item in reversed(self.context_stack):
            history_str += f"- Command: '{item.get('user_command', 'N/A')}' -> Intent: {item.get('intent', 'N/A')}\n"
        return history_str

    def end_session(self):
        """Clears the current user session and context."""
        logger.info("Ending session and clearing user context.")
        self.current_user = None
        self.access_level = None
        self.context_stack.clear()

session_manager = SessionManager()