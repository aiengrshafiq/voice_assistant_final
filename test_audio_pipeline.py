import speech_recognition as sr
import pyttsx3
import subprocess
import os
from time import sleep

# === CONFIG ===
MIC_DEVICE_INDEX = 0  # Update based on `pyaudio` results
SPEAKER_DEVICE = "plughw:2,0"  # Replace if needed (e.g., for USB/Bluetooth)
OUTPUT_FILE = "output_test.wav"

def record_and_transcribe():
    r = sr.Recognizer()

    with sr.Microphone(device_index=MIC_DEVICE_INDEX) as source:
        print("🎙️  Listening... Speak clearly.")
        r.adjust_for_ambient_noise(source)
        try:
            audio = r.listen(source, timeout=5)
            print("🧠 Transcribing...")
            text = r.recognize_google(audio)
            print(f"✅ You said: {text}")
            return text
        except sr.WaitTimeoutError:
            print("⚠️ No speech detected.")
        except sr.UnknownValueError:
            print("❌ Could not understand audio.")
        except sr.RequestError as e:
            print(f"❌ Could not request results: {e}")
        return None

def speak(text):
    try:
        print(f"🗣️ Responding with: {text}")
        engine = pyttsx3.init()
        engine.setProperty('rate', 160)
        engine.setProperty('volume', 1.0)
        engine.save_to_file(text, OUTPUT_FILE)
        engine.runAndWait()
        sleep(0.5)
        subprocess.run(["aplay", "-D", SPEAKER_DEVICE, OUTPUT_FILE], check=True)
    except Exception as e:
        print(f"❌ TTS error: {e}")

if __name__ == "__main__":
    print("🔁 Starting Audio Pipeline Test")
    result = record_and_transcribe()
    if result:
        speak(f"You said: {result}")
    else:
        speak("Sorry, I could not understand what you said.")
