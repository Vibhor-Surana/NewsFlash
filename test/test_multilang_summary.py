"""
Tests for multi-language summary generation functionality in NewsService.

This module tests the language-aware summary generation features including:
- Language parameter acceptance in summary methods
- Language-specific prompt selection logic
- Fallback mechanism for unsupported languages
- Integration with LanguageService
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from news_service import NewsService
from language_service import LanguageService


class TestMultiLanguageSummaryGeneration:
    """Test class for multi-language summary generation functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.news_service = NewsService()
        # Make article long enough to trigger AI processing (>150 chars)
        self.sample_article = "This is a sample news article about technology developments in artificial intelligence and machine learning. It contains important information about recent breakthroughs in the field of computer science and their potential impact on society. The article discusses various aspects of technological advancement and innovation."
        self.sample_title = "Technology News Update"
    
    def test_generate_summary_accepts_language_parameter(self):
        """Test that generate_summary method accepts language parameter."""
        with patch('config.Config.USE_AI_SUMMARY', True):
            with patch.object(self.news_service, '_generate_summary_for_language') as mock_generate:
                mock_generate.return_value = "Test summary"
                
                # Test with English
                result = self.news_service.generate_summary(self.sample_article, self.sample_title, 'en')
                mock_generate.assert_called_with(self.sample_article, self.sample_title, 'en')
                
                # Test with Hindi
                result = self.news_service.generate_summary(self.sample_article, self.sample_title, 'hi')
                mock_generate.assert_called_with(self.sample_article, self.sample_title, 'hi')
    
    def test_generate_summary_with_sentiment_accepts_language_parameter(self):
        """Test that generate_summary_with_sentiment method accepts language parameter."""
        with patch('config.Config.USE_AI_SUMMARY', True):
            with patch.object(self.news_service, '_generate_summary_with_sentiment_for_language') as mock_generate:
                mock_generate.return_value = {'summary': 'Test summary', 'sentiment': 'positive', 'language': 'hi'}
                
                result = self.news_service.generate_summary_with_sentiment(self.sample_article, self.sample_title, 'hi')
                
                assert result['summary'] == 'Test summary'
                assert result['sentiment'] == 'positive'
                assert result['language'] == 'hi'
                mock_generate.assert_called_with(self.sample_article, self.sample_title, 'hi')
    
    def test_language_specific_prompt_selection(self):
        """Test that appropriate prompt templates are selected based on language."""
        # Test English prompt
        en_template = self.news_service.get_sentiment_prompt_template('en')
        assert en_template is not None
        
        # Test Hindi prompt
        hi_template = self.news_service.get_sentiment_prompt_template('hi')
        assert hi_template is not None
        
        # Test Marathi prompt
        mr_template = self.news_service.get_sentiment_prompt_template('mr')
        assert mr_template is not None
        
        # Verify they are different templates
        assert en_template != hi_template
        assert en_template != mr_template
    
    def test_fallback_to_supported_language(self):
        """Test fallback mechanism for unsupported languages."""
        with patch('config.Config.USE_AI_SUMMARY', True):
            with patch.object(LanguageService, 'get_fallback_language') as mock_fallback:
                mock_fallback.return_value = 'en'
                
                with patch.object(self.news_service, '_generate_summary_for_language') as mock_generate:
                    mock_generate.return_value = "Fallback summary"
                    
                    # Test with unsupported language
                    result = self.news_service.generate_summary(self.sample_article, self.sample_title, 'fr')
                    
                    # Should call fallback language (English)
                    mock_fallback.assert_called_with('fr')
                    mock_generate.assert_called_with(self.sample_article, self.sample_title, 'en')
    
    def test_fallback_to_english_on_language_failure(self):
        """Test fallback to English when target language fails."""
        with patch('config.Config.USE_AI_SUMMARY', True):
            with patch.object(self.news_service, '_generate_summary_with_sentiment_for_language') as mock_generate:
                # First call (Hindi) fails, second call (English) succeeds
                mock_generate.side_effect = [
                    Exception("Hindi generation failed"),
                    {'summary': 'English fallback summary', 'sentiment': 'neutral', 'language': 'en'}
                ]
                
                result = self.news_service.generate_summary_with_sentiment(self.sample_article, self.sample_title, 'hi')
                
                # Should have tried Hindi first, then English
                assert mock_generate.call_count == 2
                assert result['summary'] == 'English fallback summary'
                assert result['language'] == 'en'
    
    def test_search_news_with_language_parameter(self):
        """Test that search_news method accepts and uses language parameter."""
        with patch.object(self.news_service.ddgs, 'news') as mock_search:
            # Make the body long enough to trigger AI processing
            long_body = "Test article body content for testing purposes with artificial intelligence and machine learning developments. This article contains detailed information about recent technological breakthroughs and their impact on society."
            mock_search.return_value = [
                {
                    'title': 'Test Article',
                    'url': 'http://example.com',
                    'body': long_body,
                    'date': '2024-01-01',
                    'source': 'Test Source'
                }
            ]
            
            with patch.object(self.news_service, 'generate_summary') as mock_summary:
                mock_summary.return_value = "Test summary in Hindi"
                
                results = self.news_service.search_news("technology", max_results=1, language='hi')
                
                assert len(results) == 1
                assert results[0]['language'] == 'hi'
                mock_summary.assert_called_with(
                    long_body,
                    'Test Article',
                    'hi'
                )
    
    def test_search_multiple_topics_with_language_parameter(self):
        """Test that search_multiple_topics method accepts and uses language parameter."""
        with patch.object(self.news_service, 'search_news') as mock_search:
            mock_search.return_value = [{'title': 'Test', 'language': 'mr'}]
            
            results = self.news_service.search_multiple_topics(['tech', 'sports'], language='mr')
            
            # Should call search_news with Marathi language for each topic
            assert mock_search.call_count == 2
            mock_search.assert_any_call('tech', 5, 'mr')
            mock_search.assert_any_call('sports', 5, 'mr')
    
    def test_analyze_sentiment_with_language_parameter(self):
        """Test that analyze_sentiment method accepts and uses language parameter."""
        with patch.object(self.news_service, 'get_sentiment_prompt_template') as mock_template:
            mock_template.return_value = self.news_service.prompt_templates['hi']
            
            # Mock the chain invoke instead of llm directly
            with patch('time.sleep'):  # Skip rate limiting delay
                with patch.object(self.news_service.llm, '__or__') as mock_chain:
                    mock_response = Mock()
                    mock_response.content = "भावना: सकारात्मक"
                    
                    mock_chain_obj = Mock()
                    mock_chain_obj.invoke.return_value = mock_response
                    mock_chain.return_value = mock_chain_obj
                    
                    # Use longer text to avoid short text fallback
                    long_text = "Good news about technology developments in artificial intelligence and machine learning with positive impact on society and innovation."
                    result = self.news_service.analyze_sentiment(long_text, 'hi')
                    
                    mock_template.assert_called_with('hi')
                    assert result == 'positive'
    
    def test_language_validation_integration(self):
        """Test integration with LanguageService for language validation."""
        # Test valid languages
        assert LanguageService.validate_language('en') == True
        assert LanguageService.validate_language('hi') == True
        assert LanguageService.validate_language('mr') == True
        
        # Test invalid language
        assert LanguageService.validate_language('fr') == False
        
        # Test fallback behavior
        assert LanguageService.get_fallback_language('en') == 'en'
        assert LanguageService.get_fallback_language('hi') == 'hi'
        assert LanguageService.get_fallback_language('fr') == 'en'  # Should fallback to English
    
    def test_short_article_handling_with_language(self):
        """Test handling of short articles with different languages."""
        short_article = "Short."
        
        # Should return fallback summary regardless of language
        result_en = self.news_service.generate_summary(short_article, "Title", 'en')
        result_hi = self.news_service.generate_summary(short_article, "Title", 'hi')
        
        assert result_en == short_article  # Should return original text for short articles
        assert result_hi == short_article
    
    def test_sentiment_analysis_fallback_with_language(self):
        """Test sentiment analysis fallback behavior with different languages."""
        # Test with very short text
        result = self.news_service.analyze_sentiment("Hi", 'hi')
        assert result == 'neutral'
        
        # Test with error handling
        with patch('time.sleep'):  # Skip rate limiting delay
            with patch.object(self.news_service.llm, '__or__') as mock_chain:
                mock_chain_obj = Mock()
                mock_chain_obj.invoke.side_effect = Exception("API Error")
                mock_chain.return_value = mock_chain_obj
                
                long_text = "Some text about technology and artificial intelligence developments with detailed information."
                result = self.news_service.analyze_sentiment(long_text, 'mr')
                assert result == 'neutral'
    
    def test_prompt_template_content_validation(self):
        """Test that prompt templates contain appropriate language-specific content."""
        # English template should contain English instructions
        en_template = self.news_service.get_sentiment_prompt_template('en')
        en_messages = en_template.format_messages(title="Test", article_text="Test")
        en_content = en_messages[0].content
        assert "Create a 2-sentence summary" in en_content
        assert "positive/negative/neutral" in en_content
        
        # Hindi template should contain Hindi instructions
        hi_template = self.news_service.get_sentiment_prompt_template('hi')
        hi_messages = hi_template.format_messages(title="Test", article_text="Test")
        hi_content = hi_messages[0].content
        assert "सारांश" in hi_content
        assert "भावना" in hi_content
        
        # Marathi template should contain Marathi instructions
        mr_template = self.news_service.get_sentiment_prompt_template('mr')
        mr_messages = mr_template.format_messages(title="Test", article_text="Test")
        mr_content = mr_messages[0].content
        assert "सारांश" in mr_content
        assert "भावना" in mr_content


if __name__ == '__main__':
    pytest.main([__file__])