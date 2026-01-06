"""
Integration tests for comprehensive error handling system.
"""

import unittest
import logging
from news_service import NewsService
from tts_service import TTSService
from error_handler import FallbackManager, ErrorHandler
from language_service import LanguageService


class TestErrorHandlingIntegration(unittest.TestCase):
    """Integration tests for error handling across all services."""
    
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
    
    def test_sentiment_analysis_error_handling(self):
        """Test sentiment analysis with comprehensive error handling."""
        # Test with short text (should return neutral without AI call)
        result = self.news_service.analyze_sentiment("Hi", "en")
        self.assertEqual(result, "neutral")
        
        # Test with longer text
        long_text = "This is a longer article with enough content to trigger sentiment analysis."
        result = self.news_service.analyze_sentiment(long_text, "en")
        self.assertIn(result, ["positive", "negative", "neutral"])
    
    def test_summary_generation_error_handling(self):
        """Test summary generation with error handling."""
        # Test with short article (should use fallback)
        short_article = "Short news."
        result = self.news_service.generate_summary(short_article, "Test Title", "en")
        self.assertEqual(result, short_article)
        
        # Test with longer article
        long_article = "This is a longer news article with enough content to potentially trigger AI summary generation. It contains multiple sentences and should be processed correctly by the system."
        result = self.news_service.generate_summary(long_article, "Test Title", "en")
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
    
    def test_combined_summary_sentiment_error_handling(self):
        """Test combined summary and sentiment generation with error handling."""
        article_text = "This is a test article with enough content for analysis."
        result = self.news_service.generate_summary_with_sentiment(article_text, "Test Title", "en")
        
        # Should return a dictionary with required keys
        self.assertIsInstance(result, dict)
        self.assertIn('summary', result)
        self.assertIn('sentiment', result)
        self.assertIn('language', result)
        
        # Values should be valid
        self.assertIsInstance(result['summary'], str)
        self.assertIn(result['sentiment'], ["positive", "negative", "neutral"])
        self.assertEqual(result['language'], "en")
    
    def test_language_fallback_handling(self):
        """Test language fallback mechanisms."""
        # Test with invalid language
        result = self.news_service.analyze_sentiment("Test text for analysis.", "invalid_lang")
        self.assertEqual(result, "neutral")  # Should fallback gracefully
        
        # Test with supported language
        result = self.news_service.analyze_sentiment("Test text for analysis.", "hi")
        self.assertIn(result, ["positive", "negative", "neutral"])
    
    def test_tts_error_handling(self):
        """Test TTS service error handling."""
        # Test with empty text
        result = self.tts_service.text_to_speech("", "en")
        self.assertIsNone(result)
        
        # Test with None text
        result = self.tts_service.text_to_speech(None, "en")
        self.assertIsNone(result)
        
        # Test with valid text
        result = self.tts_service.text_to_speech("Test text", "en")
        # Result may be None due to TTS service limitations in test environment
        # but should not raise exceptions
        self.assertTrue(result is None or isinstance(result, str))
    
    def test_fallback_manager_functionality(self):
        """Test FallbackManager functionality."""
        # Test language fallback chain
        chain = FallbackManager.get_language_fallback_chain("hi")
        self.assertEqual(chain, ["hi", "en"])
        
        chain = FallbackManager.get_language_fallback_chain("invalid")
        self.assertEqual(chain, ["en"])
        
        # Test sentiment fallback
        fallback = FallbackManager.get_sentiment_fallback()
        self.assertEqual(fallback, "neutral")
        
        # Test summary fallback
        summary = FallbackManager.create_fallback_summary("Test article content.")
        self.assertEqual(summary, "Test article content.")
    
    def test_language_service_integration(self):
        """Test LanguageService integration with error handling."""
        # Test valid language
        self.assertTrue(LanguageService.validate_language("en"))
        self.assertTrue(LanguageService.validate_language("hi"))
        self.assertTrue(LanguageService.validate_language("mr"))
        
        # Test invalid language
        self.assertFalse(LanguageService.validate_language("invalid"))
        self.assertFalse(LanguageService.validate_language(""))
        self.assertFalse(LanguageService.validate_language(None))
        
        # Test fallback language
        fallback = LanguageService.get_fallback_language("invalid")
        self.assertEqual(fallback, "en")
        
        fallback = LanguageService.get_fallback_language("hi")
        self.assertEqual(fallback, "hi")
    
    def test_error_logging_functionality(self):
        """Test error logging functionality."""
        # Clear previous messages
        self.log_messages.clear()
        
        # Test language error logging
        test_error = Exception("Test language error")
        ErrorHandler.log_language_error("test_operation", "hi", test_error, "en")
        
        # Check if error was logged
        error_logged = any("Language error in test_operation" in msg for msg in self.log_messages)
        self.assertTrue(error_logged)
        
        # Test sentiment error logging
        ErrorHandler.log_sentiment_error("test_sentiment", test_error, "neutral")
        
        sentiment_logged = any("Sentiment analysis error" in msg for msg in self.log_messages)
        self.assertTrue(sentiment_logged)
    
    def test_end_to_end_error_resilience(self):
        """Test end-to-end error resilience."""
        # Test complete workflow with potential errors
        article_text = "This is a comprehensive test article that will go through the complete processing pipeline including summary generation, sentiment analysis, and potential TTS conversion."
        
        # Generate summary with sentiment
        result = self.news_service.generate_summary_with_sentiment(article_text, "Test Article", "en")
        
        # Should complete successfully even if AI services fail
        self.assertIsInstance(result, dict)
        self.assertIn('summary', result)
        self.assertIn('sentiment', result)
        
        # Test TTS generation (may fail in test environment but should not crash)
        tts_result = self.tts_service.text_to_speech(result['summary'], "en")
        # Should either succeed or fail gracefully
        self.assertTrue(tts_result is None or isinstance(tts_result, str))
        
        print(f"End-to-end test completed: Summary={result['summary'][:50]}..., Sentiment={result['sentiment']}")


if __name__ == '__main__':
    # Run integration tests
    unittest.main(verbosity=2)