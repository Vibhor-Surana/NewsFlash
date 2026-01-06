import unittest
from unittest.mock import Mock, patch, MagicMock
from news_service import NewsService

class TestSentimentAnalysis(unittest.TestCase):
    def setUp(self):
        self.news_service = NewsService()
    
    def test_parse_sentiment_from_response_english(self):
        """Test parsing sentiment from English AI response"""
        # Test positive sentiment
        response = "Summary: This is great news about economic growth.\nSentiment: positive"
        sentiment = self.news_service._parse_sentiment_from_response(response)
        self.assertEqual(sentiment, 'positive')
        
        # Test negative sentiment
        response = "Summary: This is concerning news about the crisis.\nSentiment: negative"
        sentiment = self.news_service._parse_sentiment_from_response(response)
        self.assertEqual(sentiment, 'negative')
        
        # Test neutral sentiment
        response = "Summary: This is factual reporting.\nSentiment: neutral"
        sentiment = self.news_service._parse_sentiment_from_response(response)
        self.assertEqual(sentiment, 'neutral')
    
    def test_parse_sentiment_from_response_hindi(self):
        """Test parsing sentiment from Hindi AI response"""
        # Test positive sentiment in Hindi
        response = "सारांश: यह आर्थिक विकास के बारे में अच्छी खबर है।\nभावना: सकारात्मक"
        sentiment = self.news_service._parse_sentiment_from_response(response)
        self.assertEqual(sentiment, 'positive')
        
        # Test negative sentiment in Hindi
        response = "सारांश: यह संकट के बारे में चिंताजनक खबर है।\nभावना: नकारात्मक"
        sentiment = self.news_service._parse_sentiment_from_response(response)
        self.assertEqual(sentiment, 'negative')
    
    def test_parse_sentiment_fallback(self):
        """Test sentiment parsing fallback to neutral"""
        # Test unclear response
        response = "This is some unclear response without clear sentiment indicators"
        sentiment = self.news_service._parse_sentiment_from_response(response)
        self.assertEqual(sentiment, 'neutral')
        
        # Test empty response
        response = ""
        sentiment = self.news_service._parse_sentiment_from_response(response)
        self.assertEqual(sentiment, 'neutral')
    
    def test_parse_summary_and_sentiment(self):
        """Test parsing both summary and sentiment from response"""
        response = """Summary: This is a great development in technology sector.
        Sentiment: positive"""
        
        summary, sentiment = self.news_service._parse_summary_and_sentiment(response)
        self.assertEqual(summary, "This is a great development in technology sector.")
        self.assertEqual(sentiment, 'positive')
    
    def test_parse_summary_and_sentiment_hindi(self):
        """Test parsing summary and sentiment from Hindi response"""
        response = """सारांश: यह प्रौद्योगिकी क्षेत्र में एक महान विकास है।
        भावना: सकारात्मक"""
        
        summary, sentiment = self.news_service._parse_summary_and_sentiment(response)
        self.assertEqual(summary, "यह प्रौद्योगिकी क्षेत्र में एक महान विकास है।")
        self.assertEqual(sentiment, 'positive')
    
    @patch('news_service.Config.AI_SUMMARY_MIN_LENGTH', 10)
    @patch('news_service.Config.USE_AI_SUMMARY', True)
    @patch('news_service.Config.RATE_LIMIT_DELAY', 0)
    def test_analyze_sentiment_short_text(self):
        """Test sentiment analysis for very short text"""
        short_text = "Hi"
        sentiment = self.news_service.analyze_sentiment(short_text)
        self.assertEqual(sentiment, 'neutral')
    
    @patch('news_service.Config.AI_SUMMARY_MIN_LENGTH', 10)
    @patch('news_service.Config.USE_AI_SUMMARY', True)
    @patch('news_service.Config.RATE_LIMIT_DELAY', 0)
    def test_analyze_sentiment_with_mock_llm(self):
        """Test sentiment analysis with mocked LLM response"""
        # Mock the LLM response
        mock_result = Mock()
        mock_result.content = "Summary: Great news about economic growth.\nSentiment: positive"
        
        with patch.object(self.news_service, 'llm') as mock_llm:
            mock_chain = Mock()
            mock_chain.invoke.return_value = mock_result
            
            with patch.object(self.news_service, 'get_sentiment_prompt_template') as mock_template:
                mock_template.return_value.__or__ = Mock(return_value=mock_chain)
                
                sentiment = self.news_service.analyze_sentiment("This is great economic news about growth and prosperity.")
                self.assertEqual(sentiment, 'positive')
    
    @patch('news_service.Config.AI_SUMMARY_MIN_LENGTH', 10)
    @patch('news_service.Config.USE_AI_SUMMARY', True)
    @patch('news_service.Config.RATE_LIMIT_DELAY', 0)
    def test_analyze_sentiment_error_handling(self):
        """Test sentiment analysis error handling"""
        # Mock LLM to raise an exception
        with patch.object(self.news_service, 'llm') as mock_llm:
            mock_chain = Mock()
            mock_chain.invoke.side_effect = Exception("API Error")
            
            with patch.object(self.news_service, 'get_sentiment_prompt_template') as mock_template:
                mock_template.return_value.__or__ = Mock(return_value=mock_chain)
                
                sentiment = self.news_service.analyze_sentiment("Some news text")
                self.assertEqual(sentiment, 'neutral')  # Should fallback to neutral
    
    @patch('news_service.Config.AI_SUMMARY_MIN_LENGTH', 10)
    @patch('news_service.Config.USE_AI_SUMMARY', True)
    @patch('news_service.Config.RATE_LIMIT_DELAY', 0)
    def test_generate_summary_with_sentiment(self):
        """Test combined summary and sentiment generation"""
        # Mock the LLM response
        mock_result = Mock()
        mock_result.content = "Summary: This is excellent news about technological advancement.\nSentiment: positive"
        
        with patch.object(self.news_service, 'llm') as mock_llm:
            mock_chain = Mock()
            mock_chain.invoke.return_value = mock_result
            
            with patch.object(self.news_service, 'get_sentiment_prompt_template') as mock_template:
                mock_template.return_value.__or__ = Mock(return_value=mock_chain)
                
                result = self.news_service.generate_summary_with_sentiment(
                    "This is a long article about technological advancement and innovation.",
                    "Tech News"
                )
                
                self.assertIsInstance(result, dict)
                self.assertIn('summary', result)
                self.assertIn('sentiment', result)
                self.assertEqual(result['sentiment'], 'positive')
                self.assertIn('technological advancement', result['summary'])
    
    @patch('news_service.Config.AI_SUMMARY_MIN_LENGTH', 100)
    @patch('news_service.Config.USE_AI_SUMMARY', True)
    def test_generate_summary_with_sentiment_short_article(self):
        """Test summary with sentiment for short articles"""
        short_article = "Short news."
        
        result = self.news_service.generate_summary_with_sentiment(short_article, "Short Title")
        
        self.assertIsInstance(result, dict)
        self.assertIn('summary', result)
        self.assertIn('sentiment', result)
        self.assertEqual(result['sentiment'], 'neutral')
        self.assertEqual(result['summary'], short_article)  # Should use fallback
    
    @patch('news_service.Config.AI_SUMMARY_MIN_LENGTH', 10)
    @patch('news_service.Config.USE_AI_SUMMARY', False)
    def test_generate_summary_with_sentiment_ai_disabled(self):
        """Test summary with sentiment when AI is disabled"""
        article = "This is a longer article about some news event that should normally trigger AI analysis."
        
        result = self.news_service.generate_summary_with_sentiment(article, "News Title")
        
        self.assertIsInstance(result, dict)
        self.assertIn('summary', result)
        self.assertIn('sentiment', result)
        self.assertEqual(result['sentiment'], 'neutral')
        # Should use fallback summary
        self.assertTrue(len(result['summary']) > 0)
    
    def test_generate_summary_backward_compatibility(self):
        """Test that generate_summary maintains backward compatibility"""
        with patch.object(self.news_service, '_create_fallback_summary') as mock_fallback:
            mock_fallback.return_value = "Fallback summary"
            
            # Test without sentiment (backward compatible)
            result = self.news_service.generate_summary("Short article", "Title")
            self.assertIsInstance(result, str)
            
            # Test with sentiment
            result = self.news_service.generate_summary("Short article", "Title", include_sentiment=True)
            self.assertIsInstance(result, dict)
            self.assertIn('summary', result)
            self.assertIn('sentiment', result)

if __name__ == '__main__':
    unittest.main()