"""
Comprehensive tests for error handling and fallback mechanisms.
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import logging
import tempfile
import os

from error_handler import (
    ErrorHandler, FallbackManager, with_language_fallback, with_sentiment_fallback,
    with_retry, handle_language_operation, handle_sentiment_operation,
    LanguageError, SentimentAnalysisError, AIServiceError, TTSError,
    _is_retryable_error
)
from news_service import NewsService
from tts_service import TTSService
from language_service import LanguageService
from config import Config


class TestErrorHandler(unittest.TestCase):
    """Test the ErrorHandler class functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
        # Capture log messages
        self.log_messages = []
        self.handler = logging.Handler()
        self.handler.emit = lambda record: self.log_messages.append(record.getMessage())
        logging.getLogger().addHandler(self.handler)
        logging.getLogger().setLevel(logging.DEBUG)
    
    def tearDown(self):
        """Clean up after tests."""
        logging.getLogger().removeHandler(self.handler)
        self.log_messages.clear()
    
    def test_log_language_error(self):
        """Test language error logging."""
        test_error = Exception("Test language error")
        ErrorHandler.log_language_error("test_operation", "hi", test_error, "en")
        
        # Check if error was logged
        error_logged = any("Language error in test_operation for language 'hi'" in msg for msg in self.log_messages)
        self.assertTrue(error_logged)
        
        fallback_logged = any("Fallback used: en" in msg for msg in self.log_messages)
        self.assertTrue(fallback_logged)
    
    def test_log_sentiment_error(self):
        """Test sentiment error logging."""
        test_error = Exception("Test sentiment error")
        ErrorHandler.log_sentiment_error("test_operation", test_error, "neutral")
        
        # Check if error was logged
        error_logged = any("Sentiment analysis error in test_operation" in msg for msg in self.log_messages)
        self.assertTrue(error_logged)
        
        fallback_logged = any("Fallback used: neutral" in msg for msg in self.log_messages)
        self.assertTrue(fallback_logged)
    
    def test_log_ai_service_error(self):
        """Test AI service error logging."""
        test_error = Exception("Rate limit exceeded")
        ErrorHandler.log_ai_service_error("test_operation", test_error, 2)
        
        # Check if error was logged
        error_logged = any("Rate limit error in test_operation" in msg for msg in self.log_messages)
        self.assertTrue(error_logged)
        
        retry_logged = any("Retry attempt: 2" in msg for msg in self.log_messages)
        self.assertTrue(retry_logged)
    
    def test_log_tts_error(self):
        """Test TTS error logging."""
        test_error = Exception("TTS service unavailable")
        ErrorHandler.log_tts_error("test_operation", "hi", test_error, "en")
        
        # Check if error was logged
        error_logged = any("TTS error in test_operation for language 'hi'" in msg for msg in self.log_messages)
        self.assertTrue(error_logged)


class TestFallbackManager(unittest.TestCase):
    """Test the FallbackManager class functionality."""
    
    def test_get_language_fallback_chain(self):
        """Test language fallback chain generation."""
        # Test with valid language
        chain = FallbackManager.get_language_fallback_chain("hi")
        self.assertEqual(chain, ["hi", "en"])
        
        # Test with invalid language
        chain = FallbackManager.get_language_fallback_chain("invalid")
        self.assertEqual(chain, ["en"])
        
        # Test with English (should not duplicate)
        chain = FallbackManager.get_language_fallback_chain("en")
        self.assertEqual(chain, ["en"])
    
    def test_get_sentiment_fallback(self):
        """Test sentiment fallback value."""
        fallback = FallbackManager.get_sentiment_fallback()
        self.assertEqual(fallback, "neutral")
    
    def test_create_fallback_summary(self):
        """Test fallback summary creation."""
        # Test short text
        short_text = "Short article."
        summary = FallbackManager.create_fallback_summary(short_text)
        self.assertEqual(summary, short_text)
        
        # Test long text with sentences that can fit within max_length
        long_text = "First sentence. Second sentence. Third sentence should not be included. Fourth sentence definitely not included."
        summary = FallbackManager.create_fallback_summary(long_text, max_length=100)
        expected = "First sentence. Second sentence."
        self.assertEqual(summary, expected)
        
        # Test very long text without clear sentences
        very_long_text = "A" * 300
        summary = FallbackManager.create_fallback_summary(very_long_text)
        self.assertTrue(summary.endswith("..."))
        self.assertTrue(len(summary) <= 203)  # 200 + "..."
        
        # Test empty text
        empty_summary = FallbackManager.create_fallback_summary("")
        self.assertEqual(empty_summary, "No content available for summary.")
        
        # Test text that fits within max_length
        medium_text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        summary = FallbackManager.create_fallback_summary(medium_text)
        self.assertEqual(summary, medium_text)  # Should return as-is since it's under 200 chars


class TestRetryableErrors(unittest.TestCase):
    """Test retryable error detection."""
    
    def test_retryable_errors(self):
        """Test identification of retryable errors."""
        # Retryable errors
        retryable_errors = [
            Exception("Connection timeout"),
            Exception("Network error occurred"),
            Exception("503 Service Unavailable"),
            Exception("Rate limit exceeded"),
            Exception("429 Too Many Requests"),
            Exception("Quota exceeded"),
        ]
        
        for error in retryable_errors:
            self.assertTrue(_is_retryable_error(error), f"Should be retryable: {error}")
    
    def test_non_retryable_errors(self):
        """Test identification of non-retryable errors."""
        # Non-retryable errors
        non_retryable_errors = [
            Exception("401 Unauthorized"),
            Exception("403 Forbidden"),
            Exception("404 Not Found"),
            Exception("Invalid API key"),
            Exception("Authentication failed"),
            Exception("400 Bad Request"),
        ]
        
        for error in non_retryable_errors:
            self.assertFalse(_is_retryable_error(error), f"Should not be retryable: {error}")


class TestDecorators(unittest.TestCase):
    """Test error handling decorators."""
    
    def test_with_sentiment_fallback_decorator(self):
        """Test sentiment fallback decorator."""
        @with_sentiment_fallback("neutral")
        def failing_sentiment_function():
            raise Exception("Sentiment analysis failed")
        
        result = failing_sentiment_function()
        self.assertEqual(result, "neutral")
    
    def test_with_retry_decorator(self):
        """Test retry decorator."""
        call_count = 0
        
        @with_retry(max_attempts=3, base_delay=0.1)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = failing_function()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)
    
    def test_with_retry_non_retryable_error(self):
        """Test retry decorator with non-retryable error."""
        call_count = 0
        
        @with_retry(max_attempts=3, base_delay=0.1)
        def failing_function():
            nonlocal call_count
            call_count += 1
            raise Exception("401 Unauthorized")
        
        with self.assertRaises(Exception):
            failing_function()
        
        # Should not retry non-retryable errors
        self.assertEqual(call_count, 1)


class TestNewsServiceErrorHandling(unittest.TestCase):
    """Test error handling in NewsService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.news_service = NewsService()
    
    @patch('news_service.ChatGoogleGenerativeAI')
    def test_analyze_sentiment_with_error(self, mock_llm):
        """Test sentiment analysis with error handling."""
        # Mock LLM to raise an exception
        mock_llm.return_value.invoke.side_effect = Exception("AI service error")
        
        # Should fallback to neutral
        result = self.news_service.analyze_sentiment("Test article text", "en")
        self.assertEqual(result, "neutral")
    
    def test_analyze_sentiment_short_text(self):
        """Test sentiment analysis with very short text."""
        result = self.news_service.analyze_sentiment("Hi", "en")
        self.assertEqual(result, "neutral")
    
    @patch('news_service.ChatGoogleGenerativeAI')
    def test_generate_summary_with_error(self, mock_llm):
        """Test summary generation with error handling."""
        # Mock LLM to raise an exception
        mock_llm.return_value.invoke.side_effect = Exception("AI service error")
        
        article_text = "This is a test article with enough content to trigger AI summary generation."
        result = self.news_service.generate_summary(article_text, "Test Title", "en")
        
        # Should return fallback summary
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
    
    def test_generate_summary_short_article(self):
        """Test summary generation with short article."""
        short_article = "Short article."
        result = self.news_service.generate_summary(short_article, "Test Title", "en")
        
        # Should return fallback summary without calling AI
        self.assertEqual(result, short_article)


class TestTTSServiceErrorHandling(unittest.TestCase):
    """Test error handling in TTSService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tts_service = TTSService()
    
    def test_text_to_speech_empty_text(self):
        """Test TTS with empty text."""
        result = self.tts_service.text_to_speech("", "en")
        self.assertIsNone(result)
        
        result = self.tts_service.text_to_speech(None, "en")
        self.assertIsNone(result)
    
    @patch('tts_service.gTTS')
    def test_text_to_speech_with_error(self, mock_gtts):
        """Test TTS with error handling."""
        # Mock gTTS to raise an exception
        mock_gtts.side_effect = Exception("TTS service error")
        
        result = self.tts_service.text_to_speech("Test text", "en")
        self.assertIsNone(result)
    
    def test_clean_text_for_tts(self):
        """Test text cleaning for TTS."""
        dirty_text = "**Bold text** with *italics* and https://example.com URL"
        clean_text = self.tts_service._clean_text_for_tts(dirty_text)
        
        # Should remove markdown and URLs
        self.assertNotIn("**", clean_text)
        self.assertNotIn("*", clean_text)
        self.assertNotIn("https://", clean_text)


class TestLanguageOperationHandling(unittest.TestCase):
    """Test language operation error handling."""
    
    def test_handle_language_operation_success(self):
        """Test successful language operation."""
        def mock_operation(text, language):
            return f"Result for {language}"
        
        result = handle_language_operation("test_op", "hi", mock_operation, "test text")
        self.assertEqual(result, "Result for hi")
    
    def test_handle_language_operation_with_fallback(self):
        """Test language operation with fallback."""
        def mock_operation(text, language):
            if language == "invalid":
                raise Exception("Language not supported")
            return f"Result for {language}"
        
        result = handle_language_operation("test_op", "invalid", mock_operation, "test text")
        self.assertEqual(result, "Result for en")  # Should fallback to English
    
    def test_handle_sentiment_operation_success(self):
        """Test successful sentiment operation."""
        def mock_operation(text):
            return "positive"
        
        result = handle_sentiment_operation("test_op", mock_operation, "test text")
        self.assertEqual(result, "positive")
    
    def test_handle_sentiment_operation_with_fallback(self):
        """Test sentiment operation with fallback."""
        def mock_operation(text):
            raise Exception("Sentiment analysis failed")
        
        result = handle_sentiment_operation("test_op", mock_operation, "test text")
        self.assertEqual(result, "neutral")  # Should fallback to neutral


class TestIntegrationErrorHandling(unittest.TestCase):
    """Test integration-level error handling scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.news_service = NewsService()
        self.tts_service = TTSService()
    
    @patch('news_service.Config.USE_AI_SUMMARY', False)
    def test_ai_disabled_fallback(self):
        """Test behavior when AI is disabled."""
        article_text = "This is a test article with enough content."
        result = self.news_service.generate_summary(article_text, "Test Title", "en")
        
        # Should use fallback summary
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
    
    def test_unsupported_language_fallback(self):
        """Test fallback for unsupported language."""
        # Test with completely invalid language
        result = self.news_service.analyze_sentiment("Test text", "xyz")
        self.assertEqual(result, "neutral")
    
    @patch('tts_service.os.makedirs')
    @patch('tts_service.gTTS')
    def test_tts_directory_creation_error(self, mock_gtts, mock_makedirs):
        """Test TTS with directory creation error."""
        mock_makedirs.side_effect = Exception("Permission denied")
        
        result = self.tts_service.text_to_speech("Test text", "en")
        self.assertIsNone(result)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)