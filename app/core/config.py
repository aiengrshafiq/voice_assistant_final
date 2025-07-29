# app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """
    V3 Final: Explicitly defines all required settings for the application.
    This ensures all variables from the .env file are correctly typed and loaded.
    """
    # Core Assistant Settings
    OPENAI_API_KEY: str
    PORCUPINE_ACCESS_KEY: str
    DEEPGRAM_API_KEY: str
    MIC_DEVICE_INDEX: int = 1
    WAKE_WORD: str = "jarvis"
    
    # Voice Authentication
    AUTH_ENABLED: bool = False
    VOICE_AUTH_THRESHOLD: float = 0.80

    # Home Assistant
    HOME_ASSISTANT_URL: str = "http://localhost:8123"
    HOME_ASSISTANT_TOKEN: str = "YOUR_HA_TOKEN"

    # Slack
    SLACK_BOT_TOKEN: str

    # Email & Notifications
    NOTIFY_EMAIL: str
    BREVO_API_KEY: str
    EMAIL_USER: str = "no-reply@your-domain.com"
    
    # Azure Translator
    AZURE_TRANSLATOR_KEY: str
    AZURE_REGION: str
    TRANSLATE_ENDPOINT: str = "https://api.cognitive.microsofttranslator.com"

    # Deprecated but included for compatibility if any old files remain
    USER_LANGUAGE: str = "en-US"

    # The new performance toggle
    USE_EXPERIMENTAL_STT: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        # THE FIX: This line tells Pydantic to ignore extra variables in the .env file
        extra = 'ignore'

@lru_cache()
def get_settings():
    return Settings()