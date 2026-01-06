"""
Session Management Service for NewsFlash Application

This module provides session-based language preference management including:
- Language preference storage and retrieval
- Session persistence across requests
- Helper functions for session management
"""

from flask import session
from typing import Optional
import logging
from language_service import LanguageService

logger = logging.getLogger(__name__)


class SessionManager:
    """Service class for managing session-based language preferences."""
    
    # Session keys
    LANGUAGE_PREFERENCE_KEY = 'preferred_language'
    SESSION_ID_KEY = 'session_id'
    SENTIMENT_DISPLAY_KEY = 'sentiment_display'
    
    @classmethod
    def get_language_preference(cls) -> str:
        """
        Get the user's language preference from session.
        
        Returns:
            Language code from session or default language if not set
        """
        try:
            language = session.get(cls.LANGUAGE_PREFERENCE_KEY)
            
            if language and LanguageService.validate_language(language):
                logger.debug(f"Retrieved language preference from session: {language}")
                return language.lower()
            
            # Return default language if no valid preference found
            default_lang = LanguageService.get_default_language()
            logger.debug(f"No valid language preference found, using default: {default_lang}")
            return default_lang
            
        except Exception as e:
            logger.error(f"Error retrieving language preference from session: {e}")
            return LanguageService.get_default_language()
    
    @classmethod
    def set_language_preference(cls, language_code: str) -> bool:
        """
        Set the user's language preference in session.
        
        Args:
            language_code: The language code to set as preference
            
        Returns:
            True if successfully set, False if invalid language
        """
        try:
            # Validate and normalize the language code
            normalized_language = LanguageService.normalize_language_code(language_code)
            
            if not normalized_language:
                logger.warning(f"Attempted to set invalid language preference: {language_code}")
                return False
            
            # Store in session
            session[cls.LANGUAGE_PREFERENCE_KEY] = normalized_language
            session.permanent = True  # Make session persistent
            
            logger.info(f"Language preference set to: {normalized_language}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting language preference: {e}")
            return False
    
    @classmethod
    def clear_language_preference(cls) -> None:
        """
        Clear the user's language preference from session.
        """
        try:
            if cls.LANGUAGE_PREFERENCE_KEY in session:
                del session[cls.LANGUAGE_PREFERENCE_KEY]
                logger.info("Language preference cleared from session")
        except Exception as e:
            logger.error(f"Error clearing language preference: {e}")
    
    @classmethod
    def has_language_preference(cls) -> bool:
        """
        Check if user has a language preference set in session.
        
        Returns:
            True if language preference exists and is valid, False otherwise
        """
        try:
            language = session.get(cls.LANGUAGE_PREFERENCE_KEY)
            return language is not None and LanguageService.validate_language(language)
        except Exception as e:
            logger.error(f"Error checking language preference: {e}")
            return False
    
    @classmethod
    def get_session_id(cls) -> Optional[str]:
        """
        Get the current session ID.
        
        Returns:
            Session ID if exists, None otherwise
        """
        try:
            return session.get(cls.SESSION_ID_KEY)
        except Exception as e:
            logger.error(f"Error retrieving session ID: {e}")
            return None
    
    @classmethod
    def set_session_id(cls, session_id: str) -> None:
        """
        Set the session ID.
        
        Args:
            session_id: The session ID to set
        """
        try:
            session[cls.SESSION_ID_KEY] = session_id
            session.permanent = True
            logger.debug(f"Session ID set: {session_id}")
        except Exception as e:
            logger.error(f"Error setting session ID: {e}")
    
    @classmethod
    def get_sentiment_display_preference(cls) -> bool:
        """
        Get the user's sentiment display preference from session.
        
        Returns:
            True if sentiment display is enabled, True by default
        """
        try:
            return session.get(cls.SENTIMENT_DISPLAY_KEY, True)
        except Exception as e:
            logger.error(f"Error retrieving sentiment display preference: {e}")
            return True
    
    @classmethod
    def set_sentiment_display_preference(cls, enabled: bool) -> None:
        """
        Set the user's sentiment display preference in session.
        
        Args:
            enabled: Whether to display sentiment indicators
        """
        try:
            session[cls.SENTIMENT_DISPLAY_KEY] = enabled
            session.permanent = True
            logger.info(f"Sentiment display preference set to: {enabled}")
        except Exception as e:
            logger.error(f"Error setting sentiment display preference: {e}")
    
    @classmethod
    def get_session_info(cls) -> dict:
        """
        Get comprehensive session information.
        
        Returns:
            Dictionary containing session information
        """
        try:
            return {
                'session_id': cls.get_session_id(),
                'language_preference': cls.get_language_preference(),
                'has_language_preference': cls.has_language_preference(),
                'sentiment_display': cls.get_sentiment_display_preference(),
                'supported_languages': LanguageService.get_supported_languages()
            }
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return {
                'session_id': None,
                'language_preference': LanguageService.get_default_language(),
                'has_language_preference': False,
                'sentiment_display': True,
                'supported_languages': LanguageService.get_supported_languages()
            }
    
    @classmethod
    def clear_session(cls) -> None:
        """
        Clear all session data.
        """
        try:
            session.clear()
            logger.info("Session cleared")
        except Exception as e:
            logger.error(f"Error clearing session: {e}")
    
    @classmethod
    def initialize_session_defaults(cls) -> None:
        """
        Initialize session with default values if not already set.
        """
        try:
            # Set default language if not set
            if not cls.has_language_preference():
                cls.set_language_preference(LanguageService.get_default_language())
            
            # Set default sentiment display if not set
            if cls.SENTIMENT_DISPLAY_KEY not in session:
                cls.set_sentiment_display_preference(True)
                
            logger.debug("Session defaults initialized")
            
        except Exception as e:
            logger.error(f"Error initializing session defaults: {e}")


# Convenience functions for common operations
def get_user_language() -> str:
    """Convenience function to get user's language preference."""
    return SessionManager.get_language_preference()


def set_user_language(language_code: str) -> bool:
    """Convenience function to set user's language preference."""
    return SessionManager.set_language_preference(language_code)


def get_session_info() -> dict:
    """Convenience function to get session information."""
    return SessionManager.get_session_info()


def initialize_session() -> None:
    """Convenience function to initialize session defaults."""
    return SessionManager.initialize_session_defaults()