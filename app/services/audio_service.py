"""Audio processing and transcription service - ENHANCED"""
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class AudioService:
    """Service for processing audio grievances"""
    
    def __init__(self):
        self.supported_formats = ['mp3', 'wav', 'm4a', 'ogg', 'webm', 'flac']
        self.max_duration = 300  # 5 minutes max
        self.max_file_size = 25 * 1024 * 1024  # 25 MB (Groq limit)
    
    async def transcribe_audio(self, audio_data: bytes, language: str = "auto") -> dict:
        """
        Transcribe audio to text using Groq Whisper API
        
        Args:
            audio_data: Raw audio bytes
            language: Language code (auto, te for Telugu, en for English)
            
        Returns:
            Dictionary with transcription results
        """
        try:
            logger.info(f"🎤 Starting audio transcription (language: {language})")
            
            # Check file size
            if len(audio_data) > self.max_file_size:
                logger.error(f"❌ Audio file too large: {len(audio_data)} bytes")
                return {
                    "success": False,
                    "text": None,
                    "error": f"Audio file too large. Max size: {self.max_file_size / 1024 / 1024} MB"
                }
            
            # Use Groq Whisper API if configured
            if settings.LLM_PROVIDER == "groq" and settings.GROQ_API_KEY:
                logger.info("✅ Using Groq Whisper API for transcription")
                return await self._transcribe_with_groq(audio_data, language)
            else:
                # Try local Whisper as fallback
                logger.warning("⚠️ Groq not configured, trying local Whisper")
                return await self._transcribe_with_local_whisper(audio_data, language)
                
        except Exception as e:
            logger.error(f"❌ Error transcribing audio: {e}", exc_info=True)
            return {
                "success": False,
                "text": None,
                "error": str(e)
            }
    
    async def _transcribe_with_groq(self, audio_data: bytes, language: str) -> dict:
        """
        Transcribe using Groq's Whisper API (Fast and Free Tier Available)
        
        Args:
            audio_data: Audio bytes
            language: Language code
            
        Returns:
            Transcription result
        """
        try:
            from groq import Groq
            import tempfile
            import os
            
            logger.info("🚀 Initializing Groq client")
            client = Groq(api_key=settings.GROQ_API_KEY)
            
            # Groq API requires file path, so save temporarily
            # Detect audio format from first few bytes (magic numbers)
            file_extension = self._detect_audio_format(audio_data)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name
            
            logger.info(f"💾 Saved audio to temp file: {tmp_path}")
            
            try:
                # Call Groq Whisper API
                with open(tmp_path, 'rb') as audio_file:
                    logger.info("📡 Calling Groq Whisper API...")
                    
                    # Map language codes
                    lang_param = None
                    if language == "te":
                        lang_param = "te"  # Telugu
                    elif language == "en":
                        lang_param = "en"  # English
                    # If "auto", leave as None for auto-detection
                    
                    transcription = client.audio.transcriptions.create(
                        model="whisper-large-v3",  # Most accurate Whisper model
                        file=audio_file,
                        language=lang_param,
                        response_format="verbose_json",  # Get detailed info
                        temperature=0.0  # More deterministic
                    )
                
                # Extract text from response
                text = transcription.text if hasattr(transcription, 'text') else str(transcription)
                detected_lang = transcription.language if hasattr(transcription, 'language') else language
                
                logger.info(f"✅ Groq transcription successful: {len(text)} chars, language: {detected_lang}")
                
                return {
                    "success": True,
                    "text": text.strip(),
                    "language": detected_lang,
                    "duration": getattr(transcription, 'duration', None),
                    "error": None
                }
                
            finally:
                # Clean up temporary file
                try:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                        logger.info("🗑️ Cleaned up temp file")
                except Exception as e:
                    logger.warning(f"⚠️ Could not delete temp file: {e}")
            
        except ImportError:
            logger.error("❌ Groq library not installed. Run: pip install groq")
            return {
                "success": False,
                "text": None,
                "error": "Groq library not installed. Install with: pip install groq"
            }
        except Exception as e:
            logger.error(f"❌ Groq transcription error: {e}", exc_info=True)
            return {
                "success": False,
                "text": None,
                "error": f"Groq API error: {str(e)}"
            }
    
    async def _transcribe_with_local_whisper(self, audio_data: bytes, language: str) -> dict:
        """
        Fallback: Try local Whisper model (requires more setup)
        
        Args:
            audio_data: Audio bytes
            language: Language code
            
        Returns:
            Transcription result
        """
        try:
            import whisper
            import tempfile
            import os
            
            logger.info("🏠 Using local Whisper model")
            
            # Load model (this will download on first use)
            model = whisper.load_model("base")  # Options: tiny, base, small, medium, large
            
            # Save audio temporarily
            file_extension = self._detect_audio_format(audio_data)
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name
            
            try:
                # Transcribe
                lang_param = "te" if language == "te" else "en" if language == "en" else None
                
                result = model.transcribe(
                    tmp_path,
                    language=lang_param,
                    fp16=False  # Use FP32 for CPU compatibility
                )
                
                text = result.get("text", "")
                detected_lang = result.get("language", language)
                
                logger.info(f"✅ Local Whisper transcription: {len(text)} chars")
                
                return {
                    "success": True,
                    "text": text.strip(),
                    "language": detected_lang,
                    "error": None
                }
                
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            
        except ImportError:
            logger.error("❌ Local Whisper not installed. Run: pip install openai-whisper")
            return {
                "success": False,
                "text": None,
                "error": "Audio transcription not available. Please configure Groq API or install Whisper."
            }
        except Exception as e:
            logger.error(f"❌ Local Whisper error: {e}")
            return {
                "success": False,
                "text": None,
                "error": f"Local Whisper error: {str(e)}"
            }
    
    def _detect_audio_format(self, audio_data: bytes) -> str:
        """
        Detect audio format from magic numbers (file signature)
        
        Args:
            audio_data: Audio bytes
            
        Returns:
            File extension (mp3, wav, m4a, etc.)
        """
        # Check magic numbers (first few bytes)
        if len(audio_data) < 12:
            return 'mp3'  # Default
        
        header = audio_data[:12]
        
        # MP3: FF FB or FF F3 or FF F2 or ID3
        if header[:2] in [b'\xff\xfb', b'\xff\xf3', b'\xff\xf2'] or header[:3] == b'ID3':
            return 'mp3'
        
        # WAV: RIFF....WAVE
        if header[:4] == b'RIFF' and header[8:12] == b'WAVE':
            return 'wav'
        
        # M4A/MP4: ftyp
        if header[4:8] == b'ftyp':
            return 'm4a'
        
        # OGG: OggS
        if header[:4] == b'OggS':
            return 'ogg'
        
        # FLAC: fLaC
        if header[:4] == b'fLaC':
            return 'flac'
        
        # WebM: starts with 0x1A 0x45 0xDF 0xA3
        if header[:4] == b'\x1a\x45\xdf\xa3':
            return 'webm'
        
        logger.warning(f"⚠️ Unknown audio format, defaulting to mp3. Header: {header[:4].hex()}")
        return 'mp3'
    
    def validate_audio(self, audio_data: bytes) -> bool:
        """
        Validate audio file
        
        Args:
            audio_data: Audio bytes
            
        Returns:
            True if valid
        """
        # Check file size
        if len(audio_data) > self.max_file_size:
            logger.error(f"❌ Audio file too large: {len(audio_data)} bytes (max: {self.max_file_size})")
            return False
        
        # Check minimum size (at least 1KB)
        if len(audio_data) < 1024:
            logger.error(f"❌ Audio file too small: {len(audio_data)} bytes")
            return False
        
        # Detect format
        format_ext = self._detect_audio_format(audio_data)
        if format_ext not in self.supported_formats:
            logger.error(f"❌ Unsupported audio format: {format_ext}")
            return False
        
        logger.info(f"✅ Audio validation passed: {format_ext}, {len(audio_data)} bytes")
        return True
    
    def get_audio_info(self, audio_data: bytes) -> dict:
        """
        Get information about audio file
        
        Args:
            audio_data: Audio bytes
            
        Returns:
            Dictionary with audio info
        """
        format_ext = self._detect_audio_format(audio_data)
        
        return {
            "format": format_ext,
            "size_bytes": len(audio_data),
            "size_mb": round(len(audio_data) / 1024 / 1024, 2),
            "is_valid": self.validate_audio(audio_data)
        }


# Singleton instance
audio_service = AudioService()