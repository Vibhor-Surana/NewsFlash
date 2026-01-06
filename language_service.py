"""
Language Management Service for NewsFlash Application

This module provides language management functionality including:
- Supported language definitions
- Language code validation
- Language mapping and utilities
"""

from typing import Dict, List, Optional


class LanguageService:
    """Service class for managing multi-language support in the NewsFlash application."""
    
    # Supported languages with their metadata
    SUPPORTED_LANGUAGES = {
        'en': {
            'name': 'English',
            'native': 'English',
            'tts_code': 'en',
            'enabled': True
        },
        'hi': {
            'name': 'Hindi', 
            'native': 'हिंदी',
            'tts_code': 'hi',
            'enabled': True
        },
        'mr': {
            'name': 'Marathi',
            'native': 'मराठी', 
            'tts_code': 'mr',
            'enabled': True
        }
    }
    
    DEFAULT_LANGUAGE = 'en'
    
    @classmethod
    def get_supported_languages(cls) -> Dict[str, Dict[str, str]]:
        """
        Get all supported languages with their metadata.
        
        Returns:
            Dict containing language codes as keys and language metadata as values
        """
        return {
            code: lang_data for code, lang_data in cls.SUPPORTED_LANGUAGES.items()
            if lang_data.get('enabled', True)
        }
    
    @classmethod
    def validate_language(cls, language_code: str) -> bool:
        """
        Validate if a language code is supported.
        
        Args:
            language_code: The language code to validate (e.g., 'en', 'hi', 'mr')
            
        Returns:
            True if language is supported and enabled, False otherwise
        """
        if not language_code or not isinstance(language_code, str):
            return False
            
        language_code = language_code.lower().strip()
        lang_data = cls.SUPPORTED_LANGUAGES.get(language_code)
        
        return lang_data is not None and lang_data.get('enabled', True)
    
    @classmethod
    def get_default_language(cls) -> str:
        """
        Get the default language code.
        
        Returns:
            Default language code
        """
        return cls.DEFAULT_LANGUAGE
    
    @classmethod
    def get_language_name(cls, language_code: str) -> Optional[str]:
        """
        Get the English name of a language.
        
        Args:
            language_code: The language code
            
        Returns:
            English name of the language or None if not found
        """
        if not cls.validate_language(language_code):
            return None
            
        return cls.SUPPORTED_LANGUAGES[language_code.lower()]['name']
    
    @classmethod
    def get_native_name(cls, language_code: str) -> Optional[str]:
        """
        Get the native name of a language.
        
        Args:
            language_code: The language code
            
        Returns:
            Native name of the language or None if not found
        """
        if not cls.validate_language(language_code):
            return None
            
        return cls.SUPPORTED_LANGUAGES[language_code.lower()]['native']
    
    @classmethod
    def get_tts_code(cls, language_code: str) -> Optional[str]:
        """
        Get the TTS service code for a language.
        
        Args:
            language_code: The language code
            
        Returns:
            TTS service code or None if not found
        """
        if not cls.validate_language(language_code):
            return None
            
        return cls.SUPPORTED_LANGUAGES[language_code.lower()]['tts_code']
    
    @classmethod
    def get_language_codes(cls) -> List[str]:
        """
        Get list of all supported language codes.
        
        Returns:
            List of supported language codes
        """
        return [
            code for code, lang_data in cls.SUPPORTED_LANGUAGES.items()
            if lang_data.get('enabled', True)
        ]
    
    @classmethod
    def normalize_language_code(cls, language_code: str) -> Optional[str]:
        """
        Normalize and validate a language code.
        
        Args:
            language_code: The language code to normalize
            
        Returns:
            Normalized language code or None if invalid
        """
        if not language_code or not isinstance(language_code, str):
            return None
            
        normalized = language_code.lower().strip()
        
        if cls.validate_language(normalized):
            return normalized
            
        return None
    
    @classmethod
    def get_fallback_language(cls, language_code: str) -> str:
        """
        Get fallback language if the requested language is not supported.
        
        Args:
            language_code: The requested language code
            
        Returns:
            Valid language code (either the requested one or default fallback)
        """
        if cls.validate_language(language_code):
            return language_code.lower()
            
        return cls.DEFAULT_LANGUAGE


# Convenience functions for common operations
def validate_language(language_code: str) -> bool:
    """Convenience function to validate language code."""
    return LanguageService.validate_language(language_code)


def get_supported_languages() -> Dict[str, Dict[str, str]]:
    """Convenience function to get supported languages."""
    return LanguageService.get_supported_languages()


def get_default_language() -> str:
    """Convenience function to get default language."""
    return LanguageService.get_default_language()


def normalize_language_code(language_code: str) -> Optional[str]:
    """Convenience function to normalize language code."""
    return LanguageService.normalize_language_code(language_code)