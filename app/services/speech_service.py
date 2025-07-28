# app/services/speech_service.py
import asyncio
import pyaudio
import piper
from piper import PiperVoice
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# --- Text-to-Speech (TTS) Setup ---
try:
    # Download a voice from: https://rhasspy.github.io/piper-samples/
    # Place the .onnx and .onnx.json files in 'models/tts/'
    model_path = "models/tts/en_US-lessac-medium.onnx"
    voice = PiperVoice.load(model_path)
    tts_audio = pyaudio.PyAudio()
    logger.info("Piper TTS engine initialized successfully.")
except Exception as e:
    voice = None
    logger.error(f"Could not initialize Piper TTS: {e}. TTS will fall back to printing.")

def speak(text: str):
    """Uses local Piper TTS for fast speech, with a print fallback."""
    logger.info(f"[TTS] Speaking: '{text}'")
    if not voice:
        print(f"[Fallback TTS]: {text}")
        return
    try:
        stream = tts_audio.open(
            format=tts_audio.get_format_from_width(voice.config.sample_width),
            channels=voice.config.num_channels,
            rate=voice.config.sample_rate,
            output=True
        )
        for audio_bytes in voice.synthesize_stream_raw(text):
            stream.write(audio_bytes)
        stream.stop_stream()
        stream.close()
    except Exception as e:
        logger.error(f"Piper TTS playback failed: {e}")
        print(f"[Fallback TTS]: {text}")

# --- Speech-to-Text (STT) Setup using Deepgram ---
class SpeechToText:
    def __init__(self):
        self.dg_client = DeepgramClient(settings.DEEPGRAM_API_KEY)
        self.transcript_queue = asyncio.Queue()
        self.is_listening = False
        self.audio = pyaudio.PyAudio()
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000 # Deepgram prefers 16000Hz

    async def _on_message(self, *args, **kwargs):
        transcript = kwargs['channel']['alternatives'][0]['transcript']
        if len(transcript) > 0:
            logger.info(f"[STT] Final transcript received: '{transcript}'")
            await self.transcript_queue.put(transcript)

    async def _microphone_stream(self, dg_connection):
        """Captures audio and sends it to Deepgram."""
        mic_stream = self.audio.open(
            format=self.format, channels=self.channels, rate=self.rate,
            input=True, frames_per_buffer=self.chunk
        )
        logger.info("🎤 Microphone stream opened.")
        while self.is_listening:
            data = mic_stream.read(self.chunk, exception_on_overflow=False)
            await dg_connection.send(data)
            await asyncio.sleep(0.01) # Yield control
        
        mic_stream.stop_stream()
        mic_stream.close()
        logger.info("🎤 Microphone stream closed.")

    async def listen(self, timeout=7.0):
        """Listens for a single utterance and returns the transcript."""
        options = LiveOptions(
            model="nova-2-general", language="en-US", smart_format=True,
            encoding="linear16", channels=1, sample_rate=self.rate,
            endpointing="300", # End speech after 300ms of silence
        )
        try:
            dg_connection = self.dg_client.listen.asynclive.v("1")
            dg_connection.on(LiveTranscriptionEvents.Transcript, self._on_message)
            await dg_connection.start(options)
            logger.info("Deepgram connection established. Listening...")
            
            self.is_listening = True
            mic_task = asyncio.create_task(self._microphone_stream(dg_connection))

            # Wait for a transcript from the queue
            transcript = await asyncio.wait_for(self.transcript_queue.get(), timeout=timeout)
            
            self.is_listening = False
            await mic_task # Ensure microphone task finishes
            await dg_connection.finish()
            
            return transcript
        except asyncio.TimeoutError:
            logger.warning("STT listening timed out.")
            self.is_listening = False
            return None
        except Exception as e:
            logger.error(f"An error occurred during STT: {e}")
            self.is_listening = False
            return None

stt_service = SpeechToText()

# --- Unified Command Functions ---
async def listen_command():
    return await stt_service.listen()

async def confirm_action(timeout=5.0):
    """Listens for a confirmation (yes/no)."""
    response = await stt_service.listen(timeout=timeout)
    if response:
        return "yes" in response.lower() or "yeah" in response.lower() or "confirm" in response.lower()
    return False