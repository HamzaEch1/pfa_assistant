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
        
        # Configuration avec améliorations
        self._whisper_model_name = os.getenv("WHISPER_MODEL_NAME", "small")  # Modèle amélioré
        self._max_audio_duration = int(os.getenv("MAX_AUDIO_DURATION", "300"))
        self._voice_language = os.getenv("VOICE_LANGUAGE", "fr")  # Français par défaut
        self._voice_quality = os.getenv("VOICE_QUALITY", "high")
        self._noise_reduction = os.getenv("VOICE_NOISE_REDUCTION", "true").lower() == "true"
        self._auto_gain = os.getenv("VOICE_AUTO_GAIN", "true").lower() == "true"
        self._voice_enhancement = os.getenv("VOICE_ENHANCEMENT", "true").lower() == "true"
        
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
    
    def _enhance_audio_quality(self, audio: AudioSegment) -> AudioSegment:
        """Améliore la qualité audio avec diverses techniques."""
        try:
            # 1. Normalisation du volume (auto-gain)
            if self._auto_gain:
                # Normaliser à -20dBFS pour éviter la saturation
                target_dBFS = -20
                change_in_dBFS = target_dBFS - audio.dBFS
                normalized_audio = audio.apply_gain(change_in_dBFS)
                logger.debug(f"Audio normalisé: {audio.dBFS:.1f}dBFS -> {normalized_audio.dBFS:.1f}dBFS")
                audio = normalized_audio
            
            # 2. Réduction de bruit simple (high-pass filter)
            if self._noise_reduction:
                # Filtre passe-haut pour réduire les bruits de fond basse fréquence
                audio = audio.high_pass_filter(80)  # Supprime les fréquences < 80Hz
                logger.debug("Filtre passe-haut appliqué (80Hz)")
            
            # 3. Amélioration de la clarté vocale
            if self._voice_enhancement:
                # Léger boost des fréquences vocales (300-3000Hz)
                # Note: pydub ne supporte pas directement l'EQ, mais on peut améliorer autrement
                
                # Compression douce pour réduire les variations dynamiques
                # Simule une compression en normalisant par segments
                chunk_length = 1000  # 1 seconde
                enhanced_chunks = []
                
                for i in range(0, len(audio), chunk_length):
                    chunk = audio[i:i + chunk_length]
                    if len(chunk) > 100:  # Éviter les chunks trop courts
                        # Normalisation douce de chaque chunk
                        if chunk.dBFS > -40:  # Seulement si le chunk contient du signal
                            target_chunk_dBFS = -25
                            gain_change = target_chunk_dBFS - chunk.dBFS
                            # Limiter le gain à ±6dB pour éviter la distorsion
                            gain_change = max(-6, min(6, gain_change))
                            chunk = chunk.apply_gain(gain_change)
                    enhanced_chunks.append(chunk)
                
                audio = enhanced_chunks[0]
                for chunk in enhanced_chunks[1:]:
                    audio += chunk
                logger.debug("Amélioration vocale appliquée")
            
            return audio
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'amélioration audio: {e}")
            return audio  # Retourner l'audio original en cas d'erreur
    
    def _convert_audio_format(self, input_path: str, output_path: str, target_format: str = "wav") -> str:
        """Convert audio file to the target format with quality enhancements."""
        try:
            # Load audio with pydub (supports many formats)
            audio = AudioSegment.from_file(input_path)
            
            # Appliquer les améliorations de qualité
            audio = self._enhance_audio_quality(audio)
            
            # Convert to mono and set optimal sample rate for Whisper
            if self._voice_quality == "high":
                sample_rate = 22050  # Meilleure qualité pour la reconnaissance vocale
            else:
                sample_rate = 16000  # Standard
                
            audio = audio.set_channels(1).set_frame_rate(sample_rate)
            
            # Check duration
            duration_seconds = len(audio) / 1000.0
            if duration_seconds > self._max_audio_duration:
                raise Exception(f"Audio too long: {duration_seconds:.1f}s (max: {self._max_audio_duration}s)")
            
            # Export in target format with optimal settings
            audio.export(output_path, format=target_format, 
                        parameters=["-acodec", "pcm_s16le", "-ar", str(sample_rate), "-ac", "1"])
            
            logger.info(f"Audio converted and enhanced: {input_path} -> {output_path} ({duration_seconds:.1f}s, {sample_rate}Hz)")
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
    
    def _post_process_transcription(self, text: str) -> str:
        """Post-traite la transcription pour corriger les erreurs courantes."""
        if not text:
            return text
        
        # Dictionnaire des corrections courantes pour le français bancaire
        corrections = [
            # Corrections spécifiques en premier (plus longues vers plus courtes)
            ("je vais savoir les chips", "je veux savoir les types"),
            ("cart de crédit", "carte de crédit"),
            ("compte courrant", "compte courant"),
            ("cart bancaire", "carte bancaire"),
            ("carte de credit", "carte de crédit"),
            ("carte de debit", "carte de débit"),
            ("je vais savoir", "je veux savoir"),
            ("je vai savoir", "je veux savoir"),
            ("à l'étype", "les types"),
            ("l'étype", "les types"),
            ("vais savoir", "veux savoir"),
            ("va savoir", "veux savoir"),
            ("carte 1K", "cartes"),
            ("banquaire", "bancaire"),
            ("existant", "existants"),
            ("étype", "types"),
            ("chips", "types"),
            ("chip", "type"),
        ]
        
        # Appliquer les corrections dans l'ordre (évite les collisions)
        processed_text = text
        for wrong, correct in corrections:
            if wrong in processed_text:
                processed_text = processed_text.replace(wrong, correct)
        
        # Nettoyage général
        processed_text = processed_text.strip()
        
        # Logger les corrections appliquées
        if processed_text != text:
            logger.info(f"Transcription corrigée: '{text}' -> '{processed_text}'")
        
        return processed_text
    
    def _calculate_confidence(self, whisper_result: Dict[str, Any]) -> str:
        """Calcule un score de confiance basé sur les résultats Whisper."""
        try:
            # Facteurs pour déterminer la confiance
            text_length = len(whisper_result.get("text", "").strip())
            duration = whisper_result.get("duration", 0)
            
            # Vérifier s'il y a des segments avec des informations de probabilité
            segments = whisper_result.get("segments", [])
            if segments:
                # Calculer la probabilité moyenne des segments
                avg_probability = sum(seg.get("avg_logprob", -1) for seg in segments) / len(segments)
                # Convertir logprob en score de confiance
                if avg_probability > -0.5:
                    confidence = "très_haute"
                elif avg_probability > -1.0:
                    confidence = "haute"
                elif avg_probability > -1.5:
                    confidence = "moyenne"
                else:
                    confidence = "faible"
            else:
                # Heuristique basée sur la longueur et la durée
                if text_length > 20 and duration > 2:
                    confidence = "haute"
                elif text_length > 10 and duration > 1:
                    confidence = "moyenne"
                else:
                    confidence = "faible"
            
            return confidence
            
        except Exception as e:
            logger.warning(f"Erreur lors du calcul de confiance: {e}")
            return "inconnue"
    
    async def transcribe_audio(self, audio_file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribe audio file to text using Whisper with enhancements.
        """
        # Check if voice processing is available (this raises an exception if not)
        self._check_voice_available()
            
        if not self.whisper_model:
            self._load_whisper_model()
        
        # Utiliser la langue configurée par défaut si non spécifiée
        effective_language = language or self._voice_language
        
        try:
            # First, try transcribing directly with Whisper (it can handle many formats)
            logger.info(f"Attempting direct transcription with Whisper for: {audio_file_path}")
            
            def transcribe_sync():
                transcribe_options = {
                    "language": effective_language if effective_language and effective_language != "auto" else None,
                    "fp16": False,  # Use fp32 for CPU
                    "verbose": False,
                    "word_timestamps": True,  # Pour une meilleure analyse
                    "condition_on_previous_text": False,  # Éviter la répétition de contexte incorrect
                }
                return self.whisper_model.transcribe(audio_file_path, **transcribe_options)
            
            # Run transcription in thread pool to avoid blocking
            result = await asyncio.get_event_loop().run_in_executor(
                self._executor, transcribe_sync
            )
            
            transcribed_text = result["text"].strip()
            detected_language = result.get("language", effective_language or "unknown")
            
            # Appliquer le post-processing
            processed_text = self._post_process_transcription(transcribed_text)
            
            # Log success
            logger.info(f"Direct Whisper transcription successful. Language: {detected_language}, Length: {len(processed_text)} chars")
            
            return {
                "text": processed_text,
                "original_text": transcribed_text,  # Garder l'original pour debug
                "language": detected_language,
                "duration": result.get("duration", 0),
                "confidence": self._calculate_confidence(result)
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
                        "language": effective_language if effective_language and effective_language != "auto" else None,
                        "fp16": False,
                        "verbose": False,
                        "word_timestamps": True,
                        "condition_on_previous_text": False,
                    }
                    return self.whisper_model.transcribe(converted_path, **transcribe_options)
                
                result = await asyncio.get_event_loop().run_in_executor(
                    self._executor, transcribe_converted_sync
                )
                
                transcribed_text = result["text"].strip()
                detected_language = result.get("language", effective_language or "unknown")
                
                # Appliquer le post-processing
                processed_text = self._post_process_transcription(transcribed_text)
                
                # Clean up converted file
                if os.path.exists(converted_path):
                    os.remove(converted_path)
                
                logger.info(f"Converted audio transcription successful. Language: {detected_language}, Length: {len(processed_text)} chars")
                
                return {
                    "text": processed_text,
                    "original_text": transcribed_text,
                    "language": detected_language,
                    "duration": result.get("duration", 0),
                    "confidence": self._calculate_confidence(result)
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
            
            # Better debugging for empty transcription avec des détails améliorés
            logger.info(f"Transcription result: '{transcribed_text}' (length: {len(transcribed_text)})")
            logger.info(f"Confidence: {transcription.get('confidence', 'unknown')}")
            logger.info(f"Language: {transcription.get('language', 'unknown')}")
            
            if transcription.get('original_text'):
                logger.info(f"Original (before correction): '{transcription.get('original_text')}'")
            
            if not transcribed_text.strip():
                # Provide more helpful error message
                import os
                file_size = os.path.getsize(audio_file_path) if os.path.exists(audio_file_path) else 0
                confidence = transcription.get('confidence', 'unknown')
                duration = transcription.get('duration', 0)
                
                error_msg = f"No speech detected in audio file. File size: {file_size} bytes, " \
                           f"Duration: {duration:.1f}s, Confidence: {confidence}. " \
                           f"Please ensure: 1) Microphone is working, 2) Audio contains clear speech, " \
                           f"3) Audio is not too quiet, 4) Recording duration is sufficient (>1 second), " \
                           f"5) Speak clearly in French"
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
            "voice_language": self._voice_language,
            "voice_quality": self._voice_quality,
            "noise_reduction": self._noise_reduction,
            "auto_gain": self._auto_gain,
            "voice_enhancement": self._voice_enhancement,
            "supported_formats": ["wav", "mp3", "m4a", "flac", "ogg", "webm"],
            "languages": len(self.get_supported_languages()),
            "enhancements": {
                "post_processing": True,
                "confidence_scoring": True,
                "audio_preprocessing": True,
                "french_banking_corrections": True
            }
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