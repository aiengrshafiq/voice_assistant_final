import sounddevice as sd
import numpy as np
import argparse
import os
import soundfile as sf
from pathlib import Path
from resemblyzer import VoiceEncoder, preprocess_wav

# --- Configuration ---
RECORDING_SECONDS = 7
EMBEDDING_FILENAME = "ceo_voice_embedding.npy"
MODELS_DIR = Path(__file__).parent.parent / "models"
EMBEDDINGS_DIR = MODELS_DIR / "embeddings"
SAMPLE_RATE = 16000  # Resemblyzer works best with 16kHz
# ---

def record_audio(seconds: int) -> np.ndarray | None:
    """Records audio from the default microphone using sounddevice."""
    try:
        print("--------------------------------------------------")
        print(f"Starting voice enrollment recording for {seconds} seconds...")
        print("Say something like: 'Hi, my name is [Your Name] and this is my voice for the Jarvis assistant.'")
        print("--------------------------------------------------")

        # Record audio
        recording = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
        sd.wait()  # Wait until recording is finished

        print("Recording finished.")
        # The recording is already a numpy array, which is perfect.
        return recording.flatten()

    except Exception as e:
        print(f"\n❌ ERROR: Failed to record audio programmatically.")
        print(f"   Details: {e}")
        print("\n--- TROUBLESHOOTING ---")
        print("This often happens on Raspberry Pi due to audio configuration issues.")
        print("As a fallback, you can record a file manually and use the --input-file option.")
        print("Example Manual Recording Command:")
        print(f"  arecord -d {seconds} -f S16_LE -r {SAMPLE_RATE} my_enrollment.wav")
        print("\nThen run this script again with:")
        print("  python scripts/enroll_voice.py --input-file my_enrollment.wav")
        print("---------------------------\n")
        return None

def create_embedding(wav: np.ndarray, embedding_path: Path):
    """Creates a voice embedding from an audio waveform and saves it."""
    print("Processing audio to create voice embedding...")
    encoder = VoiceEncoder()
    
    # Resemblyzer's preprocess_wav handles normalization if needed, but our input is good.
    # We can pass the numpy array directly.
    embedding = encoder.embed_utterance(wav)
    
    np.save(embedding_path, embedding)
    print(f"✅ Success! Voice embedding saved to: {embedding_path}")

def main(args):
    """Main function to run the enrollment process."""
    if not EMBEDDINGS_DIR.exists():
        print(f"Creating directory: {EMBEDDINGS_DIR}")
        EMBEDDINGS_DIR.mkdir(parents=True)
        
    embedding_file = EMBEDDINGS_DIR / EMBEDDING_FILENAME
    audio_waveform = None

    if args.input_file:
        # --- Workflow 1: Use a pre-recorded file ---
        print(f"Loading audio from specified file: {args.input_file}")
        try:
            audio_waveform, sr = sf.read(args.input_file, dtype='float32')
            if sr != SAMPLE_RATE:
                # This is less ideal, resampling can introduce artifacts.
                # For best results, record at 16kHz directly.
                print(f"Warning: Audio file sample rate is {sr}Hz, not {SAMPLE_RATE}Hz. Resampling is not yet implemented. Please record at 16kHz.")
                # For now, we will exit if the sample rate is wrong.
                return 
            
            # Ensure mono
            if audio_waveform.ndim > 1:
                audio_waveform = audio_waveform.mean(axis=1)

        except Exception as e:
            print(f"❌ ERROR: Could not read or process the audio file: {e}")
            return
    else:
        # --- Workflow 2: Attempt to record programmatically ---
        audio_waveform = record_audio(RECORDING_SECONDS)

    if audio_waveform is not None:
        create_embedding(audio_waveform, embedding_file)
        print("\nEnrollment complete. You can now start the main assistant.")
    else:
        print("\nEnrollment process could not be completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enroll a user's voice by recording or using a pre-existing audio file.")
    parser.add_argument(
        "--input-file",
        "-i",
        type=str,
        help="Path to a .wav file to use for enrollment instead of recording live."
    )
    args = parser.parse_args()
    main(args)