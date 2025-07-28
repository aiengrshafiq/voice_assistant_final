# app/core/session.py
import numpy as np
from pathlib import Path
from collections import deque
from resemblyzer import VoiceEncoder
from numpy.linalg import norm
from app.core.logger import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

class SessionManager:
    def __init__(self):
        self.encoder = VoiceEncoder()
        self.ceo_voice_embedding = self._load_embedding()
        self.access_level: str | None = None
        self.context_stack = deque(maxlen=5) # Short-term memory for 5 turns
        self.similarity_threshold = settings.VOICE_AUTH_THRESHOLD 

    def _load_embedding(self) -> np.ndarray | None:
        # This function can remain the same
        embedding_path = Path("models/embeddings/ceo_voice_embedding.npy")
        if not embedding_path.exists():
            if settings.AUTH_ENABLED:
                logger.error("Voice auth is ENABLED, but voice embedding not found.")
                raise FileNotFoundError("CEO voice embedding not found.")
            return None
        return np.load(embedding_path)

    def verify_voice(self, audio_data: np.ndarray) -> bool:
        # This function can remain the same
        if self.ceo_voice_embedding is None: return False
        try:
            utterance_embedding = self.encoder.embed_utterance(audio_data)
            similarity = np.dot(self.ceo_voice_embedding, utterance_embedding) / \
                         (norm(self.ceo_voice_embedding) * norm(utterance_embedding))
            is_verified = similarity > self.similarity_threshold
            logger.info(f"Voice similarity score: {similarity:.2f}. Verified: {is_verified}")
            return is_verified
        except Exception as e:
            logger.exception(f"Error during voice verification: {e}")
            return False

    def add_to_context(self, nlu_result: dict):
        """Adds a successful NLU result to the context stack."""
        logger.info(f"Adding to context: {nlu_result}")
        self.context_stack.append(nlu_result)

    def get_formatted_history(self) -> list:
        """V3: Returns the context stack as a list of dictionaries."""
        return list(reversed(self.context_stack))

    def clear_context(self):
        """Clears the conversational context stack."""
        logger.info("Clearing conversation context.")
        self.context_stack.clear()

session_manager = SessionManager()