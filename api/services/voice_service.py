# api/services/voice_service.py
import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    import whisper
    from pydub import AudioSegment
    from pydub.utils import which
    import librosa
    import soundfile as sf
    VOICE_AVAILABLE = True
    
    # Configure ffmpeg path for pydub
    AudioSegment.converter = "/usr/bin/ffmpeg"
    AudioSegment.ffmpeg = "/usr/bin/ffmpeg"
    
except ImportError as e:
    logging.warning(f"Voice dependencies not available: {e}")
    VOICE_AVAILABLE = False

from . import rag_service, chat_service

logger = logging.getLogger(__name__)

class VoiceService:
    """Service for handling speech-to-text and RAG integration."""
    
    def __init__(self):
        """Initialize the voice service with Whisper model."""
        self.whisper_model = None
        self.audio_dir = Path("user_files/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self._whisper_model_name = os.getenv("WHISPER_MODEL_NAME", "base")
        self._max_audio_duration = int(os.getenv("MAX_AUDIO_DURATION", "300"))  # 5 minutes
        
        # Thread pool for CPU-intensive tasks
        self._executor = ThreadPoolExecutor(max_workers=2)
        
        if not VOICE_AVAILABLE:
            logger.warning("Voice processing not available - missing dependencies")
    
    def _check_voice_available(self):
        """Check if voice processing is available."""
        if not VOICE_AVAILABLE:
            raise Exception("Voice processing not available - please install voice dependencies")
    
    def _load_whisper_model(self):
        """Load Whisper model if not already loaded."""
        if self.whisper_model is None:
            self._check_voice_available()
            logger.info(f"Loading Whisper model: {self._whisper_model_name}")
            try:
                self.whisper_model = whisper.load_model(self._whisper_model_name)
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise
    
    def _convert_audio_format(self, input_path: str, output_path: str, target_format: str = "wav") -> str:
        """Convert audio file to the target format."""
        try:
            # Load audio with pydub (supports many formats)
            audio = AudioSegment.from_file(input_path)
            
            # Convert to mono and set sample rate to 16kHz (good for Whisper)
            audio = audio.set_channels(1).set_frame_rate(16000)
            
            # Check duration
            duration_seconds = len(audio) / 1000.0
            if duration_seconds > self._max_audio_duration:
                raise Exception(f"Audio too long: {duration_seconds:.1f}s (max: {self._max_audio_duration}s)")
            
            # Export in target format
            audio.export(output_path, format=target_format)
            logger.info(f"Audio converted from {input_path} to {output_path} ({duration_seconds:.1f}s)")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to convert audio format: {e}")
            # If conversion fails, try with librosa as fallback
            try:
                y, sr = librosa.load(input_path, sr=16000, mono=True)
                duration_seconds = len(y) / sr
                
                if duration_seconds > self._max_audio_duration:
                    raise Exception(f"Audio too long: {duration_seconds:.1f}s (max: {self._max_audio_duration}s)")
                
                sf.write(output_path, y, sr)
                logger.info(f"Audio converted using librosa fallback ({duration_seconds:.1f}s)")
                return output_path
            except Exception as librosa_e:
                logger.error(f"Librosa fallback also failed: {librosa_e}")
                raise
    
    def _transcribe_audio_sync(self, audio_file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Synchronous transcription function for threading."""
        self._load_whisper_model()
        
        # Create a temporary WAV file for processing
        temp_wav = None
        processing_file = audio_file_path
        
        # Convert to WAV if necessary
        if not audio_file_path.lower().endswith('.wav'):
            temp_wav = tempfile.mktemp(suffix='.wav')
            processing_file = self._convert_audio_format(audio_file_path, temp_wav)
        
        # Transcribe audio
        logger.info(f"Transcribing audio file: {processing_file}")
        
        # Prepare transcription options
        transcribe_options = {
            "fp16": False,  # Use FP32 for better compatibility
            "verbose": False
        }
        
        if language:
            transcribe_options["language"] = language
        
        result = self.whisper_model.transcribe(processing_file, **transcribe_options)
        
        # Clean up temporary file
        if temp_wav and os.path.exists(temp_wav):
            os.remove(temp_wav)
        
        return result
    
    async def transcribe_audio(self, audio_file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribe audio file to text using Whisper.
        """
        # Check if voice processing is available (this raises an exception if not)
        self._check_voice_available()
            
        if not self.whisper_model:
            self._load_whisper_model()
        
        try:
            # First, try transcribing directly with Whisper (it can handle many formats)
            logger.info(f"Attempting direct transcription with Whisper for: {audio_file_path}")
            
            def transcribe_sync():
                transcribe_options = {
                    "language": language if language and language != "auto" else None,
                    "fp16": False,  # Use fp32 for CPU
                    "verbose": False
                }
                return self.whisper_model.transcribe(audio_file_path, **transcribe_options)
            
            # Run transcription in thread pool to avoid blocking
            result = await asyncio.get_event_loop().run_in_executor(
                self._executor, transcribe_sync
            )
            
            transcribed_text = result["text"].strip()
            detected_language = result.get("language", language or "unknown")
            
            # Log success
            logger.info(f"Direct Whisper transcription successful. Language: {detected_language}, Length: {len(transcribed_text)} chars")
            
            return {
                "text": transcribed_text,
                "language": detected_language,
                "duration": result.get("duration", 0)
            }
            
        except Exception as direct_error:
            logger.warning(f"Direct Whisper transcription failed: {direct_error}")
            logger.info("Attempting audio format conversion...")
            
            # If direct transcription fails, try converting format first
            try:
                # Convert to WAV format that Whisper definitely supports
                converted_path = self._convert_audio_format(audio_file_path, "wav")
                
                def transcribe_converted_sync():
                    transcribe_options = {
                        "language": language if language and language != "auto" else None,
                        "fp16": False,
                        "verbose": False
                    }
                    return self.whisper_model.transcribe(converted_path, **transcribe_options)
                
                result = await asyncio.get_event_loop().run_in_executor(
                    self._executor, transcribe_converted_sync
                )
                
                transcribed_text = result["text"].strip()
                detected_language = result.get("language", language or "unknown")
                
                # Clean up converted file
                if os.path.exists(converted_path):
                    os.remove(converted_path)
                
                logger.info(f"Converted audio transcription successful. Language: {detected_language}, Length: {len(transcribed_text)} chars")
                
                return {
                    "text": transcribed_text,
                    "language": detected_language,
                    "duration": result.get("duration", 0)
                }
                
            except Exception as convert_error:
                logger.error(f"Audio conversion and transcription failed: {convert_error}")
                raise Exception(f"Failed to transcribe audio: {str(convert_error)}")
                
        except Exception as e:
            logger.error(f"Failed to transcribe audio: {e}")
            raise Exception(f"Speech-to-text failed: {str(e)}")
    
    async def process_voice_conversation(
        self, 
        audio_file_path: str, 
        user_id: str,
        conversation_id: Optional[str] = None,
        language: Optional[str] = None,
        embedding_model=None,
        qdrant_client=None,
        ollama_client=None
    ) -> Dict[str, Any]:
        """
        Complete voice conversation workflow: transcribe → RAG → response.
        
        Args:
            audio_file_path: Path to the audio file
            user_id: User identifier
            conversation_id: Optional conversation ID
            language: Language code for transcription
            embedding_model: SentenceTransformer model
            qdrant_client: Qdrant client
            ollama_client: Ollama client
            
        Returns:
            Dictionary with transcription, RAG response, and metadata
        """
        try:
            # Step 1: Transcribe audio to text
            logger.info("Step 1: Transcribing audio...")
            transcription = await self.transcribe_audio(audio_file_path, language)
            transcribed_text = transcription["text"]
            
            # Better debugging for empty transcription
            logger.info(f"Transcription result: '{transcribed_text}' (length: {len(transcribed_text)})")
            
            if not transcribed_text.strip():
                # Provide more helpful error message
                import os
                file_size = os.path.getsize(audio_file_path) if os.path.exists(audio_file_path) else 0
                error_msg = f"No speech detected in audio file. File size: {file_size} bytes. " \
                           f"Please ensure: 1) Microphone is working, 2) Audio contains speech, " \
                           f"3) Audio is not too quiet, 4) Recording duration is sufficient (>1 second)"
                logger.warning(error_msg)
                raise Exception(error_msg)
            
            # Step 2: Process through RAG system
            logger.info("Step 2: Processing through RAG system...")
            
            # Use the rag_service module functions directly
            if embedding_model and qdrant_client and ollama_client:
                assistant_response = await rag_service.get_rag_response(
                    user_query=transcribed_text,
                    embedding_model=embedding_model,
                    qdrant_client=qdrant_client,
                    ollama_client=ollama_client,
                    conversation_history=None,
                    file_context=None
                )
            else:
                # Fallback response if services not available
                assistant_response = f"I heard you say: '{transcribed_text}'. Voice processing is working, but RAG services need to be properly initialized for full conversation."
            
            # Step 3: Save to conversation history (if available)
            logger.info("Step 3: Saving to conversation history...")
            try:
                # For now, we'll skip saving to avoid dependency issues
                logger.info("Conversation history saving skipped in voice service")
            except Exception as e:
                logger.warning(f"Failed to save conversation history: {e}")
            
            # Clean up audio file
            self.cleanup_audio_file(audio_file_path)
            
            return {
                "transcription": transcription,
                "rag_response": {"response": assistant_response},
                "user_message": transcribed_text,
                "assistant_response": assistant_response,
                "conversation_id": conversation_id,
                "metadata": {
                    "processing_time": transcription.get("duration", 0),
                    "language": transcription["language"],
                    "confidence": "high" if len(transcribed_text) > 10 else "medium"
                }
            }
            
        except Exception as e:
            logger.error(f"Voice conversation processing failed: {e}")
            # Clean up on error
            self.cleanup_audio_file(audio_file_path)
            raise Exception(f"Voice conversation failed: {str(e)}")
    
    def cleanup_audio_file(self, file_path: str):
        """Clean up temporary audio files."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up audio file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup audio file {file_path}: {e}")
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages."""
        if not VOICE_AVAILABLE:
            return {}
        
        try:
            import whisper.tokenizer
            return dict(whisper.tokenizer.LANGUAGES.items())
        except:
            return {
                "en": "English",
                "fr": "French", 
                "es": "Spanish",
                "de": "German",
                "it": "Italian"
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        if not VOICE_AVAILABLE:
            return {"available": False, "reason": "Voice dependencies not installed"}
        
        info = {
            "available": True,
            "model_name": self._whisper_model_name,
            "max_duration": self._max_audio_duration,
            "supported_formats": ["wav", "mp3", "m4a", "flac", "ogg"],
            "languages": len(self.get_supported_languages())
        }
        
        if self.whisper_model:
            info.update({
                "loaded": True,
                "device": str(self.whisper_model.device),
                "model_dims": str(self.whisper_model.dims) if hasattr(self.whisper_model, 'dims') else "unknown"
            })
        else:
            info["loaded"] = False
        
        return info

# Global voice service instance
voice_service = VoiceService() 