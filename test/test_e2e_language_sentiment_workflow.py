#!/usr/bin/env python3
"""
End-to-End Integration Tests for Language and Sentiment Workflow

This test suite covers the complete user journey with language selection,
sentiment analysis integration, TTS functionality, and error handling.
Tests Requirements: 1.1, 2.1, 3.1, 4.2
"""

import pytest
import json
import time
import os
import tempfile
import uuid
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timezone

# Add the project root to the Python path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import NewsArticle, ConversationSession
from news_service import NewsService
from tts_service import TTSService
from language_service import LanguageService
from session_manager import SessionManager


class TestE2ELanguageSentimentWorkflow:
    """End-to-end integration tests for language and sentiment workflow."""
    
    @pytest.fixture
    def test_app(self):
        """Configure test Flask app."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, test_app):
        """Create test client."""
        return test_app.test_client()
    
    @pytest.fixture
    def mock_session_id(self):
        """Generate a mock session ID."""
        return str(uuid.uuid4())
    
    @pytest.fixture
    def test_articles_data(self):
        """Sample test articles with different sentiments and languages."""
        return [
            {
                'title': 'Revolutionary AI Breakthrough Announced',
                'body': 'Scientists at leading research institutions have announced a major breakthrough in artificial intelligence technology that promises to revolutionize healthcare and education. The new AI system demonstrates unprecedented accuracy in medical diagnosis and personalized learning.',
                'url': 'https://example.com/ai-breakthrough',
                'expected_sentiment': 'positive',
                'topic': 'technology'
            },
            {
                'title': 'Economic Crisis Deepens Worldwide',
                'body': 'Global economic indicators continue to show worsening conditions as inflation rises and unemployment reaches critical levels. Financial experts warn of potential recession and market instability in the coming months.',
                'url': 'https://example.com/economic-crisis',
                'expected_sentiment': 'negative',
                'topic': 'economy'
            },
            {
                'title': 'Weather Forecast for Next Week',
                'body': 'Next week will see partly cloudy skies with temperatures ranging from 20 to 25 degrees Celsius. Light rain is expected on Wednesday and Thursday, followed by clear skies for the weekend.',
                'url': 'https://example.com/weather-forecast',
                'expected_sentiment': 'neutral',
                'topic': 'weather'
            }
        ]
    
    # Test 1: Complete User Journey with Language Selection
    
    def test_complete_user_journey_english(self, client, test_app, mock_session_id, test_articles_data):
        """Test complete user journey in English language."""
        with test_app.app_context():
            # Step 1: Initialize session
            with client.session_transaction() as sess:
                sess['session_id'] = mock_session_id
            
            # Step 2: Set language preference to English
            response = client.post('/set-language', json={'language': 'en'})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['language'] == 'en'
            
            # Step 3: Verify language preference is stored
            response = client.get('/get-languages')
            assert response.status_code == 200
            data = response.get_json()
            assert data['current_language'] == 'en'
            
            # Step 4: Mock news search and sentiment analysis
            with patch('news_service.NewsService.search_news') as mock_search, \
                 patch('news_service.NewsService.generate_summary_with_sentiment') as mock_sentiment:
                
                # Configure mocks
                mock_search.return_value = [test_articles_data[0]]  # Positive article
                mock_sentiment.return_value = {
                    'summary': 'AI breakthrough promises to revolutionize healthcare and education.',
                    'sentiment': 'positive',
                    'language': 'en'
                }
                
                # Step 5: Perform search with language parameter
                response = client.post('/search', json={
                    'query': 'technology',
                    'language': 'en',
                    'max_results': 1
                })
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert data['language'] == 'en'
                assert len(data['articles']) == 1
                
                article = data['articles'][0]
                assert article['sentiment'] == 'positive'
                assert article['language'] == 'en'
                assert 'summary' in article
                
                # Verify mocks were called with correct parameters
                mock_search.assert_called_once_with('technology', 1, 'en')
                mock_sentiment.assert_called_once()
    
    def test_complete_user_journey_hindi(self, client, test_app, mock_session_id, test_articles_data):
        """Test complete user journey in Hindi language."""
        with test_app.app_context():
            # Step 1: Initialize session
            with client.session_transaction() as sess:
                sess['session_id'] = mock_session_id
            
            # Step 2: Set language preference to Hindi
            response = client.post('/set-language', json={'language': 'hi'})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['language'] == 'hi'
            
            # Step 3: Mock news search and sentiment analysis for Hindi
            with patch('news_service.NewsService.search_news') as mock_search, \
                 patch('news_service.NewsService.generate_summary_with_sentiment') as mock_sentiment:
                
                # Configure mocks for Hindi
                mock_search.return_value = [test_articles_data[1]]  # Negative article
                mock_sentiment.return_value = {
                    'summary': 'वैश्विक आर्थिक संकेतक बिगड़ती स्थितियों को दर्शाते हैं।',
                    'sentiment': 'negative',
                    'language': 'hi'
                }
                
                # Step 4: Perform search in Hindi
                response = client.post('/search', json={
                    'query': 'economy',
                    'language': 'hi',
                    'max_results': 1
                })
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert data['language'] == 'hi'
                
                article = data['articles'][0]
                assert article['sentiment'] == 'negative'
                assert article['language'] == 'hi'
                
                # Verify Hindi was used in the search
                mock_search.assert_called_once_with('economy', 1, 'hi')
    
    def test_complete_user_journey_marathi(self, client, test_app, mock_session_id, test_articles_data):
        """Test complete user journey in Marathi language."""
        with test_app.app_context():
            # Step 1: Initialize session
            with client.session_transaction() as sess:
                sess['session_id'] = mock_session_id
            
            # Step 2: Set language preference to Marathi
            response = client.post('/set-language', json={'language': 'mr'})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['language'] == 'mr'
            
            # Step 3: Mock news search and sentiment analysis for Marathi
            with patch('news_service.NewsService.search_news') as mock_search, \
                 patch('news_service.NewsService.generate_summary_with_sentiment') as mock_sentiment:
                
                # Configure mocks for Marathi
                mock_search.return_value = [test_articles_data[2]]  # Neutral article
                mock_sentiment.return_value = {
                    'summary': 'पुढील आठवड्यात अंशतः ढगाळ आकाश असेल.',
                    'sentiment': 'neutral',
                    'language': 'mr'
                }
                
                # Step 4: Perform search in Marathi
                response = client.post('/search', json={
                    'query': 'weather',
                    'language': 'mr',
                    'max_results': 1
                })
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert data['language'] == 'mr'
                
                article = data['articles'][0]
                assert article['sentiment'] == 'neutral'
                assert article['language'] == 'mr'
                
                # Verify Marathi was used in the search
                mock_search.assert_called_once_with('weather', 1, 'mr')
    
    # Test 2: Sentiment Analysis Integration with Multi-Language Summaries
    
    def test_sentiment_analysis_with_multilingual_summaries(self, test_app):
        """Test sentiment analysis integration with summaries in different languages."""
        with test_app.app_context():
            news_service = NewsService()
            
            test_cases = [
                {
                    'text': 'Great news! Scientists have made a breakthrough discovery that will revolutionize medicine and healthcare worldwide. This amazing development promises to save millions of lives and improve quality of life for patients everywhere. The research team has worked tirelessly for years to achieve this remarkable milestone.',
                    'title': 'Scientific Breakthrough',
                    'language': 'en',
                    'expected_sentiment': 'positive'
                },
                {
                    'text': 'Tragic accident results in multiple casualties and widespread damage across the region. Emergency services are overwhelmed as they respond to the devastating incident that has left families shattered and communities in mourning. The full extent of the damage is still being assessed.',
                    'title': 'Tragic Accident',
                    'language': 'en',
                    'expected_sentiment': 'negative'
                },
                {
                    'text': 'The meeting was held as scheduled with standard agenda items discussed by committee members. Various reports were presented and reviewed according to the established procedures. The session concluded with routine administrative matters being addressed.',
                    'title': 'Regular Meeting',
                    'language': 'en',
                    'expected_sentiment': 'neutral'
                }
            ]
            
            for case in test_cases:
                # Mock the handle_language_operation function to return our expected result
                with patch('news_service.handle_language_operation') as mock_handle:
                    mock_handle.return_value = {
                        'summary': f"Test summary for {case['title']}",
                        'sentiment': case['expected_sentiment'],
                        'language': case['language']
                    }
                    
                    # Test sentiment analysis integration
                    result = news_service.generate_summary_with_sentiment(
                        case['text'], case['title'], case['language']
                    )
                    
                    assert result['sentiment'] == case['expected_sentiment']
                    assert result['language'] == case['language']
                    assert 'summary' in result
                    
                    # Verify the handle_language_operation was called
                    mock_handle.assert_called_once()
    
    # Test 3: TTS Functionality Across All Supported Languages
    
    def test_tts_functionality_all_languages(self, client, test_app, mock_session_id):
        """Test TTS functionality across all supported languages."""
        with test_app.app_context():
            # Initialize session
            with client.session_transaction() as sess:
                sess['session_id'] = mock_session_id
            
            test_text = "This is a test message for text-to-speech conversion."
            supported_languages = LanguageService.get_supported_languages()
            
            for lang_code in supported_languages.keys():
                with patch('tts_service.TTSService._generate_tts_for_language') as mock_tts:
                    # Mock successful TTS generation
                    mock_tts.return_value = True
                    
                    # Mock file creation
                    with patch('os.path.exists', return_value=True), \
                         patch('os.path.getsize', return_value=1024):
                        
                        # Test TTS generation for each language
                        response = client.post('/tts', json={
                            'text': test_text,
                            'language': lang_code
                        })
                        
                        assert response.status_code == 200
                        data = response.get_json()
                        assert data['success'] is True
                        assert data['language'] == lang_code
                        assert 'audio_url' in data
                        
                        # Verify TTS was called with correct language
                        mock_tts.assert_called_once()
    
    def test_tts_with_session_language_preference(self, client, test_app, mock_session_id):
        """Test TTS uses session language preference when not specified in request."""
        with test_app.app_context():
            # Initialize session
            with client.session_transaction() as sess:
                sess['session_id'] = mock_session_id
            
            # Set language preference to Hindi
            response = client.post('/set-language', json={'language': 'hi'})
            assert response.status_code == 200
            
            with patch('tts_service.TTSService._generate_tts_for_language') as mock_tts:
                mock_tts.return_value = True
                
                with patch('os.path.exists', return_value=True), \
                     patch('os.path.getsize', return_value=1024):
                    
                    # Test TTS without specifying language (should use session preference)
                    response = client.post('/tts', json={
                        'text': 'Test message'
                    })
                    
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['success'] is True
                    assert data['language'] == 'hi'  # Should use session preference
    
    # Test 4: Error Handling and Fallback Mechanisms
    
    def test_language_fallback_mechanisms(self, client, test_app, mock_session_id):
        """Test language fallback mechanisms when unsupported language is requested."""
        with test_app.app_context():
            # Initialize session
            with client.session_transaction() as sess:
                sess['session_id'] = mock_session_id
            
            # Test 1: Unsupported language in search should fallback to English
            with patch('news_service.NewsService.search_news') as mock_search:
                mock_search.return_value = []
                
                response = client.post('/search', json={
                    'query': 'test',
                    'language': 'unsupported_lang',
                    'max_results': 1
                })
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['language'] == 'en'  # Should fallback to English
                
                # Verify search was called with fallback language
                mock_search.assert_called_once_with('test', 1, 'en')
            
            # Test 2: Unsupported language in TTS should fallback to English
            with patch('tts_service.TTSService._generate_tts_for_language') as mock_tts:
                mock_tts.return_value = True
                
                with patch('os.path.exists', return_value=True), \
                     patch('os.path.getsize', return_value=1024):
                    
                    response = client.post('/tts', json={
                        'text': 'Test message',
                        'language': 'unsupported_lang'
                    })
                    
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['language'] == 'en'  # Should fallback to English
    
    def test_sentiment_analysis_error_handling(self, test_app):
        """Test sentiment analysis error handling and fallback to neutral."""
        with test_app.app_context():
            news_service = NewsService()
            
            # Test 1: AI service failure should fallback to neutral sentiment
            with patch.object(news_service, '_generate_summary_with_sentiment_for_language') as mock_generate:
                mock_generate.side_effect = Exception("AI service error")
                
                result = news_service.generate_summary_with_sentiment(
                    "Test article text", "Test Title", "en"
                )
                
                assert result['sentiment'] == 'neutral'  # Should fallback to neutral
                assert 'summary' in result  # Should still provide a summary
                assert result['language'] == 'en'
            
            # Test 2: Very short text should return neutral sentiment
            result = news_service.generate_summary_with_sentiment(
                "Short", "Title", "en"
            )
            
            assert result['sentiment'] == 'neutral'
            assert result['language'] == 'en'
    
    def test_tts_error_handling(self, client, test_app, mock_session_id):
        """Test TTS error handling and fallback mechanisms."""
        with test_app.app_context():
            # Initialize session
            with client.session_transaction() as sess:
                sess['session_id'] = mock_session_id
            
            # Test 1: TTS generation failure should return error
            with patch('tts_service.TTSService._generate_tts_for_language') as mock_tts:
                mock_tts.side_effect = Exception("TTS generation failed")
                
                response = client.post('/tts', json={
                    'text': 'Test message',
                    'language': 'en'
                })
                
                assert response.status_code == 500
                data = response.get_json()
                assert 'error' in data
            
            # Test 2: Empty text should return error
            response = client.post('/tts', json={
                'text': '',
                'language': 'en'
            })
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data
            assert 'Text is required' in data['error']
    
    # Test 5: Session Management and Language Persistence
    
    def test_language_persistence_across_requests(self, client, test_app, mock_session_id):
        """Test that language preferences persist across multiple requests."""
        with test_app.app_context():
            # Initialize session
            with client.session_transaction() as sess:
                sess['session_id'] = mock_session_id
            
            # Set language to Hindi
            response = client.post('/set-language', json={'language': 'hi'})
            assert response.status_code == 200
            
            # Verify language persists in subsequent requests
            for _ in range(3):  # Test multiple requests
                response = client.get('/get-languages')
                assert response.status_code == 200
                data = response.get_json()
                assert data['current_language'] == 'hi'
                
                # Small delay to simulate real usage
                time.sleep(0.1)
    
    def test_session_language_switching(self, client, test_app, mock_session_id):
        """Test switching between languages within the same session."""
        with test_app.app_context():
            # Initialize session
            with client.session_transaction() as sess:
                sess['session_id'] = mock_session_id
            
            languages_to_test = ['en', 'hi', 'mr', 'en']  # Test switching back
            
            for lang in languages_to_test:
                # Set language
                response = client.post('/set-language', json={'language': lang})
                assert response.status_code == 200
                data = response.get_json()
                assert data['language'] == lang
                
                # Verify language was set
                response = client.get('/get-languages')
                assert response.status_code == 200
                data = response.get_json()
                assert data['current_language'] == lang
    
    # Test 6: Database Integration with Language and Sentiment
    
    def test_database_storage_with_language_sentiment(self, client, test_app, mock_session_id):
        """Test that articles are stored in database with correct language and sentiment data."""
        with test_app.app_context():
            # Initialize session and conversation
            with client.session_transaction() as sess:
                sess['session_id'] = mock_session_id
            
            # Create conversation session
            conv_session = ConversationSession(
                session_id=mock_session_id,
                topics='["technology"]'
            )
            db.session.add(conv_session)
            db.session.commit()
            
            # Mock news search with sentiment data
            with patch('news_service.NewsService.search_multiple_topics') as mock_search:
                mock_search.return_value = {
                    'technology': [{
                        'title': 'AI Breakthrough',
                        'url': 'https://example.com/ai',
                        'summary': 'Revolutionary AI technology announced.',
                        'sentiment': 'positive',
                        'language': 'hi'
                    }]
                }
                
                # Perform search_news which saves to database
                response = client.post('/search_news', json={'language': 'hi'})
                assert response.status_code == 200
                
                # Verify article was saved with correct language and sentiment
                article = NewsArticle.query.filter_by(session_id=mock_session_id).first()
                assert article is not None
                assert article.sentiment == 'positive'
                assert article.language == 'hi'
                assert article.summary_language == 'hi'
                assert article.title == 'AI Breakthrough'
    
    # Test 7: Performance and Concurrent Requests
    
    def test_concurrent_language_requests(self, test_app):
        """Test handling of concurrent requests with different language preferences."""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request(lang_code, client_factory):
            """Make a request with specific language."""
            try:
                client = client_factory()
                session_id = str(uuid.uuid4())
                
                with client.session_transaction() as sess:
                    sess['session_id'] = session_id
                
                # Set language
                response = client.post('/set-language', json={'language': lang_code})
                if response.status_code == 200:
                    # Verify language was set
                    response = client.get('/get-languages')
                    if response.status_code == 200:
                        data = response.get_json()
                        results.put((lang_code, data['current_language'], True))
                    else:
                        results.put((lang_code, None, False))
                else:
                    results.put((lang_code, None, False))
            except Exception as e:
                results.put((lang_code, str(e), False))
        
        with test_app.app_context():
            # Create client factory
            def client_factory():
                return test_app.test_client()
            
            # Test concurrent requests for different languages
            languages = ['en', 'hi', 'mr']
            threads = []
            
            for lang in languages:
                thread = threading.Thread(target=make_request, args=(lang, client_factory))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=10)  # 10 second timeout
            
            # Verify results
            assert results.qsize() == len(languages)
            
            while not results.empty():
                requested_lang, returned_lang, success = results.get()
                assert success, f"Request for language {requested_lang} failed"
                assert requested_lang == returned_lang, f"Language mismatch: requested {requested_lang}, got {returned_lang}"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short", "-x"])