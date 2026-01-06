"""
Tests for sentiment analysis error handling scenarios.
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import logging

from news_service import NewsService
from error_handler import ErrorHandler, FallbackManager, SentimentAnalysisError
from config import Config


class TestSentimentErrorScenarios(unittest.TestCase):
    """Test sentiment analysis error scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.news_service = NewsService()
        
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
    
    def test_sentiment_analysis_empty_response(self):
        """Test sentiment analysis with empty AI response."""
        with patch.object(self.news_service, 'get_sentiment_prompt_template') as mock_template:
            with patch.object(self.news_service.llm, 'invoke') as mock_invoke:
                # Mock empty response
                mock_result = Mock()
                mock_result.content = ""
                mock_invoke.return_value = mock_result
                
                result = self.news_service.analyze_sentiment("Test article text", "en")
                
                # Should fallback to neutral
                self.assertEqual(result, "neutral")
    
    def test_sentiment_analysis_malformed_response(self):
        """Test sentiment analysis with malformed AI response."""
        with patch.object(self.news_service, 'get_sentiment_prompt_template') as mock_template:
            with patch.object(self.news_service.llm, 'invoke') as mock_invoke:
                # Mock malformed response
                mock_result = Mock()
                mock_result.content = "This is not a proper sentiment response format"
                mock_invoke.return_value = mock_result
                
                result = self.news_service.analyze_sentiment("Test article text", "en")
                
                # Should fallback to neutral when parsing fails
                self.assertEqual(result, "neutral")
    
    def test_sentiment_analysis_no_content_attribute(self):
        """Test sentiment analysis when AI response has no content attribute."""
        with patch.object(self.news_service, 'get_sentiment_prompt_template') as mock_template:
            with patch.object(self.news_service.llm, 'invoke') as mock_invoke:
                # Mock response without content attribute
                mock_result = Mock(spec=[])  # No content attribute
                mock_invoke.return_value = mock_result
                
                result = self.news_service.analyze_sentiment("Test article text", "en")
                
                # Should fallback to neutral
                self.assertEqual(result, "neutral")
    
    def test_sentiment_parsing_different_languages(self):
        """Test sentiment parsing from responses in different languages."""
        test_cases = [
            # English responses
            ("Summary: Good news today.\nSentiment: positive", "positive"),
            ("Summary: Bad news today.\nSentiment: negative", "negative"),
            ("Summary: Regular news.\nSentiment: neutral", "neutral"),
            
            # Hindi responses
            ("सारांश: अच्छी खबर।\nभावना: सकारात्मक", "positive"),
            ("सारांश: बुरी खबर।\nभावना: नकारात्मक", "negative"),
            ("सारांश: सामान्य खबर।\nभावना: तटस्थ", "neutral"),
            
            # Mixed format responses
            ("The sentiment is positive for this article", "positive"),
            ("This article has negative sentiment", "negative"),
            ("Neutral sentiment detected", "neutral"),
            
            # Malformed responses
            ("No clear sentiment indicators", "neutral"),
            ("", "neutral"),
        ]
        
        for response_text, expected_sentiment in test_cases:
            result = self.news_service._parse_sentiment_from_response(response_text)
            self.assertEqual(result, expected_sentiment, 
                           f"Failed for response: '{response_text}'")
    
    def test_sentiment_analysis_very_short_text(self):
        """Test sentiment analysis with very short text."""
        short_texts = [
            "",
            "Hi",
            "OK",
            "Yes",
            "No",
            "A",
            "Test",
        ]
        
        for text in short_texts:
            result = self.news_service.analyze_sentiment(text, "en")
            self.assertEqual(result, "neutral", 
                           f"Short text '{text}' should return neutral sentiment")
    
    @patch('news_service.ChatGoogleGenerativeAI')
    def test_sentiment_analysis_api_timeout(self, mock_llm):
        """Test sentiment analysis with API timeout."""
        # Mock timeout error
        mock_llm.return_value.invoke.side_effect = Exception("Request timeout")
        
        result = self.news_service.analyze_sentiment("Test article text", "en")
        
        # Should fallback to neutral
        self.assertEqual(result, "neutral")
        
        # Check that error was logged
        error_logged = any("sentiment analysis" in msg.lower() for msg in self.log_messages)
        self.assertTrue(error_logged)
    
    @patch('news_service.ChatGoogleGenerativeAI')
    def test_sentiment_analysis_network_error(self, mock_llm):
        """Test sentiment analysis with network error."""
        # Mock network error
        mock_llm.return_value.invoke.side_effect = Exception("Network connection failed")
        
        result = self.news_service.analyze_sentiment("Test article text", "en")
        
        # Should fallback to neutral
        self.assertEqual(result, "neutral")
    
    @patch('news_service.ChatGoogleGenerativeAI')
    def test_sentiment_analysis_authentication_error(self, mock_llm):
        """Test sentiment analysis with authentication error."""
        # Mock authentication error
        mock_llm.return_value.invoke.side_effect = Exception("401 Authentication failed")
        
        result = self.news_service.analyze_sentiment("Test article text", "en")
        
        # Should fallback to neutral
        self.assertEqual(result, "neutral")
    
    def test_combined_summary_sentiment_parsing_errors(self):
        """Test parsing errors in combined summary and sentiment generation."""
        test_cases = [
            # Missing summary
            ("Sentiment: positive", None, "positive"),
            
            # Missing sentiment
            ("Summary: This is a summary.", "This is a summary.", "neutral"),
            
            # Both missing
            ("Random text without format", None, "neutral"),
            
            # Partial format
            ("Summary: Good news\nSome other text", "Good news", "neutral"),
            
            # Multiple lines after summary
            ("Summary: Line 1\nLine 2\nSentiment: positive", "Line 1 Line 2", "positive"),
        ]
        
        for response_text, expected_summary, expected_sentiment in test_cases:
            summary, sentiment = self.news_service._parse_summary_and_sentiment(response_text)
            
            if expected_summary is None:
                self.assertIsNone(summary, f"Summary should be None for: '{response_text}'")
            else:
                self.assertEqual(summary, expected_summary, 
                               f"Summary mismatch for: '{response_text}'")
            
            self.assertEqual(sentiment, expected_sentiment, 
                           f"Sentiment mismatch for: '{response_text}'")
    
    @patch('news_service.Config.SENTIMENT_FALLBACK_ENABLED', False)
    def test_sentiment_fallback_disabled(self):
        """Test behavior when sentiment fallback is disabled."""
        with patch('news_service.ChatGoogleGenerativeAI') as mock_llm:
            # Mock LLM to raise an exception
            mock_llm.return_value.invoke.side_effect = Exception("Sentiment analysis failed")
            
            # When fallback is disabled, should still return neutral due to decorator
            result = self.news_service.analyze_sentiment("Test text", "en")
            self.assertEqual(result, "neutral")
    
    def test_sentiment_analysis_with_special_characters(self):
        """Test sentiment analysis with text containing special characters."""
        special_texts = [
            "Great news! 🎉 Everything is awesome!",
            "Bad news... 😢 Things are terrible.",
            "Normal news. Nothing special here.",
            "Text with @mentions and #hashtags",
            "Text with URLs: https://example.com",
            "Text with numbers: 123, 456.78, $100",
        ]
        
        for text in special_texts:
            # Should not crash and should return a valid sentiment
            result = self.news_service.analyze_sentiment(text, "en")
            self.assertIn(result, ["positive", "negative", "neutral"], 
                         f"Invalid sentiment for text: '{text}'")
    
    @patch('news_service.ChatGoogleGenerativeAI')
    def test_sentiment_analysis_rate_limiting(self, mock_llm):
        """Test sentiment analysis with rate limiting."""
        # Mock rate limit error
        mock_llm.return_value.invoke.side_effect = Exception("429 Too Many Requests")
        
        result = self.news_service.analyze_sentiment("Test article text", "en")
        
        # Should fallback to neutral
        self.assertEqual(result, "neutral")
        
        # Check that rate limit was logged
        rate_limit_logged = any("rate limit" in msg.lower() for msg in self.log_messages)
        self.assertTrue(rate_limit_logged)
    
    def test_sentiment_consistency_across_languages(self):
        """Test that sentiment fallback is consistent across languages."""
        languages = ["en", "hi", "mr", "invalid"]
        
        with patch.object(self.news_service.llm, 'invoke') as mock_invoke:
            # Mock to always fail
            mock_invoke.side_effect = Exception("AI service unavailable")
            
            for lang in languages:
                result = self.news_service.analyze_sentiment("Test text", lang)
                self.assertEqual(result, "neutral", 
                               f"Sentiment fallback should be neutral for language: {lang}")
    
    def test_sentiment_error_logging_details(self):
        """Test detailed error logging for sentiment analysis."""
        with patch.object(self.news_service.llm, 'invoke') as mock_invoke:
            # Mock specific error
            test_error = Exception("Specific sentiment analysis error")
            mock_invoke.side_effect = test_error
            
            result = self.news_service.analyze_sentiment("Test text", "en")
            
            # Should fallback to neutral
            self.assertEqual(result, "neutral")
            
            # Check that specific error details were logged
            error_details_logged = any("Specific sentiment analysis error" in msg for msg in self.log_messages)
            self.assertTrue(error_details_logged)


class TestSentimentFallbackManager(unittest.TestCase):
    """Test sentiment-related fallback manager functionality."""
    
    def test_sentiment_fallback_value(self):
        """Test that sentiment fallback returns correct value."""
        fallback = FallbackManager.get_sentiment_fallback()
        self.assertEqual(fallback, "neutral")
    
    def test_sentiment_fallback_consistency(self):
        """Test that sentiment fallback is consistent across calls."""
        fallback1 = FallbackManager.get_sentiment_fallback()
        fallback2 = FallbackManager.get_sentiment_fallback()
        self.assertEqual(fallback1, fallback2)
    
    def test_sentiment_error_handler_logging(self):
        """Test sentiment error handler logging functionality."""
        # Capture log messages
        log_messages = []
        handler = logging.Handler()
        handler.emit = lambda record: log_messages.append(record.getMessage())
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.DEBUG)
        
        try:
            test_error = Exception("Test sentiment error")
            ErrorHandler.log_sentiment_error("test_operation", test_error, "neutral")
            
            # Check that error was logged with correct details
            error_logged = any("Sentiment analysis error in test_operation" in msg for msg in log_messages)
            self.assertTrue(error_logged)
            
            fallback_logged = any("Fallback used: neutral" in msg for msg in log_messages)
            self.assertTrue(fallback_logged)
            
        finally:
            logging.getLogger().removeHandler(handler)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)