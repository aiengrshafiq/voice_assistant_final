# app/services/speech_service.py
import asyncio
import os
import subprocess
import pyaudio
import wave
import speech_recognition as sr
from gtts import gTTS
from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents, LiveOptions
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

def speak(text: str):
    """Uses gTTS and mpg123 for the most reliable audio output."""
    try:
        logger.info(f"[TTS] Speaking: {text}")
        tts = gTTS(text=text, lang="en")
        filename = "/tmp/jarvis_speak.mp3"
        tts.save(filename)
        subprocess.run(["mpg123", "-q", filename], check=True)
        os.remove(filename)
    except Exception as e:
        logger.error(f"[TTS] gTTS/mpg123 failed: {e}")

# --- STABLE SPEECH-TO-TEXT ENGINE ---
class StableSpeechToText:
    """Uses the robust speech_recognition library. Reliable but slower."""
    def __init__(self):
        self.recognizer = sr.Recognizer()

    async def listen(self, timeout=7.0):
        try:
            with sr.Microphone(device_index=settings.MIC_DEVICE_INDEX) as source:
                logger.info("(Stable STT) Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                logger.info("(Stable STT) Listening for command...")
                
                audio = await asyncio.to_thread(
                    self.recognizer.listen, source, timeout=timeout, phrase_time_limit=10
                )
                
                logger.info("(Stable STT) Recognizing speech with Whisper...")
                text = await asyncio.to_thread(
                    self.recognizer.recognize_whisper, audio, language="english", model="base.en"
                )
                logger.info(f"[STT] Transcript received: '{text}'")
                return text.lower()
        except Exception as e:
            logger.error(f"An error occurred during Stable STT: {e}")
            return None

# --- EXPERIMENTAL FAST SPEECH-TO-TEXT ENGINE ---
class FastSpeechToText:
    """Uses Deepgram's streaming service. Fast but can be sensitive to hardware."""
    def __init__(self):
        config = DeepgramClientOptions(verbose=0)
        self.dg_client = DeepgramClient(settings.DEEPGRAM_API_KEY, config)
        self.transcript_queue = asyncio.Queue()

    async def _on_message(self, result, **kwargs):
        transcript = result.channel.alternatives[0].transcript
        if len(transcript) > 0:
            logger.info(f"[STT] Transcript received: '{transcript}'")
            await self.transcript_queue.put(transcript)

    async def listen(self, timeout=7.0):
        dg_connection = self.dg_client.listen.asynclive.v("1")
        dg_connection.on(LiveTranscriptionEvents.Transcript, self._on_message)
        options = LiveOptions(model="nova-2", language="en-US", smart_format=True)
        
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16, channels=1, rate=16000, input=True,
            input_device_index=settings.MIC_DEVICE_INDEX, frames_per_buffer=4096
        )
        mic_task = None
        try:
            await dg_connection.start(options)
            logger.info("(Fast STT) Deepgram connection established. Listening...")
            
            async def microphone_stream():
                while True:
                    data = await asyncio.to_thread(stream.read, 4096)
                    await dg_connection.send(data)
                    await asyncio.sleep(0.01)

            mic_task = asyncio.create_task(microphone_stream())
            transcript = await asyncio.wait_for(self.transcript_queue.get(), timeout=timeout)
            await dg_connection.finish()
            return transcript.lower()
        except Exception as e:
            logger.error(f"An error occurred during Fast STT: {e}")
            await dg_connection.finish()
            return None
        finally:
            if mic_task: mic_task.cancel()
            stream.stop_stream(); stream.close(); pa.terminate()

# --- SELECT THE ENGINE BASED ON THE .ENV TOGGLE ---
if settings.USE_EXPERIMENTAL_STT:
    logger.info("🚀 EXPERIMENTAL FAST MODE ENABLED: Using Deepgram for STT.")
    stt_service = FastSpeechToText()
else:
    logger.info("✅ STABLE MODE ENABLED: Using local Whisper for STT.")
    stt_service = StableSpeechToText()

# --- SHARED FUNCTIONS ---
async def confirm_action(timeout=5.0):
    response = await stt_service.listen(timeout=timeout)
    return response and any(word in response.lower() for word in ["yes", "yeah", "confirm", "correct"])