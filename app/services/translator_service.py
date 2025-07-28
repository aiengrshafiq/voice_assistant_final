#app/services/translator_service.py
import requests
from app.core.logger import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

class TranslatorService:
    """Service for handling language detection and translation via Azure."""

    def __init__(self):
        if not all([settings.AZURE_TRANSLATOR_KEY, settings.AZURE_REGION, settings.TRANSLATE_ENDPOINT]):
            logger.warning("Azure Translator service is not fully configured.")
        
        self.headers = {
            "Ocp-Apim-Subscription-Key": settings.AZURE_TRANSLATOR_KEY,
            "Ocp-Apim-Subscription-Region": settings.AZURE_REGION,
            "Content-type": "application/json"
        }

    def detect_language(self, text: str) -> str | None:
        """Detects the language of the given text."""
        path = "/detect?api-version=3.0"
        body = [{"text": text}]
        try:
            response = requests.post(settings.TRANSLATE_ENDPOINT + path, headers=self.headers, json=body)
            response.raise_for_status()
            # Return the language code, e.g., 'en', 'ar'
            return response.json()[0]["language"]
        except Exception:
            logger.exception("Azure language detection failed.")
            return None

    def translate(self, text: str, to_lang: str) -> str | None:
        """Translates the given text to the target language."""
        path = "/translate?api-version=3.0"
        params = f"&to={to_lang}"
        body = [{"text": text}]
        try:
            response = requests.post(settings.TRANSLATE_ENDPOINT + path + params, headers=self.headers, json=body)
            response.raise_for_status()
            return response.json()[0]["translations"][0]["text"]
        except Exception:
            logger.exception("Azure translation failed.")
            return None

# Create a single instance
translator_service = TranslatorService()