import logging
import os
import tempfile
from typing import Optional, Dict
from gtts import gTTS
from config import Config
from language_service import LanguageService
from error_handler import (
    ErrorHandler, FallbackManager, with_language_fallback, with_retry,
    handle_language_operation, TTSError, LanguageError
)
import uuid

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self, language: str = None, slow: bool = None):
        """
        Initialize TTS service with language support.
        
        Args:
            language: Language code for TTS (defaults to config or 'en')
            slow: Whether to use slow speech (defaults to config)
        """
        self.default_language = language or Config.TTS_LANGUAGE or LanguageService.get_default_language()
        self.slow = slow if slow is not None else Config.TTS_SLOW
        
        # Validate and normalize the default language
        self.default_language = LanguageService.get_fallback_language(self.default_language)
        
        logger.info(f"TTSService initialized with default language: {self.default_language}")

    def text_to_speech(self, text: str, language: str = None) -> Optional[str]:
        """
        Convert text to speech and return the audio file path with comprehensive error handling.
        
        Args:
            text: Text to convert to speech
            language: Language code for TTS (optional, uses default if not provided)
            
        Returns:
            URL path to the generated audio file or None if failed
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for TTS")
                return None
            
            # Determine language to use
            target_language = self._get_target_language(language)
            
            # Clean text for TTS
            clean_text = self._clean_text_for_tts(text)
            
            if len(clean_text) > 5000:  # Limit text length
                clean_text = clean_text[:5000] + "... Text truncated for audio generation."
            
            logger.info(f"Generating TTS for text of length: {len(clean_text)} in language: {target_language}")
            
            # Generate unique filename with language code
            audio_filename = f"tts_{target_language}_{uuid.uuid4().hex[:8]}.mp3"
            audio_path = os.path.join("static", "audio", audio_filename)
            
            # Ensure audio directory exists
            os.makedirs(os.path.dirname(audio_path), exist_ok=True)
            
            # Use comprehensive error handling for TTS generation
            success = handle_language_operation(
                "text_to_speech",
                target_language,
                self._generate_tts_for_language,
                clean_text, audio_path
            )
            
            if success:
                logger.info(f"TTS audio saved to: {audio_path}")
                return f"/static/audio/{audio_filename}"
            else:
                return None
            
        except Exception as e:
            ErrorHandler.log_tts_error("text_to_speech", language or self.default_language, e)
            return None

    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text to make it more suitable for TTS"""
        try:
            # Remove markdown formatting
            text = text.replace('**', '').replace('*', '').replace('_', '')
            
            # Remove URLs
            import re
            text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
            
            # Remove multiple spaces and newlines
            text = re.sub(r'\s+', ' ', text)
            
            # Remove special characters that might cause issues
            text = re.sub(r'[^\w\s\.,!?;:()-]', ' ', text)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error cleaning text for TTS: {e}")
            return text

    def set_language(self, language: str) -> None:
        """
        Set the default language for TTS.
        
        Args:
            language: Language code to set as default
        """
        validated_language = LanguageService.get_fallback_language(language)
        self.default_language = validated_language
        logger.info(f"TTS default language set to: {validated_language}")
    
    def get_supported_languages(self) -> Dict[str, Dict[str, str]]:
        """
        Get all supported languages for TTS.
        
        Returns:
            Dictionary of supported languages with metadata
        """
        return LanguageService.get_supported_languages()
    
    def _get_target_language(self, language: str = None) -> str:
        """
        Determine the target language for TTS generation.
        
        Args:
            language: Requested language code
            
        Returns:
            Valid language code to use for TTS
        """
        if language:
            return LanguageService.get_fallback_language(language)
        return self.default_language
    
    def _get_tts_language_code(self, language: str) -> str:
        """
        Get the appropriate TTS language code for Google TTS.
        
        Args:
            language: Internal language code
            
        Returns:
            Google TTS compatible language code
        """
        tts_code = LanguageService.get_tts_code(language)
        return tts_code if tts_code else LanguageService.get_default_language()
    
    @with_retry(max_attempts=2)  # Fewer retries for TTS to avoid long delays
    def _generate_tts_for_language(self, text: str, audio_path: str, language: str) -> bool:
        """
        Generate TTS for a specific language with retry logic.
        
        Args:
            text: Text to convert
            audio_path: Path to save audio file
            language: Target language
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get TTS language code
            tts_lang_code = self._get_tts_language_code(language)
            
            # Generate TTS
            tts = gTTS(text=text, lang=tts_lang_code, slow=self.slow)
            tts.save(audio_path)
            
            # Verify file was created successfully
            if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
                raise TTSError(f"TTS file not created or empty: {audio_path}")
            
            logger.info(f"Successfully generated TTS for language {language}")
            return True
            
        except Exception as e:
            ErrorHandler.log_tts_error("_generate_tts_for_language", language, e)
            raise TTSError(f"TTS generation failed for language {language}: {e}")
    
    def _generate_tts_with_fallback(self, text: str, language: str, audio_path: str) -> bool:
        """
        Generate TTS with fallback mechanism - deprecated, use _generate_tts_for_language instead.
        
        Args:
            text: Text to convert
            language: Target language
            audio_path: Path to save audio file
            
        Returns:
            True if successful, False otherwise
        """
        logger.warning("Using deprecated _generate_tts_with_fallback, consider using _generate_tts_for_language")
        try:
            return self._generate_tts_for_language(text, audio_path, language)
        except Exception as e:
            ErrorHandler.log_tts_error("_generate_tts_with_fallback", language, e)
            return False

    def get_audio_url(self, text: str, language: str = None, cache_key: Optional[str] = None) -> Optional[str]:
        """
        Get audio URL for text, with optional caching and comprehensive error handling.
        
        Args:
            text: Text to convert to speech
            language: Language code for TTS
            cache_key: Optional cache key for future caching implementation
            
        Returns:
            URL path to audio file or None if failed
        """
        try:
            # For now, generate fresh audio each time
            # In production, you might want to implement caching
            return self.text_to_speech(text, language)
            
        except Exception as e:
            ErrorHandler.log_tts_error("get_audio_url", language or self.default_language, e)
            return None

    def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up old TTS files to save disk space"""
        try:
            audio_dir = os.path.join("static", "audio")
            if not os.path.exists(audio_dir):
                return
            
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(audio_dir):
                if filename.startswith("tts_") and filename.endswith(".mp3"):
                    file_path = os.path.join(audio_dir, filename)
                    if os.path.isfile(file_path):
                        file_age = current_time - os.path.getmtime(file_path)
                        if file_age > max_age_seconds:
                            os.remove(file_path)
                            logger.debug(f"Cleaned up old TTS file: {filename}")
                            
        except Exception as e:
            logger.error(f"Error cleaning up TTS files: {e}")
