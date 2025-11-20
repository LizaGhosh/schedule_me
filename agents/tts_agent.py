"""Agent for text-to-speech using ElevenLabs."""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import constants

load_dotenv()


class TTSAgent:
    """Handles text-to-speech using ElevenLabs."""
    
    def __init__(self):
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in environment variables")
        
        try:
            from elevenlabs.client import ElevenLabs
            self.client = ElevenLabs(api_key=api_key)
            self.client_available = True
            self.api_key = api_key
            print("TTS Agent initialized successfully")
        except ImportError:
            self.client_available = False
            print("Warning: elevenlabs package not installed. TTS will be disabled.")
            print("Install with: pip install elevenlabs")
        except Exception as e:
            self.client_available = False
            print(f"Warning: TTS Agent initialization failed: {e}")
    
    def generate_audio(self, text: str, voice_id: str = None, model: str = None) -> bytes:
        """
        Generate audio from text using ElevenLabs.
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID (uses constant or default if None)
            model: Model to use (uses constant or default if None)
        
        Returns:
            Audio bytes (MP3 format)
        """
        if not self.client_available:
            return None
        
        try:
            voice_id = voice_id or constants.ELEVENLABS_VOICE_ID
            model = model or constants.ELEVENLABS_MODEL
            
            # Use default voice ID if none specified
            # You can get voice IDs from https://elevenlabs.io/app/voices
            voice_to_use = voice_id if voice_id else constants.ELEVENLABS_VOICE_ID
            
            print(f"Generating audio with voice ID: {voice_to_use}, model: {model}")
            print(f"Text length: {len(text)} characters")
            
            # Use text_to_speech.convert which doesn't require voices_read permission
            # Use newer model compatible with free tier
            model_to_use = model if model else constants.ELEVENLABS_MODEL
            
            audio_generator = self.client.text_to_speech.convert(
                voice_id=voice_to_use,
                text=text,
                model_id=model_to_use,
                output_format="mp3_44100_128"  # MP3 format for web compatibility
            )
            
            # Convert generator/stream to bytes
            print("Converting audio generator to bytes...")
            audio_chunks = []
            for chunk in audio_generator:
                audio_chunks.append(chunk)
            
            audio = b''.join(audio_chunks)
            
            if audio:
                print(f"Generated {len(audio)} bytes of audio")
            else:
                print("Warning: Generated audio is empty")
            
            return audio
            
        except Exception as e:
            print(f"Error generating audio: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_audio(self, audio_bytes: bytes, filepath: str) -> bool:
        """
        Save audio bytes to file.
        
        Args:
            audio_bytes: Audio data
            filepath: Path to save file
        
        Returns:
            True if successful, False otherwise
        """
        if not audio_bytes:
            return False
        
        try:
            with open(filepath, 'wb') as f:
                f.write(audio_bytes)
            return True
        except Exception as e:
            print(f"Error saving audio: {e}")
            return False

