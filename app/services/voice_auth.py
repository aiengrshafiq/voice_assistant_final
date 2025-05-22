import os
import numpy as np
import soundfile as sf
from resemblyzer import VoiceEncoder, preprocess_wav
from app.core.logger import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

VOICEPRINT_DIR = "voiceprints"
os.makedirs(VOICEPRINT_DIR, exist_ok=True)

encoder = VoiceEncoder()
SAMPLE_RATE = 16000


def get_embedding(wav_path: str):
    try:
        wav = preprocess_wav(wav_path)
        embed = encoder.embed_utterance(wav)
        return embed
    except Exception as e:
        logger.exception(f"[VoiceAuth] Failed to generate embedding: {e}")
        return None


def register_voice(label: str, wav_path: str) -> bool:
    try:
        embedding = get_embedding(wav_path)
        if embedding is None:
            return False
        save_path = os.path.join(VOICEPRINT_DIR, f"{label}.npy")
        np.save(save_path, embedding)
        logger.info(f"[VoiceAuth] Voice registered for label: {label}")
        return True
    except Exception as e:
        logger.exception("[VoiceAuth] Registration failed")
        return False


def verify_voice(wav_path: str, allowed_labels: list[str] = None, threshold: float = 0.75):
    try:
        test_embedding = get_embedding(wav_path)
        if test_embedding is None:
            return None

        best_score = -1
        best_label = None

        for filename in os.listdir(VOICEPRINT_DIR):
            label = filename.replace(".npy", "")
            if allowed_labels and label not in allowed_labels:
                continue

            ref_embedding = np.load(os.path.join(VOICEPRINT_DIR, filename))
            score = np.dot(test_embedding, ref_embedding) / (
                np.linalg.norm(test_embedding) * np.linalg.norm(ref_embedding)
            )

            logger.info(f"[VoiceAuth] Match score with {label}: {score:.3f}")

            if score > best_score:
                best_score = score
                best_label = label

        if best_score >= threshold:
            return {"label": best_label, "score": round(best_score, 3)}
        else:
            logger.warning("[VoiceAuth] No match above threshold.")
            return None
    except Exception as e:
        logger.exception("[VoiceAuth] Verification failed")
        return None
