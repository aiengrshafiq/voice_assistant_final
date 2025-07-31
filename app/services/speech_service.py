# app/services/speech_service.py
import asyncio
import os
import subprocess
import speech_recognition as sr
from gtts import gTTS
import requests
from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents, LiveOptions
from app.core.config import get_settings
from app.core.logger import get_logger
from app.services.audio_stream_service import AudioStreamService

logger = get_logger(__name__)
settings = get_settings()

def _speak_gtts(text: str, lang: str):
    try:
        logger.info(f"[gTTS] Speaking ({lang}): {text}")
        tts = gTTS(text=text, lang=lang)
        filename = "/tmp/jarvis_speak.mp3"
        tts.save(filename)
        subprocess.run(["mpg123", "-q", filename], check=True)
        os.remove(filename)
    except Exception as e:
        logger.exception(f"[TTS] gTTS fallback failed: {e}")

def _speak_elevenlabs(text: str, lang: str):
    if not settings.ELEVENLABS_API_KEY:
        logger.error("[TTS] ElevenLabs API key not configured.")
        return
    try:
        voice_map = {"en": settings.ELEVENLABS_VOICE_ID_EN, "ar": settings.ELEVENLABS_VOICE_ID_AR}
        voice_id = voice_map.get(lang, settings.ELEVENLABS_VOICE_ID_EN)
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream",
            headers={"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": settings.ELEVENLABS_API_KEY},
            json={"text": text, "model_id": "eleven_multilingual_v2"},
            stream=True
        )
        response.raise_for_status()
        player_process = subprocess.Popen(["mpg123", "-q", "-"], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for chunk in response.iter_content(chunk_size=4096):
            if chunk: player_process.stdin.write(chunk)
        player_process.stdin.close()
        player_process.wait()
    except Exception as e:
        logger.exception(f"[TTS] ElevenLabs streaming failed: {e}")

def speak(text: str, lang: str = "en"):
    _speak_gtts(text, lang)

def speak_translation(text: str, lang: str = "en"):
    _speak_elevenlabs(text, lang)

class StableSpeechToText:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    async def listen(self, timeout=7.0):
        try:
            with sr.Microphone(device_index=settings.MIC_DEVICE_INDEX, sample_rate=16000) as source:
                logger.info("(Stable STT) Adjusting/Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = await asyncio.to_thread(self.recognizer.listen, source, timeout=timeout)
                logger.info("(Stable STT) Recognizing...")
                text = await asyncio.to_thread(self.recognizer.recognize_google, audio)
                logger.info(f"[STT] Transcript received: '{text}'")
                return text.lower()
        except Exception as e:
            logger.error(f"An error occurred during Stable STT: {e}")
            return None

class FastSpeechToText:
    def __init__(self, audio_stream: AudioStreamService):
        config = DeepgramClientOptions(verbose=0, options={"keepalive": "true"})
        self.dg_client = DeepgramClient(settings.DEEPGRAM_API_KEY, config)
        self.transcript_queue = asyncio.Queue()
        self.audio_stream = audio_stream
        self.chunk_size = 512 * 8

    async def _on_message(self, result, **kwargs):
        transcript = result.channel.alternatives[0].transcript
        if len(transcript) > 0: await self.transcript_queue.put(transcript)

    async def listen(self, timeout=7.0):
        dg_connection = self.dg_client.listen.asynclive.v("1")
        dg_connection.on(LiveTranscriptionEvents.Transcript, self._on_message)
        options = LiveOptions(model="nova-2", language="en-US", smart_format=True, sample_rate=16000, encoding="linear16", channels=1)
        mic_task = None
        try:
            await dg_connection.start(options)
            logger.info("(Fast STT) Deepgram connection established. Listening...")
            async def microphone_stream():
                while True:
                    data = await asyncio.to_thread(self.audio_stream.read, self.chunk_size)
                    await dg_connection.send(data)
                    await asyncio.sleep(0.01)
            mic_task = asyncio.create_task(microphone_stream())
            transcript = await asyncio.wait_for(self.transcript_queue.get(), timeout=timeout)
            await dg_connection.finish()
            return transcript.lower()
        except Exception as e:
            logger.exception("An error occurred during Fast STT")
            if dg_connection: await dg_connection.finish()
            return None
        finally:
            if mic_task and not mic_task.done(): mic_task.cancel()