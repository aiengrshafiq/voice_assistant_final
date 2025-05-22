# config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    PORCUPINE_ACCESS_KEY: str
    MIC_DEVICE_INDEX: int = 2
    SPEAKER_DEVICE: str = "default"
    GOOGLE_CREDENTIALS_PATH: str = "credentials.json"
    WEATHER_API_KEY: str = ""
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    EMAIL_USER: str = ""
    EMAIL_PASSWORD: str = ""
    DB_PATH: str = "assistant.db"
    HOME_ASSISTANT_URL: str = "http://localhost:8123"
    HOME_ASSISTANT_TOKEN: str = ""
    TTS_ENGINE: str = "gtts"  # "gtts" or "pyttsx3"
    AUTHORIZED_VOICE_LABELS: str = "CEO,Shafiq,Nouman"  # Comma-separated
    AUTH_ENABLED: bool = False
    # ✅ Add missing .env fields
    NOTIFY_EMAIL: str = ""
    BREVO_API_KEY: str = ""
    

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "allow"  # forbid is the default; you can change to "allow" if needed

@lru_cache()
def get_settings():
    return Settings()