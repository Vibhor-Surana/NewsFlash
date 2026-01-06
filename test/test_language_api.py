import pytest
import json
from unittest.mock import patch, MagicMock
from app import app, db
from models import ConversationSession
import uuid

class TestLanguageAPI:
    """Test cases for language preference API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                yield client
                db.drop_all()
    
    @pytest.fixture
    def mock_session(self, client):
        """Create a mock session"""
        with client.session_transaction() as sess:
            sess['session_id'] = str(uuid.uuid4())
        return sess['session_id']
    
    # Tests for /set-language endpoint
    
    def test_set_language_endpoint_exists(self, client):
        """Test that the /set-language endpoint exists and accepts POST requests"""
        response = client.post('/set-language', json={'language': 'en'})
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_set_language_requires_json_body(self, client):
        """Test that set-language endpoint requires JSON body"""
        response = client.post('/set-language')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Request body is required' in data['error']
    
    def test_set_language_requires_language_parameter(self, client):
        """Test that set-language endpoint requires language parameter"""
        response = client.post('/set-language', json={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Language is required' in data['error']
    
    def test_set_language_rejects_empty_language(self, client):
        """Test that set-language endpoint rejects empty language"""
        response = client.post('/set-language', json={'language': '   '})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Language is required' in data['error']
    
    @patch('routes.SessionManager.set_language_preference')
    @patch('routes.SessionManager.get_session_id')
    def test_set_language_with_valid_language(self, mock_get_session, mock_set_lang, client, mock_session):
        """Test set-language with valid language"""
        mock_set_lang.return_value = True
        mock_get_session.return_value = mock_session
        
        response = client.post('/set-language', json={'language': 'hi'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['language'] == 'hi'
        assert 'message' in data
        
        # Verify SessionManager was called
        mock_set_lang.assert_called_once_with('hi')
    
    @patch('routes.SessionManager.set_language_preference')
    def test_set_language_with_invalid_language(self, mock_set_lang, client, mock_session):
        """Test set-language with invalid language"""
        mock_set_lang.return_value = False
        
        response = client.post('/set-language', json={'language': 'invalid'})
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data
        assert 'Unsupported language' in data['error']
    
    @patch('routes.SessionManager.set_language_preference')
    def test_set_language_handles_session_manager_error(self, mock_set_lang, client, mock_session):
        """Test set-language handles SessionManager errors gracefully"""
        mock_set_lang.side_effect = Exception("Session manager error")
        
        response = client.post('/set-language', json={'language': 'en'})
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'An error occurred while setting language preference' in data['error']
    
    def test_set_language_method_not_allowed(self, client):
        """Test that GET method is not allowed on /set-language endpoint"""
        response = client.get('/set-language')
        assert response.status_code == 405  # Method Not Allowed
    
    # Tests for /get-languages endpoint
    
    def test_get_languages_endpoint_exists(self, client):
        """Test that the /get-languages endpoint exists and accepts GET requests"""
        response = client.get('/get-languages')
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    @patch('language_service.LanguageService.get_supported_languages')
    @patch('routes.SessionManager.get_language_preference')
    def test_get_languages_returns_supported_languages(self, mock_get_pref, mock_get_langs, client):
        """Test get-languages returns supported languages"""
        mock_languages = {
            'en': {'name': 'English', 'native': 'English'},
            'hi': {'name': 'Hindi', 'native': 'हिंदी'},
            'mr': {'name': 'Marathi', 'native': 'मराठी'}
        }
        mock_get_langs.return_value = mock_languages
        mock_get_pref.return_value = 'en'
        
        response = client.get('/get-languages')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'languages' in data
        assert 'current_language' in data
        assert data['languages'] == mock_languages
        assert data['current_language'] == 'en'
    
    @patch('language_service.LanguageService.get_supported_languages')
    @patch('routes.SessionManager.get_language_preference')
    def test_get_languages_with_different_current_language(self, mock_get_pref, mock_get_langs, client):
        """Test get-languages with different current language"""
        mock_languages = {
            'en': {'name': 'English', 'native': 'English'},
            'hi': {'name': 'Hindi', 'native': 'हिंदी'},
            'mr': {'name': 'Marathi', 'native': 'मराठी'}
        }
        mock_get_langs.return_value = mock_languages
        mock_get_pref.return_value = 'hi'
        
        response = client.get('/get-languages')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['current_language'] == 'hi'
    
    @patch('language_service.LanguageService.get_supported_languages')
    def test_get_languages_handles_language_service_error(self, mock_get_langs, client):
        """Test get-languages handles LanguageService errors gracefully"""
        mock_get_langs.side_effect = Exception("Language service error")
        
        response = client.get('/get-languages')
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'An error occurred while getting supported languages' in data['error']
    
    @patch('routes.SessionManager.get_language_preference')
    def test_get_languages_handles_session_manager_error(self, mock_get_pref, client):
        """Test get-languages handles SessionManager errors gracefully"""
        mock_get_pref.side_effect = Exception("Session manager error")
        
        response = client.get('/get-languages')
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'An error occurred while getting supported languages' in data['error']
    
    def test_get_languages_method_not_allowed(self, client):
        """Test that POST method is not allowed on /get-languages endpoint"""
        response = client.post('/get-languages')
        assert response.status_code == 405  # Method Not Allowed
    
    # Integration tests
    
    @patch('routes.SessionManager.set_language_preference')
    @patch('routes.SessionManager.get_language_preference')
    @patch('language_service.LanguageService.get_supported_languages')
    def test_language_preference_workflow(self, mock_get_langs, mock_get_pref, mock_set_pref, client, mock_session):
        """Test complete language preference workflow"""
        # Setup mocks
        mock_languages = {
            'en': {'name': 'English', 'native': 'English'},
            'hi': {'name': 'Hindi', 'native': 'हिंदी'}
        }
        mock_get_langs.return_value = mock_languages
        mock_set_pref.return_value = True
        
        # Initially English
        mock_get_pref.return_value = 'en'
        
        # Get initial languages
        response = client.get('/get-languages')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['current_language'] == 'en'
        
        # Set language to Hindi
        response = client.post('/set-language', json={'language': 'hi'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['language'] == 'hi'
        
        # Verify set_language_preference was called
        mock_set_pref.assert_called_once_with('hi')
        
        # Update mock to return Hindi
        mock_get_pref.return_value = 'hi'
        
        # Get languages again to verify change
        response = client.get('/get-languages')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['current_language'] == 'hi'
    
    # Validation tests
    
    def test_set_language_validates_input_types(self, client):
        """Test set-language validates input types"""
        # Test with non-string language
        response = client.post('/set-language', json={'language': 123})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Language must be a string' in data['error']
        
        # Test with null language
        response = client.post('/set-language', json={'language': None})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Language must be a string' in data['error']
    
    def test_set_language_trims_whitespace(self, client, mock_session):
        """Test set-language trims whitespace from language parameter"""
        with patch('routes.SessionManager.set_language_preference') as mock_set_lang:
            mock_set_lang.return_value = True
            
            response = client.post('/set-language', json={'language': '  en  '})
            assert response.status_code == 200
            
            # Verify trimmed language was passed to SessionManager
            mock_set_lang.assert_called_once_with('en')
    
    def test_language_endpoints_case_sensitivity(self, client, mock_session):
        """Test language endpoints handle case sensitivity properly"""
        with patch('routes.SessionManager.set_language_preference') as mock_set_lang:
            mock_set_lang.return_value = True
            
            # Test uppercase language code
            response = client.post('/set-language', json={'language': 'EN'})
            assert response.status_code == 200
            
            data = json.loads(response.data)
            # Should be normalized to lowercase in response
            assert data['language'] == 'en'