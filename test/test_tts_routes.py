"""
Integration tests for TTS API endpoints with language support.

Tests the enhanced TTS routes with language parameters, session management,
and error handling for unsupported languages.
"""

import unittest
from unittest.mock import Mock, patch
import json
from app import app, db
from models import ConversationSession
import uuid


class TestTTSRoutes(unittest.TestCase):
    """Test cases for TTS API endpoints with language support."""
    
    def setUp(self):
        """Set up test fixtures."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create tables
        db.create_all()
        
        # Test data
        self.test_text = "This is a test message for TTS generation."
        self.test_text_hindi = "यह टीटीएस जेनरेशन के लिए एक परीक्षण संदेश है।"
        self.test_text_marathi = "हा TTS निर्मितीसाठी एक चाचणी संदेश आहे."
    
    def tearDown(self):
        """Clean up test fixtures."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def _create_session(self):
        """Helper method to create a test session."""
        with self.client.session_transaction() as sess:
            sess['session_id'] = str(uuid.uuid4())
            return sess['session_id']
    
    @patch('routes.tts_service.text_to_speech')
    def test_tts_endpoint_default_language(self, mock_tts):
        """Test TTS endpoint with default language (English)."""
        mock_tts.return_value = "/static/audio/test.mp3"
        
        response = self.client.post('/tts', 
                                  json={'text': self.test_text},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['audio_url'], "/static/audio/test.mp3")
        self.assertEqual(data['language'], 'en')
        mock_tts.assert_called_once_with(self.test_text, 'en')
    
    @patch('routes.tts_service.text_to_speech')
    def test_tts_endpoint_with_language_parameter(self, mock_tts):
        """Test TTS endpoint with explicit language parameter."""
        mock_tts.return_value = "/static/audio/test_hi.mp3"
        
        response = self.client.post('/tts', 
                                  json={'text': self.test_text_hindi, 'language': 'hi'},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['audio_url'], "/static/audio/test_hi.mp3")
        self.assertEqual(data['language'], 'hi')
        mock_tts.assert_called_once_with(self.test_text_hindi, 'hi')
    
    @patch('routes.tts_service.text_to_speech')
    def test_tts_endpoint_with_session_language(self, mock_tts):
        """Test TTS endpoint using session language preference."""
        mock_tts.return_value = "/static/audio/test_mr.mp3"
        
        # Set language preference in session
        with self.client.session_transaction() as sess:
            sess['preferred_language'] = 'mr'
        
        response = self.client.post('/tts', 
                                  json={'text': self.test_text_marathi},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['language'], 'mr')
        mock_tts.assert_called_once_with(self.test_text_marathi, 'mr')
    
    @patch('routes.tts_service.text_to_speech')
    def test_tts_endpoint_invalid_language_fallback(self, mock_tts):
        """Test TTS endpoint with invalid language falls back to English."""
        mock_tts.return_value = "/static/audio/test_fallback.mp3"
        
        response = self.client.post('/tts', 
                                  json={'text': self.test_text, 'language': 'invalid'},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['language'], 'en')  # Should fallback to English
        mock_tts.assert_called_once_with(self.test_text, 'en')
    
    def test_tts_endpoint_empty_text(self):
        """Test TTS endpoint with empty text returns error."""
        response = self.client.post('/tts', 
                                  json={'text': ''},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Text is required')
    
    def test_tts_endpoint_no_text(self):
        """Test TTS endpoint without text parameter returns error."""
        response = self.client.post('/tts', 
                                  json={},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Text is required')
    
    @patch('routes.tts_service.text_to_speech')
    def test_tts_endpoint_service_failure(self, mock_tts):
        """Test TTS endpoint when service fails to generate audio."""
        mock_tts.return_value = None  # Simulate service failure
        
        response = self.client.post('/tts', 
                                  json={'text': self.test_text, 'language': 'hi'},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('Failed to generate audio in hi', data['error'])
    
    @patch('routes.tts_service.text_to_speech')
    def test_tts_endpoint_service_failure_english(self, mock_tts):
        """Test TTS endpoint when service fails for English."""
        mock_tts.return_value = None  # Simulate service failure
        
        response = self.client.post('/tts', 
                                  json={'text': self.test_text, 'language': 'en'},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Failed to generate audio in en')
    
    def test_set_language_endpoint_valid(self):
        """Test setting valid language preference."""
        response = self.client.post('/set-language', 
                                  json={'language': 'hi'},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['language'], 'hi')
        self.assertIn('Hindi', data['message'])
    
    def test_set_language_endpoint_invalid(self):
        """Test setting invalid language preference."""
        response = self.client.post('/set-language', 
                                  json={'language': 'invalid'},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Unsupported language', data['error'])
    
    def test_set_language_endpoint_empty(self):
        """Test setting empty language preference."""
        response = self.client.post('/set-language', 
                                  json={},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Language is required')
    
    def test_get_languages_endpoint(self):
        """Test getting supported languages."""
        response = self.client.get('/get-languages')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('languages', data)
        self.assertIn('current_language', data)
        
        # Check that all expected languages are present
        languages = data['languages']
        self.assertIn('en', languages)
        self.assertIn('hi', languages)
        self.assertIn('mr', languages)
        
        # Check language metadata
        self.assertEqual(languages['en']['name'], 'English')
        self.assertEqual(languages['hi']['name'], 'Hindi')
        self.assertEqual(languages['mr']['name'], 'Marathi')
    
    def test_get_languages_with_session_preference(self):
        """Test getting languages with session preference set."""
        # Set language preference in session
        with self.client.session_transaction() as sess:
            sess['preferred_language'] = 'hi'
        
        response = self.client.get('/get-languages')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['current_language'], 'hi')
    
    def test_language_preference_persistence(self):
        """Test that language preference persists across requests."""
        # Set language preference
        response1 = self.client.post('/set-language', 
                                   json={'language': 'mr'},
                                   content_type='application/json')
        self.assertEqual(response1.status_code, 200)
        
        # Check that preference is maintained
        response2 = self.client.get('/get-languages')
        self.assertEqual(response2.status_code, 200)
        data = json.loads(response2.data)
        self.assertEqual(data['current_language'], 'mr')
    
    @patch('routes.tts_service.text_to_speech')
    def test_language_preference_used_in_tts(self, mock_tts):
        """Test that session language preference is used in TTS calls."""
        mock_tts.return_value = "/static/audio/test.mp3"
        
        # Set language preference
        self.client.post('/set-language', 
                        json={'language': 'hi'},
                        content_type='application/json')
        
        # Make TTS request without explicit language
        response = self.client.post('/tts', 
                                  json={'text': self.test_text},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['language'], 'hi')
        mock_tts.assert_called_once_with(self.test_text, 'hi')
    
    @patch('routes.tts_service.text_to_speech')
    def test_explicit_language_overrides_session(self, mock_tts):
        """Test that explicit language parameter overrides session preference."""
        mock_tts.return_value = "/static/audio/test.mp3"
        
        # Set session language to Hindi
        with self.client.session_transaction() as sess:
            sess['preferred_language'] = 'hi'
        
        # Make TTS request with explicit Marathi language
        response = self.client.post('/tts', 
                                  json={'text': self.test_text, 'language': 'mr'},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['language'], 'mr')  # Should use explicit language
        mock_tts.assert_called_once_with(self.test_text, 'mr')


if __name__ == '__main__':
    unittest.main()