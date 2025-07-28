# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()
env_path = Path(".") / ".env"

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
    USER_LANGUAGE: str = "en-US"
    WAKE_WORD: str = "jarvis"
    SLACK_BOT_TOKEN: str = "YOUR_SLACK_TOKEN_HERE" # Placeholder
    VOICE_AUTH_THRESHOLD: float = 0.65

    # --- AZURE TRANSLATOR ---
    AZURE_TRANSLATOR_KEY: str ="1Wry3RrRuk6eKp62trVIQ44OnoRukTUNs38JasEETHMibPuJFtKPJQQJ99BEACYeBjFXJ3w3AAAbACOGoa9p"
    AZURE_REGION: str ="eastus" # e.g., eastus
    TRANSLATE_ENDPOINT: str ="https://api.cognitive.microsofttranslator.com"

    # --- TEXT-TO-SPEECH PROVIDER ---
    TTS_PROVIDER: str ="elevenlabs" # Use 'elevenlabs' or 'gtts'
    ELEVENLABS_API_KEY: str ="sk_9e2b620f79f0424a1cb90d016e90f6d18747b2885d95c03b"
    # Find Voice IDs in your ElevenLabs Voice Lab
    ELEVENLABS_VOICE_ID_EN: str ="SV61h9yhBg4i91KIBwdz" # e.g., 21m00Tcm4TlvDq8ikWAM
    ELEVENLABS_VOICE_ID_AR: str ="jAAHNNqlbAX9iWjJPEtE"
    # Name of your audio output device for mpg123, find with 'aplay -L'
    #SPEAKER_DEVICE="default"
    DEEPGRAM_API_KEY: str ="58c440889de2a574a10058a3fe66783fe87cd855"
    

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "allow"  # forbid is the default; you can change to "allow" if needed

@lru_cache()
def get_settings():
    return Settings()
