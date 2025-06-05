import re
import sys
import traceback
import torch
import torchaudio
from pathlib import Path
from typing import Dict, Tuple
import datetime
import streamlit as st
import threading
from queue import Queue
import os
os.environ["TORCHDYNAMO_DISABLE"] = "1"

# Configuration
CONFIG = {
    "model_type": "transformer",  # or "hybrid"
    "possible_paths": [
        Path.home() / "Desktop" / "Python" / "Zonos-for-windows",
        Path(__file__).parent
    ],
    "audio_refs": {
        "happy": "Happy_Ref.wav",
        "neutral": "Default_Ref.wav",
        "sweet": "Sweet_Ref.wav",
        "playful": "Playful_Ref.wav",
        "gross": "Gross_Ref.wav",
        "soft": "Soft_Ref.wav",
        "bratty": "Bratty_Ref.wav",
        "goth": "Goth_Ref.wav"
    },
    "audio_ref_dir": Path.home() / "Desktop" / "Python" / "FluffyAi" / "Audio" / "RefAudio",
    "output_dir": Path.home() / "Desktop" / "Python" / "FluffyAi" / "Audio" / "Output"
}


class VoiceService:
    def __init__(self, model_type="transformer"):
        """Initialize the TTS system"""
        self._model_type = model_type  # Store the model type
        self._initializing = False
        self._ready = False
        self._error = None
        self._init_queue = Queue()  # Initialize the queue
        self.config = CONFIG
        self.device = None
        self.model = None
        self.emotion_refs = None
        self.tts = False

        # Start initialization
        self._start_async_init()

    def _start_async_init(self):
        """Start asynchronous initialization"""
        if not self._initializing and not self._ready:
            self._initializing = True
            thread = threading.Thread(target=self._async_init, daemon=True)
            thread.start()

    def _async_init(self):
        """Actual initialization in background thread"""
        try:
            self._setup_imports()
            self.device = self._get_device()
            self.model = self._load_model(self._model_type)
            self.emotion_refs = self._load_emotion_refs()
            self._ensure_output_dir()
            self.tts = True
            self._ready = True
            print("VoiceService initialized successfully!")
            print("Available emotions:", list(self.emotion_refs.keys()))
        except Exception as e:
            self._error = str(e)
            print(f"VoiceService initialization failed: {e}")
        finally:
            self._initializing = False
            self._init_queue.put(self._ready)  # Signal completion with status
            st.rerun()  # Add this line to trigger Streamlit refresh

    def is_initializing(self):
        """Check if service is initializing"""
        return self._initializing

    def is_ready(self):
        """Check if service is ready to use"""
        return self._ready

    def get_error(self):
        """Get initialization error if any"""
        return self._error
    
    def wait_for_init(self, timeout=30):
        """Wait for initialization to complete (for sync operations)"""
        try:
            self._init_queue.get(timeout=timeout)
            return self._ready
        except:
            return False

    def ensure_voice_service(self):
        """Ensure voice service is initialized (lazy loading)"""
        if st.session_state.voice_service is None and not st.session_state.voice_initializing:
            try:
                st.session_state.voice_initializing = True
                st.session_state.voice_init_error = None

                # Show loading state if in a page that needs voice
                if st.session_state.page in ["voice", "chat"]:
                    with st.spinner("Initializing voice service..."):
                        st.session_state.voice_service = VoiceService()
                        st.session_state.voice_available = True
                else:
                    # Initialize silently for other pages
                    st.session_state.voice_service = VoiceService()
                    st.session_state.voice_available = True

            except Exception as e:
                st.session_state.voice_init_error = str(e)
                st.session_state.voice_available = False
                print(f"VoiceService initialization failed: {e}")
            finally:
                st.session_state.voice_initializing = False

        return st.session_state.voice_service

    def _setup_imports(self):
        """Handle imports with fallback paths"""
        try:
            from zonos.model import Zonos
            from zonos.conditioning import make_cond_dict
            from zonos.utils import DEFAULT_DEVICE
            global Zonos, make_cond_dict, DEFAULT_DEVICE
        except ImportError:
            for path in CONFIG['possible_paths']:
                if (path / "zonos").exists():
                    sys.path.insert(0, str(path))
                    try:
                        from zonos.model import Zonos
                        from zonos.conditioning import make_cond_dict
                        from zonos.utils import DEFAULT_DEVICE
                        global Zonos, make_cond_dict, DEFAULT_DEVICE
                        print(f"Successfully imported zonos from {path}")
                        break
                    except ImportError as e:
                        print(f"Failed to import from {path}: {e}")
                        continue
            else:
                raise ImportError("Could not find zonos package in any of the specified paths")

    def _get_device(self):
        """Get the appropriate torch device"""
        try:
            return DEFAULT_DEVICE
        except NameError:
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _load_model(self, model_type: str):
        """Load the Zonos model"""
        try:
            model = Zonos.from_pretrained(f"Zyphra/Zonos-v0.1-{model_type}", device=self.device)
            print(f"Successfully loaded {model_type} model on {self.device}")
            return model
        except Exception as e:
            print(f"Failed to load model: {e}")
            raise

    def _load_emotion_refs(self) -> Dict[str, Tuple[torch.Tensor, int]]:
        """Load all emotion reference audio files"""
        emotion_refs = {}
        for emotion, filename in CONFIG['audio_refs'].items():
            filepath = CONFIG['audio_ref_dir'] / filename
            if not filepath.exists():
                print(f"Warning: Reference audio file {filepath} not found for emotion {emotion}")
                continue

            try:
                wav, sr = torchaudio.load(filepath)
                emotion_refs[emotion] = (wav, sr)
                print(f"Loaded reference audio for {emotion}")
            except Exception as e:
                print(f"Failed to load {emotion} reference audio: {e}")

        if not emotion_refs:
            raise ValueError("No emotion reference audio files could be loaded")
        return emotion_refs

    def _ensure_output_dir(self):
        """Ensure the output directory exists"""
        CONFIG['output_dir'].mkdir(parents=True, exist_ok=True)

    def get_available_emotions(self):
        """Return list of available emotions"""
        try:
            emotions = list(self.emotion_refs.keys())
            return emotions
        except Exception as e:
            print(f"Error getting available emotions: {e}")
            return []

    def extract_dialogue(self, text: str) -> str:
        """
        Extract only the dialogue portions from text (content within quotation marks)
        Returns empty string if no dialogue found.
        """
        # Find all text between quotes (including nested quotes)
        dialogues = re.findall(r'"(.*?)"', text)

        # Join with pauses between dialogue segments
        processed = " ... ... ".join(dialogues)

        # If no dialogue found, return empty string
        return processed if processed.strip() else ""

    def generate_speech(self, text: str, emotion:str, dialogue_only: bool = True) -> str:
        """Generate speech from text with the selected emotion"""
        try:
            # Pre-process text if we only want dialogue
            if dialogue_only:
                processed_text = self.extract_dialogue(text)
                if not processed_text:
                    print("[INFO] No dialogue found in text - nothing to synthesize")
                    return None
                print(f"[DEBUG] Extracted dialogue: {processed_text}")
            else:
                processed_text = text

            print(f"\nGenerating speech from: {processed_text}")


            print(f"\n[DEBUG] Starting speech generation with emotion: {emotion}")

            # 1. Get reference audio
            print(f"[DEBUG] Getting reference audio for {emotion}")
            wav, sr = self.emotion_refs[emotion]
            print(f"[DEBUG] Reference audio shape: {wav.shape}, sample rate: {sr}")

            # 2. Create speaker embedding
            print("[DEBUG] Creating speaker embedding...")
            speaker = self.model.make_speaker_embedding(wav, sr)
            print(f"[DEBUG] Speaker embedding created. Type: {type(speaker)}")

            # 3. Prepare conditioning
            print("[DEBUG] Preparing conditioning...")
            cond_dict = make_cond_dict(
                text=processed_text,
                speaker=speaker,
                language="en-us"
            )
            print(f"[DEBUG] Conditioning dict: {cond_dict.keys()}")

            # 4. Prepare conditioning (additional step from working version)
            print("[DEBUG] Preparing final conditioning...")
            conditioning = self.model.prepare_conditioning(cond_dict)
            print(f"[DEBUG] Conditioning type: {type(conditioning)}")

            # 5. Generate speech codes
            print("[DEBUG] Generating speech codes...")
            codes = self.model.generate(conditioning)
            print(f"[DEBUG] Codes generated. Type: {type(codes)}, shape: {getattr(codes, 'shape', 'N/A')}")

            # 6. Decode to waveform
            print("[DEBUG] Decoding to waveform...")
            decoder_output = self.model.autoencoder.decode(codes)
            print(f"[DEBUG] Decoder output type: {type(decoder_output)}")

            # Handle different output types
            if isinstance(decoder_output, dict):
                print("[DEBUG] Decoder output is a dictionary. Keys:", decoder_output.keys())
                wavs = decoder_output.get('wav') or decoder_output.get('audio') or decoder_output.get('output')
                if wavs is None:
                    raise ValueError("Could not find waveform in decoder output dictionary")
            else:
                wavs = decoder_output

            print(f"[DEBUG] Waveform type: {type(wavs)}, shape: {getattr(wavs, 'shape', 'N/A')}")

            # Ensure proper tensor format
            if not isinstance(wavs, torch.Tensor):
                raise ValueError(f"Expected torch.Tensor, got {type(wavs)}")

            wavs = wavs.cpu()
            print(f"[DEBUG] After CPU move - shape: {wavs.shape}")

            # 7. Save output
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = CONFIG['output_dir'] / f"{emotion}_output_{timestamp}.wav"
            print(f"[DEBUG] Saving to: {output_path}")

            # Ensure correct shape [channels, samples]
            if len(wavs.shape) == 3:  # [batch, channels, samples]
                wavs = wavs[0]  # Take first in batch
            elif len(wavs.shape) == 2:  # [channels, samples]
                pass  # Already correct
            elif len(wavs.shape) == 1:  # [samples]
                wavs = wavs.unsqueeze(0)  # [1, samples]
            else:
                raise ValueError(f"Unexpected waveform shape: {wavs.shape}")

            torchaudio.save(str(output_path), wavs, self.model.autoencoder.sampling_rate)
            print(f"[SUCCESS] Generated speech saved to {output_path}")
            return str(output_path)

        except Exception as e:
            print(f"[ERROR] During speech generation: {e}", file=sys.stderr)
            print("[DEBUG] Exception details:", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            raise


# Add this method to the VoiceService class
def preview_voice(self, text: str, emotion: str) -> str:
    """Generate a voice preview with the given text and emotion"""
    try:
        # Generate the speech (reusing our existing method)
        output_path = self.generate_speech(text, emotion)
        return output_path
    except Exception as e:
        print(f"Error generating preview: {e}")
        raise

if __name__ == "__main__":
    try:
        # Initialize and run the TTS system
        tts = VoiceService(CONFIG["model_type"])

        # Example usage:
        emotions = tts.get_available_emotions()
        #print("Available emotions:", emotions)

        # Generate speech with the first available emotion
        if emotions:
            output_path = tts.generate_speech("Hello, this is a test.", emotions[0])
            print("Generated audio at:", output_path)
    except Exception as e:
        print(f"Failed to initialize Zonos TTS: {e}")
        sys.exit(1)