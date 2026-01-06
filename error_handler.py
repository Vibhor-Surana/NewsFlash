"""
Comprehensive Error Handling Module for NewsFlash Application

This module provides centralized error handling, logging, and fallback mechanisms
for language-specific operations and sentiment analysis.
"""

import logging
import time
import functools
from typing import Any, Callable, Dict, Optional, Union
from config import Config
from language_service import LanguageService

logger = logging.getLogger(__name__)

class NewsFlashError(Exception):
    """Base exception class for NewsFlash application errors."""
    pass

class LanguageError(NewsFlashError):
    """Exception raised for language-related errors."""
    pass

class SentimentAnalysisError(NewsFlashError):
    """Exception raised for sentiment analysis errors."""
    pass

class AIServiceError(NewsFlashError):
    """Exception raised for AI service errors."""
    pass

class TTSError(NewsFlashError):
    """Exception raised for TTS service errors."""
    pass

class ErrorHandler:
    """Centralized error handling and logging for the NewsFlash application."""
    
    @staticmethod
    def log_language_error(operation: str, language: str, error: Exception, fallback_used: str = None):
        """Log language-specific errors with context."""
        if Config.ENABLE_FALLBACK_LOGGING:
            error_msg = f"Language error in {operation} for language '{language}': {str(error)}"
            if fallback_used:
                error_msg += f" | Fallback used: {fallback_used}"
            logger.error(error_msg, exc_info=True)
    
    @staticmethod
    def log_sentiment_error(operation: str, error: Exception, fallback_used: str = "neutral"):
        """Log sentiment analysis errors with context."""
        if Config.ENABLE_FALLBACK_LOGGING:
            error_msg = f"Sentiment analysis error in {operation}: {str(error)}"
            error_msg += f" | Fallback used: {fallback_used}"
            logger.error(error_msg, exc_info=True)
    
    @staticmethod
    def log_ai_service_error(operation: str, error: Exception, retry_count: int = 0):
        """Log AI service errors with retry context."""
        error_str = str(error).lower()
        if "429" in str(error) or "quota" in error_str or "rate limit" in error_str:
            error_type = "Rate limit"
        else:
            error_type = "AI service"
        
        error_msg = f"{error_type} error in {operation}: {str(error)}"
        if retry_count > 0:
            error_msg += f" | Retry attempt: {retry_count}"
        logger.error(error_msg, exc_info=True)
    
    @staticmethod
    def log_tts_error(operation: str, language: str, error: Exception, fallback_used: str = None):
        """Log TTS service errors with context."""
        if Config.ENABLE_FALLBACK_LOGGING:
            error_msg = f"TTS error in {operation} for language '{language}': {str(error)}"
            if fallback_used:
                error_msg += f" | Fallback used: {fallback_used}"
            logger.error(error_msg, exc_info=True)

def with_language_fallback(fallback_language: str = None):
    """
    Decorator to provide language fallback functionality.
    
    Args:
        fallback_language: Language to fallback to (defaults to system default)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract language parameter
            language = kwargs.get('language') or (args[2] if len(args) > 2 else None)
            if not language:
                language = LanguageService.get_default_language()
            
            # Validate and get fallback language
            target_language = LanguageService.get_fallback_language(language)
            original_language = language
            
            # Update language parameter
            if 'language' in kwargs:
                kwargs['language'] = target_language
            elif len(args) > 2:
                args = list(args)
                args[2] = target_language
                args = tuple(args)
            
            try:
                # Log language fallback if it occurred
                if target_language != original_language and Config.ENABLE_FALLBACK_LOGGING:
                    logger.info(f"Language fallback: {original_language} -> {target_language} in {func.__name__}")
                
                return func(*args, **kwargs)
                
            except Exception as e:
                # If target language fails and it's not the default, try default language
                if target_language != LanguageService.get_default_language() and Config.LANGUAGE_FALLBACK_ENABLED:
                    ErrorHandler.log_language_error(
                        func.__name__, target_language, e, LanguageService.get_default_language()
                    )
                    
                    # Update to default language
                    if 'language' in kwargs:
                        kwargs['language'] = LanguageService.get_default_language()
                    elif len(args) > 2:
                        args = list(args)
                        args[2] = LanguageService.get_default_language()
                        args = tuple(args)
                    
                    try:
                        return func(*args, **kwargs)
                    except Exception as fallback_error:
                        ErrorHandler.log_language_error(
                            func.__name__, LanguageService.get_default_language(), fallback_error
                        )
                        raise LanguageError(f"All language fallbacks failed in {func.__name__}: {fallback_error}")
                else:
                    ErrorHandler.log_language_error(func.__name__, target_language, e)
                    raise LanguageError(f"Language operation failed in {func.__name__}: {e}")
        
        return wrapper
    return decorator

def with_sentiment_fallback(fallback_sentiment: str = "neutral"):
    """
    Decorator to provide sentiment analysis fallback functionality.
    
    Args:
        fallback_sentiment: Sentiment to fallback to on errors
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if Config.SENTIMENT_FALLBACK_ENABLED:
                    ErrorHandler.log_sentiment_error(func.__name__, e, fallback_sentiment)
                    return fallback_sentiment
                else:
                    ErrorHandler.log_sentiment_error(func.__name__, e)
                    raise SentimentAnalysisError(f"Sentiment analysis failed in {func.__name__}: {e}")
        
        return wrapper
    return decorator

def with_retry(max_attempts: int = None, base_delay: float = None, exponential_backoff: bool = True):
    """
    Decorator to provide retry functionality with exponential backoff.
    
    Args:
        max_attempts: Maximum retry attempts (defaults to config)
        base_delay: Base delay between retries (defaults to config)
        exponential_backoff: Whether to use exponential backoff
    """
    max_attempts = max_attempts or Config.MAX_RETRY_ATTEMPTS
    base_delay = base_delay or Config.RETRY_DELAY
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if this is a retryable error
                    if not _is_retryable_error(e):
                        raise e
                    
                    if attempt < max_attempts - 1:  # Don't sleep on last attempt
                        delay = base_delay * (2 ** attempt) if exponential_backoff else base_delay
                        ErrorHandler.log_ai_service_error(func.__name__, e, attempt + 1)
                        logger.info(f"Retrying {func.__name__} in {delay} seconds (attempt {attempt + 1}/{max_attempts})")
                        time.sleep(delay)
                    else:
                        ErrorHandler.log_ai_service_error(func.__name__, e, attempt + 1)
            
            raise AIServiceError(f"All retry attempts failed in {func.__name__}: {last_exception}")
        
        return wrapper
    return decorator

def _is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is retryable.
    
    Args:
        error: The exception to check
        
    Returns:
        True if the error should be retried, False otherwise
    """
    error_str = str(error).lower()
    
    # Retryable errors
    retryable_indicators = [
        "timeout", "connection", "network", "temporary", "503", "502", "500",
        "rate limit", "429", "quota exceeded", "service unavailable"
    ]
    
    # Non-retryable errors
    non_retryable_indicators = [
        "401", "403", "404", "invalid api key", "authentication", "authorization",
        "bad request", "400", "not found"
    ]
    
    # Check for non-retryable errors first
    for indicator in non_retryable_indicators:
        if indicator in error_str:
            return False
    
    # Check for retryable errors
    for indicator in retryable_indicators:
        if indicator in error_str:
            return True
    
    # Default to retryable for unknown errors
    return True

class FallbackManager:
    """Manages fallback strategies for different operations."""
    
    @staticmethod
    def get_language_fallback_chain(requested_language: str) -> list:
        """
        Get the fallback chain for a requested language.
        
        Args:
            requested_language: The originally requested language
            
        Returns:
            List of languages to try in order
        """
        chain = []
        
        # Add the requested language if valid
        if LanguageService.validate_language(requested_language):
            chain.append(requested_language.lower())
        
        # Add default language if not already in chain
        default_lang = LanguageService.get_default_language()
        if default_lang not in chain:
            chain.append(default_lang)
        
        return chain
    
    @staticmethod
    def get_sentiment_fallback() -> str:
        """Get the fallback sentiment value."""
        return "neutral"
    
    @staticmethod
    def create_fallback_summary(article_text: str, max_length: int = 200) -> str:
        """
        Create a fallback summary without AI.
        
        Args:
            article_text: The article text to summarize
            max_length: Maximum length of the summary
            
        Returns:
            Fallback summary text
        """
        if not article_text or len(article_text.strip()) == 0:
            return "No content available for summary."
        
        article_text = article_text.strip()
        
        if len(article_text) <= max_length:
            return article_text
        
        # Try to find sentence boundaries
        sentences = article_text.split('. ')
        if len(sentences) >= 2:
            # Take first two sentences
            summary = '. '.join(sentences[:2]) + '.'
            if len(summary) <= max_length:
                return summary
        
        # Fallback to character truncation
        return article_text[:max_length].strip() + "..."

# Convenience functions for common error handling patterns
def handle_language_operation(operation_name: str, language: str, operation_func: Callable, *args, **kwargs) -> Any:
    """
    Handle a language-specific operation with comprehensive error handling.
    
    Args:
        operation_name: Name of the operation for logging
        language: Target language
        operation_func: Function to execute
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        Result of the operation or fallback value
    """
    fallback_chain = FallbackManager.get_language_fallback_chain(language)
    
    for lang in fallback_chain:
        try:
            return operation_func(*args, language=lang, **kwargs)
        except Exception as e:
            ErrorHandler.log_language_error(operation_name, lang, e)
            if lang == fallback_chain[-1]:  # Last language in chain
                raise LanguageError(f"All language fallbacks failed for {operation_name}: {e}")
    
    raise LanguageError(f"No valid languages in fallback chain for {operation_name}")

def handle_sentiment_operation(operation_name: str, operation_func: Callable, *args, **kwargs) -> str:
    """
    Handle a sentiment analysis operation with error handling.
    
    Args:
        operation_name: Name of the operation for logging
        operation_func: Function to execute
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        Sentiment result or fallback value
    """
    try:
        return operation_func(*args, **kwargs)
    except Exception as e:
        if Config.SENTIMENT_FALLBACK_ENABLED:
            fallback = FallbackManager.get_sentiment_fallback()
            ErrorHandler.log_sentiment_error(operation_name, e, fallback)
            return fallback
        else:
            ErrorHandler.log_sentiment_error(operation_name, e)
            raise SentimentAnalysisError(f"Sentiment analysis failed for {operation_name}: {e}")