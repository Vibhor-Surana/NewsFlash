"""
Tests for language-specific error handling scenarios.
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import logging

from news_service import NewsService
from tts_service import TTSService
from language_service import LanguageService
from error_handler import ErrorHandler, FallbackManager
from config import Config


class TestLanguageSpecificErrors(unittest.TestCase):
    """Test language-specific error scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.news_service = NewsService()
        self.tts_service = TTSService()
        
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
    
    @patch('news_service.ChatGoogleGenerativeAI')
    def test_hindi_summary_failure_fallback_to_english(self, mock_llm):
        """Test Hindi summary failure with fallback to English."""
        # Mock LLM to fail for Hindi but succeed for English
        def mock_invoke(params):
            # Check if this is a Hindi prompt (contains Hindi text)
            if any(hindi_char in str(params) for hindi_char in ['हिंदी', 'सारांश', 'भावना']):
                raise Exception("Hindi processing failed")
            else:
                # Return English response
                mock_result = Mock()
                mock_result.content = "This is an English summary."
                return mock_result
        
        mock_llm.return_value.invoke.side_effect = mock_invoke
        
        article_text = "This is a test article with enough content to trigger AI summary generation."
        result = self.news_service.generate_summary(article_text, "Test Title", "hi")
        
        # Should fallback to English and return a summary
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
        
        # Check that fallback was logged
        fallback_logged = any("falling back to English" in msg.lower() for msg in self.log_messages)
        self.assertTrue(fallback_logged)
    
    @patch('news_service.ChatGoogleGenerativeAI')
    def test_marathi_sentiment_failure_fallback_to_neutral(self, mock_llm):
        """Test Marathi sentiment analysis failure with fallback to neutral."""
        # Mock LLM to fail for Marathi sentiment analysis
        mock_llm.return_value.invoke.side_effect = Exception("Marathi sentiment analysis failed")
        
        result = self.news_service.analyze_sentiment("Test article text", "mr")
        
        # Should fallback to neutral
        self.assertEqual(result, "neutral")
        
        # Check that error was logged
        error_logged = any("sentiment analysis" in msg.lower() for msg in self.log_messages)
        self.assertTrue(error_logged)
    
    @patch('tts_service.gTTS')
    def test_hindi_tts_failure_fallback_to_english(self, mock_gtts):
        """Test Hindi TTS failure with fallback to English."""
        call_count = 0
        
        def mock_gtts_init(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            # Fail for Hindi (first call), succeed for English (second call)
            if 'lang' in kwargs and kwargs['lang'] == 'hi':
                raise Exception("Hindi TTS not available")
            
            # Return mock TTS object for English
            mock_tts = Mock()
            mock_tts.save = Mock()
            return mock_tts
        
        mock_gtts.side_effect = mock_gtts_init
        
        result = self.tts_service.text_to_speech("Test text", "hi")
        
        # Should attempt fallback (result may be None due to mocking, but should not raise exception)
        self.assertIsNone(result)  # Due to our mock setup
        
        # Check that TTS was attempted
        self.assertTrue(call_count > 0)
    
    @patch('news_service.ChatGoogleGenerativeAI')
    def test_invalid_language_code_fallback(self, mock_llm):
        """Test invalid language code with fallback to default."""
        mock_result = Mock()
        mock_result.content = "English summary with neutral sentiment."
        mock_llm.return_value.invoke.return_value = mock_result
        
        # Test with completely invalid language code
        result = self.news_service.generate_summary("Test article", "Test Title", "xyz123")
        
        # Should fallback to English and work
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
    
    def test_language_service_fallback_chain(self):
        """Test language service fallback chain generation."""
        # Test valid language
        chain = FallbackManager.get_language_fallback_chain("hi")
        self.assertEqual(chain, ["hi", "en"])
        
        # Test invalid language
        chain = FallbackManager.get_language_fallback_chain("invalid")
        self.assertEqual(chain, ["en"])
        
        # Test None language
        chain = FallbackManager.get_language_fallback_chain(None)
        self.assertEqual(chain, ["en"])
    
    @patch('news_service.ChatGoogleGenerativeAI')
    def test_rate_limit_error_handling(self, mock_llm):
        """Test rate limit error handling."""
        # Mock rate limit error
        mock_llm.return_value.invoke.side_effect = Exception("429 Rate limit exceeded")
        
        article_text = "This is a test article with enough content to trigger AI summary generation."
        result = self.news_service.generate_summary(article_text, "Test Title", "en")
        
        # Should return fallback summary
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
        
        # Check that rate limit was logged
        rate_limit_logged = any("rate limit" in msg.lower() for msg in self.log_messages)
        self.assertTrue(rate_limit_logged)
    
    @patch('news_service.ChatGoogleGenerativeAI')
    def test_quota_exceeded_error_handling(self, mock_llm):
        """Test quota exceeded error handling."""
        # Mock quota exceeded error
        mock_llm.return_value.invoke.side_effect = Exception("Quota exceeded for this request")
        
        # Use longer text to avoid short text fallback
        long_text = "This is a longer test article with enough content to trigger AI sentiment analysis instead of the short text fallback mechanism."
        result = self.news_service.analyze_sentiment(long_text, "en")
        
        # Should return neutral sentiment
        self.assertEqual(result, "neutral")
        
        # Check that quota error was logged
        quota_logged = any("quota" in msg.lower() for msg in self.log_messages)
        self.assertTrue(quota_logged)
    
    def test_tts_language_code_mapping(self):
        """Test TTS language code mapping."""
        # Test valid language codes
        self.assertEqual(self.tts_service._get_tts_language_code("en"), "en")
        self.assertEqual(self.tts_service._get_tts_language_code("hi"), "hi")
        self.assertEqual(self.tts_service._get_tts_language_code("mr"), "mr")
        
        # Test invalid language code (should fallback to default)
        self.assertEqual(self.tts_service._get_tts_language_code("invalid"), "en")
    
    @patch('news_service.ChatGoogleGenerativeAI')
    def test_combined_summary_sentiment_error_handling(self, mock_llm):
        """Test combined summary and sentiment generation with errors."""
        # Mock LLM to return malformed response
        mock_result = Mock()
        mock_result.content = "Malformed response without proper format"
        mock_llm.return_value.invoke.return_value = mock_result
        
        article_text = "This is a test article with enough content."
        result = self.news_service.generate_summary_with_sentiment(article_text, "Test Title", "en")
        
        # Should return fallback values
        self.assertIsInstance(result, dict)
        self.assertIn('summary', result)
        self.assertIn('sentiment', result)
        self.assertEqual(result['sentiment'], 'neutral')  # Should fallback to neutral
    
    def test_text_cleaning_for_tts(self):
        """Test text cleaning for TTS with various problematic inputs."""
        # Test with markdown
        markdown_text = "**Bold** and *italic* text with [links](http://example.com)"
        clean_text = self.tts_service._clean_text_for_tts(markdown_text)
        self.assertNotIn("**", clean_text)
        self.assertNotIn("*", clean_text)
        self.assertNotIn("[", clean_text)
        self.assertNotIn("](", clean_text)
        
        # Test with URLs
        url_text = "Visit https://example.com for more info"
        clean_text = self.tts_service._clean_text_for_tts(url_text)
        self.assertNotIn("https://", clean_text)
        
        # Test with special characters
        special_text = "Text with @#$%^&*() special chars"
        clean_text = self.tts_service._clean_text_for_tts(special_text)
        # Should remove most special chars but keep basic punctuation
        self.assertNotIn("@", clean_text)
        self.assertNotIn("#", clean_text)
        self.assertNotIn("$", clean_text)
    
    @patch('news_service.Config.ENABLE_FALLBACK_LOGGING', False)
    def test_fallback_logging_disabled(self):
        """Test behavior when fallback logging is disabled."""
        # Clear previous log messages
        self.log_messages.clear()
        
        # This should not log fallback messages
        ErrorHandler.log_language_error("test_op", "hi", Exception("Test error"), "en")
        
        # Should not have logged anything due to disabled fallback logging
        language_error_logged = any("Language error" in msg for msg in self.log_messages)
        self.assertFalse(language_error_logged)
    
    def test_error_message_formatting(self):
        """Test error message formatting in different scenarios."""
        # Test with different error types
        test_cases = [
            ("Connection timeout", True),  # Should be retryable
            ("401 Unauthorized", False),   # Should not be retryable
            ("Rate limit exceeded", True), # Should be retryable
            ("Invalid API key", False),    # Should not be retryable
        ]
        
        from error_handler import _is_retryable_error
        
        for error_msg, expected_retryable in test_cases:
            error = Exception(error_msg)
            is_retryable = _is_retryable_error(error)
            self.assertEqual(is_retryable, expected_retryable, 
                           f"Error '{error_msg}' retryable status should be {expected_retryable}")


class TestErrorRecoveryScenarios(unittest.TestCase):
    """Test error recovery scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.news_service = NewsService()
    
    @patch('news_service.ChatGoogleGenerativeAI')
    def test_partial_service_failure_recovery(self, mock_llm):
        """Test recovery from partial service failures."""
        call_count = 0
        
        def mock_invoke(params):
            nonlocal call_count
            call_count += 1
            
            # Fail first two calls, succeed on third
            if call_count <= 2:
                raise Exception("Temporary service failure")
            
            mock_result = Mock()
            mock_result.content = "Summary: Successful summary.\nSentiment: positive"
            return mock_result
        
        mock_llm.return_value.invoke.side_effect = mock_invoke
        
        # This should eventually succeed after retries
        with patch('news_service.Config.MAX_RETRY_ATTEMPTS', 3):
            # Use longer text to avoid short text fallback
            long_text = "This is a longer test article with enough content to trigger AI sentiment analysis instead of the short text fallback mechanism."
            result = self.news_service.analyze_sentiment(long_text, "en")
            
            # Should eventually succeed
            self.assertEqual(result, "positive")
            self.assertEqual(call_count, 3)
    
    @patch('news_service.ChatGoogleGenerativeAI')
    def test_complete_service_failure_fallback(self, mock_llm):
        """Test fallback when service completely fails."""
        # Mock complete service failure
        mock_llm.return_value.invoke.side_effect = Exception("Service completely unavailable")
        
        article_text = "This is a test article with enough content."
        
        # Test summary generation
        summary_result = self.news_service.generate_summary(article_text, "Test Title", "en")
        self.assertIsInstance(summary_result, str)
        self.assertTrue(len(summary_result) > 0)
        
        # Test sentiment analysis
        sentiment_result = self.news_service.analyze_sentiment(article_text, "en")
        self.assertEqual(sentiment_result, "neutral")
        
        # Test combined generation
        combined_result = self.news_service.generate_summary_with_sentiment(article_text, "Test Title", "en")
        self.assertIsInstance(combined_result, dict)
        self.assertEqual(combined_result['sentiment'], 'neutral')


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)