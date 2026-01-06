"""
Integration Tests for Session Management Routes

This module contains tests for Flask routes that handle session-based language preferences.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from app import app, db
from session_manager import SessionManager


class TestSessionRoutes:
    """Test cases for session management routes."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                yield client
                db.drop_all()
    
    def test_index_route_initializes_session(self, client):
        """Test that index route properly initializes session."""
        response = client.get('/')
        
        assert response.status_code == 200
        
        # Check that session was initialized
        with client.session_transaction() as sess:
            assert 'session_id' in sess
            # Session defaults should be initialized
    
    def test_set_language_route_valid_language(self, client):
        """Test setting valid language preference via API."""
        response = client.post('/set-language',
                             data=json.dumps({'language': 'hi'}),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['language'] == 'hi'
        
        # Verify language was stored in session
        with client.session_transaction() as sess:
            assert sess.get('preferred_language') == 'hi'
    
    def test_set_language_route_invalid_language(self, client):
        """Test setting invalid language preference via API."""
        response = client.post('/set-language',
                             data=json.dumps({'language': 'invalid'}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Unsupported language' in data['error']
    
    def test_set_language_route_missing_language(self, client):
        """Test setting language preference without providing language."""
        response = client.post('/set-language',
                             data=json.dumps({}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Language is required' in data['error']
    
    def test_set_language_route_case_insensitive(self, client):
        """Test that language setting is case insensitive."""
        response = client.post('/set-language',
                             data=json.dumps({'language': 'HI'}),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['language'] == 'hi'  # Should be normalized to lowercase
    
    def test_get_languages_route(self, client):
        """Test getting supported languages via API."""
        response = client.get('/get-languages')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'languages' in data
        assert 'current_language' in data
        
        # Check that supported languages are returned
        languages = data['languages']
        assert 'en' in languages
        assert 'hi' in languages
        assert 'mr' in languages
    
    def test_get_languages_route_with_preference(self, client):
        """Test getting languages when user has set preference."""
        # First set a language preference
        client.post('/set-language',
                   data=json.dumps({'language': 'mr'}),
                   content_type='application/json')
        
        # Then get languages
        response = client.get('/get-languages')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['current_language'] == 'mr'
    
    def test_session_info_route(self, client):
        """Test getting session information via API."""
        # First set some preferences
        client.post('/set-language',
                   data=json.dumps({'language': 'hi'}),
                   content_type='application/json')
        
        response = client.get('/session-info')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'session_info' in data
        
        session_info = data['session_info']
        assert session_info['language_preference'] == 'hi'
        assert session_info['has_language_preference'] is True
        assert 'session_id' in session_info
        assert 'supported_languages' in session_info
    
    def test_search_news_uses_session_language(self, client):
        """Test that search_news route uses session language preference."""
        # Set language preference
        client.post('/set-language',
                   data=json.dumps({'language': 'hi'}),
                   content_type='application/json')
        
        # Mock the news service to avoid actual API calls
        with patch('routes.news_service') as mock_news_service:
            mock_news_service.search_multiple_topics.return_value = {
                'test_topic': [{'title': 'Test Article', 'url': 'http://test.com', 'summary': 'Test summary'}]
            }
            
            # Create a conversation session first
            with client.session_transaction() as sess:
                sess['session_id'] = 'test-session'
            
            # Mock conversation session
            with patch('routes.ConversationSession') as mock_conv_session:
                mock_session = MagicMock()
                mock_session.get_topics.return_value = ['test_topic']
                mock_conv_session.query.filter_by.return_value.first.return_value = mock_session
                
                response = client.post('/search_news',
                                     data=json.dumps({}),
                                     content_type='application/json')
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['language'] == 'hi'
                
                # Verify news service was called with Hindi language
                mock_news_service.search_multiple_topics.assert_called_once()
                call_args = mock_news_service.search_multiple_topics.call_args
                assert call_args[1]['language'] == 'hi'
    
    def test_tts_route_uses_session_language(self, client):
        """Test that TTS route uses session language preference."""
        # Set language preference
        client.post('/set-language',
                   data=json.dumps({'language': 'mr'}),
                   content_type='application/json')
        
        # Mock the TTS service
        with patch('routes.tts_service') as mock_tts_service:
            mock_tts_service.text_to_speech.return_value = 'test_audio.mp3'
            
            response = client.post('/tts',
                                 data=json.dumps({'text': 'Test text'}),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['language'] == 'mr'
            
            # Verify TTS service was called with Marathi language
            mock_tts_service.text_to_speech.assert_called_once_with('Test text', 'mr')
    
    def test_tts_route_language_override(self, client):
        """Test that TTS route can override session language."""
        # Set session language to Hindi
        client.post('/set-language',
                   data=json.dumps({'language': 'hi'}),
                   content_type='application/json')
        
        # Mock the TTS service
        with patch('routes.tts_service') as mock_tts_service:
            mock_tts_service.text_to_speech.return_value = 'test_audio.mp3'
            
            # Request TTS in English (override session language)
            response = client.post('/tts',
                                 data=json.dumps({'text': 'Test text', 'language': 'en'}),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['language'] == 'en'
            
            # Verify TTS service was called with English, not Hindi
            mock_tts_service.text_to_speech.assert_called_once_with('Test text', 'en')
    
    def test_session_persistence_across_requests(self, client):
        """Test that session preferences persist across multiple requests."""
        # Set language preference
        response1 = client.post('/set-language',
                              data=json.dumps({'language': 'hi'}),
                              content_type='application/json')
        assert response1.status_code == 200
        
        # Make another request and check language is still set
        response2 = client.get('/get-languages')
        assert response2.status_code == 200
        data = json.loads(response2.data)
        assert data['current_language'] == 'hi'
        
        # Make a third request to verify persistence
        response3 = client.get('/session-info')
        assert response3.status_code == 200
        data = json.loads(response3.data)
        assert data['session_info']['language_preference'] == 'hi'
    
    def test_multiple_language_changes(self, client):
        """Test changing language preference multiple times."""
        # Set to Hindi
        response1 = client.post('/set-language',
                              data=json.dumps({'language': 'hi'}),
                              content_type='application/json')
        assert response1.status_code == 200
        
        # Change to Marathi
        response2 = client.post('/set-language',
                              data=json.dumps({'language': 'mr'}),
                              content_type='application/json')
        assert response2.status_code == 200
        
        # Change to English
        response3 = client.post('/set-language',
                              data=json.dumps({'language': 'en'}),
                              content_type='application/json')
        assert response3.status_code == 200
        
        # Verify final language is English
        response4 = client.get('/get-languages')
        data = json.loads(response4.data)
        assert data['current_language'] == 'en'
    
    def test_default_language_behavior(self, client):
        """Test default language behavior when no preference is set."""
        # Access index to initialize session but don't set language
        client.get('/')
        
        # Check that default language is returned
        response = client.get('/get-languages')
        data = json.loads(response.data)
        assert data['current_language'] == 'en'  # Default should be English
        
        # Check session info
        response = client.get('/session-info')
        data = json.loads(response.data)
        assert data['session_info']['language_preference'] == 'en'


class TestSessionErrorHandling:
    """Test error handling in session management routes."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                yield client
                db.drop_all()
    
    def test_set_language_malformed_json(self, client):
        """Test setting language with malformed JSON."""
        response = client.post('/set-language',
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400
    
    def test_set_language_no_content_type(self, client):
        """Test setting language without proper content type."""
        response = client.post('/set-language',
                             data=json.dumps({'language': 'hi'}))
        
        # Should still work as Flask can handle it
        assert response.status_code in [200, 400]  # Depends on Flask version
    
    @patch('routes.SessionManager.set_language_preference')
    def test_set_language_session_error(self, mock_set_lang, client):
        """Test handling of session errors in set_language route."""
        mock_set_lang.side_effect = Exception("Session error")
        
        response = client.post('/set-language',
                             data=json.dumps({'language': 'hi'}),
                             content_type='application/json')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('routes.SessionManager.get_session_info')
    def test_session_info_error(self, mock_get_info, client):
        """Test handling of errors in session-info route."""
        mock_get_info.side_effect = Exception("Session error")
        
        response = client.get('/session-info')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data


if __name__ == '__main__':
    pytest.main([__file__])