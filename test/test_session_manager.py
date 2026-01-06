"""
Tests for Session Management Service

This module contains comprehensive tests for session-based language preference management.
"""

import pytest
from unittest.mock import patch, MagicMock
from session_manager import SessionManager
from language_service import LanguageService


class TestSessionManager:
    """Test cases for SessionManager class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_session = {}
        
    @patch('session_manager.session')
    def test_get_language_preference_with_valid_language(self, mock_session):
        """Test getting language preference when valid language is stored."""
        mock_session.get.return_value = 'hi'
        
        result = SessionManager.get_language_preference()
        
        assert result == 'hi'
        mock_session.get.assert_called_once_with(SessionManager.LANGUAGE_PREFERENCE_KEY)
    
    @patch('session_manager.session')
    def test_get_language_preference_with_invalid_language(self, mock_session):
        """Test getting language preference when invalid language is stored."""
        mock_session.get.return_value = 'invalid_lang'
        
        result = SessionManager.get_language_preference()
        
        assert result == LanguageService.get_default_language()
    
    @patch('session_manager.session')
    def test_get_language_preference_no_preference(self, mock_session):
        """Test getting language preference when no preference is stored."""
        mock_session.get.return_value = None
        
        result = SessionManager.get_language_preference()
        
        assert result == LanguageService.get_default_language()
    
    @patch('session_manager.session')
    def test_set_language_preference_valid_language(self, mock_session):
        """Test setting valid language preference."""
        mock_session.__setitem__ = MagicMock()
        
        result = SessionManager.set_language_preference('hi')
        
        assert result is True
        mock_session.__setitem__.assert_called_with(SessionManager.LANGUAGE_PREFERENCE_KEY, 'hi')
    
    @patch('session_manager.session')
    def test_set_language_preference_invalid_language(self, mock_session):
        """Test setting invalid language preference."""
        result = SessionManager.set_language_preference('invalid_lang')
        
        assert result is False
    
    @patch('session_manager.session')
    def test_set_language_preference_empty_string(self, mock_session):
        """Test setting empty string as language preference."""
        result = SessionManager.set_language_preference('')
        
        assert result is False
    
    @patch('session_manager.session')
    def test_set_language_preference_none(self, mock_session):
        """Test setting None as language preference."""
        result = SessionManager.set_language_preference(None)
        
        assert result is False
    
    @patch('session_manager.session')
    def test_clear_language_preference(self, mock_session):
        """Test clearing language preference."""
        mock_session.__contains__ = MagicMock(return_value=True)
        mock_session.__delitem__ = MagicMock()
        
        SessionManager.clear_language_preference()
        
        mock_session.__delitem__.assert_called_once_with(SessionManager.LANGUAGE_PREFERENCE_KEY)
    
    @patch('session_manager.session')
    def test_clear_language_preference_not_exists(self, mock_session):
        """Test clearing language preference when it doesn't exist."""
        mock_session.__contains__ = MagicMock(return_value=False)
        mock_session.__delitem__ = MagicMock()
        
        SessionManager.clear_language_preference()
        
        mock_session.__delitem__.assert_not_called()
    
    @patch('session_manager.session')
    def test_has_language_preference_true(self, mock_session):
        """Test checking language preference when valid preference exists."""
        mock_session.get.return_value = 'en'
        
        result = SessionManager.has_language_preference()
        
        assert result is True
    
    @patch('session_manager.session')
    def test_has_language_preference_false_invalid(self, mock_session):
        """Test checking language preference when invalid preference exists."""
        mock_session.get.return_value = 'invalid_lang'
        
        result = SessionManager.has_language_preference()
        
        assert result is False
    
    @patch('session_manager.session')
    def test_has_language_preference_false_none(self, mock_session):
        """Test checking language preference when no preference exists."""
        mock_session.get.return_value = None
        
        result = SessionManager.has_language_preference()
        
        assert result is False
    
    @patch('session_manager.session')
    def test_get_session_id(self, mock_session):
        """Test getting session ID."""
        expected_id = 'test-session-id'
        mock_session.get.return_value = expected_id
        
        result = SessionManager.get_session_id()
        
        assert result == expected_id
        mock_session.get.assert_called_once_with(SessionManager.SESSION_ID_KEY)
    
    @patch('session_manager.session')
    def test_set_session_id(self, mock_session):
        """Test setting session ID."""
        session_id = 'test-session-id'
        mock_session.__setitem__ = MagicMock()
        
        SessionManager.set_session_id(session_id)
        
        mock_session.__setitem__.assert_any_call(SessionManager.SESSION_ID_KEY, session_id)
    
    @patch('session_manager.session')
    def test_get_sentiment_display_preference_default(self, mock_session):
        """Test getting sentiment display preference with default value."""
        mock_session.get.return_value = True
        
        result = SessionManager.get_sentiment_display_preference()
        
        assert result is True
    
    @patch('session_manager.session')
    def test_get_sentiment_display_preference_false(self, mock_session):
        """Test getting sentiment display preference when set to False."""
        mock_session.get.return_value = False
        
        result = SessionManager.get_sentiment_display_preference()
        
        assert result is False
    
    @patch('session_manager.session')
    def test_set_sentiment_display_preference(self, mock_session):
        """Test setting sentiment display preference."""
        mock_session.__setitem__ = MagicMock()
        
        SessionManager.set_sentiment_display_preference(False)
        
        mock_session.__setitem__.assert_any_call(SessionManager.SENTIMENT_DISPLAY_KEY, False)
    
    @patch('session_manager.session')
    def test_get_session_info(self, mock_session):
        """Test getting comprehensive session information."""
        mock_session.get.side_effect = lambda key, default=None: {
            SessionManager.SESSION_ID_KEY: 'test-session-id',
            SessionManager.LANGUAGE_PREFERENCE_KEY: 'hi',
            SessionManager.SENTIMENT_DISPLAY_KEY: True
        }.get(key, default)
        
        result = SessionManager.get_session_info()
        
        assert result['session_id'] == 'test-session-id'
        assert result['language_preference'] == 'hi'
        assert result['has_language_preference'] is True
        assert result['sentiment_display'] is True
        assert 'supported_languages' in result
    
    @patch('session_manager.session')
    def test_clear_session(self, mock_session):
        """Test clearing entire session."""
        mock_session.clear = MagicMock()
        
        SessionManager.clear_session()
        
        mock_session.clear.assert_called_once()
    
    @patch('session_manager.session')
    def test_initialize_session_defaults_no_existing_preferences(self, mock_session):
        """Test initializing session defaults when no preferences exist."""
        mock_session.get.return_value = None
        mock_session.__contains__ = MagicMock(return_value=False)
        mock_session.__setitem__ = MagicMock()
        
        SessionManager.initialize_session_defaults()
        
        # Should set default language and sentiment display
        mock_session.__setitem__.assert_any_call(SessionManager.LANGUAGE_PREFERENCE_KEY, 'en')
        mock_session.__setitem__.assert_any_call(SessionManager.SENTIMENT_DISPLAY_KEY, True)
    
    @patch('session_manager.session')
    def test_initialize_session_defaults_existing_preferences(self, mock_session):
        """Test initializing session defaults when preferences already exist."""
        mock_session.get.return_value = 'hi'  # Existing language preference
        mock_session.__contains__ = MagicMock(return_value=True)  # Sentiment preference exists
        mock_session.__setitem__ = MagicMock()
        
        SessionManager.initialize_session_defaults()
        
        # Should not override existing preferences
        mock_session.__setitem__.assert_not_called()
    
    @patch('session_manager.session')
    @patch('session_manager.logger')
    def test_error_handling_in_get_language_preference(self, mock_logger, mock_session):
        """Test error handling in get_language_preference method."""
        mock_session.get.side_effect = Exception("Session error")
        
        result = SessionManager.get_language_preference()
        
        assert result == LanguageService.get_default_language()
        mock_logger.error.assert_called_once()
    
    @patch('session_manager.session')
    @patch('session_manager.logger')
    def test_error_handling_in_set_language_preference(self, mock_logger, mock_session):
        """Test error handling in set_language_preference method."""
        mock_session.__setitem__.side_effect = Exception("Session error")
        
        result = SessionManager.set_language_preference('en')
        
        assert result is False
        mock_logger.error.assert_called_once()


class TestConvenienceFunctions:
    """Test cases for convenience functions."""
    
    @patch('session_manager.SessionManager.get_language_preference')
    def test_get_user_language(self, mock_get_lang):
        """Test get_user_language convenience function."""
        from session_manager import get_user_language
        
        mock_get_lang.return_value = 'hi'
        
        result = get_user_language()
        
        assert result == 'hi'
        mock_get_lang.assert_called_once()
    
    @patch('session_manager.SessionManager.set_language_preference')
    def test_set_user_language(self, mock_set_lang):
        """Test set_user_language convenience function."""
        from session_manager import set_user_language
        
        mock_set_lang.return_value = True
        
        result = set_user_language('mr')
        
        assert result is True
        mock_set_lang.assert_called_once_with('mr')
    
    @patch('session_manager.SessionManager.get_session_info')
    def test_get_session_info_convenience(self, mock_get_info):
        """Test get_session_info convenience function."""
        from session_manager import get_session_info
        
        expected_info = {'session_id': 'test', 'language_preference': 'en'}
        mock_get_info.return_value = expected_info
        
        result = get_session_info()
        
        assert result == expected_info
        mock_get_info.assert_called_once()
    
    @patch('session_manager.SessionManager.initialize_session_defaults')
    def test_initialize_session_convenience(self, mock_init):
        """Test initialize_session convenience function."""
        from session_manager import initialize_session
        
        initialize_session()
        
        mock_init.assert_called_once()


class TestSessionManagerIntegration:
    """Integration tests for SessionManager with LanguageService."""
    
    def test_language_validation_integration(self):
        """Test that SessionManager properly integrates with LanguageService validation."""
        # Test with valid languages
        assert SessionManager.set_language_preference('en') is True
        assert SessionManager.set_language_preference('hi') is True
        assert SessionManager.set_language_preference('mr') is True
        
        # Test with invalid languages
        assert SessionManager.set_language_preference('fr') is False
        assert SessionManager.set_language_preference('de') is False
        assert SessionManager.set_language_preference('xyz') is False
    
    def test_case_insensitive_language_handling(self):
        """Test that language codes are handled case-insensitively."""
        assert SessionManager.set_language_preference('EN') is True
        assert SessionManager.set_language_preference('Hi') is True
        assert SessionManager.set_language_preference('MR') is True
    
    def test_language_normalization(self):
        """Test that language codes are properly normalized."""
        # This test would need to be run with actual Flask session context
        # For now, we test the validation logic
        from language_service import LanguageService
        
        assert LanguageService.normalize_language_code('EN') == 'en'
        assert LanguageService.normalize_language_code('Hi') == 'hi'
        assert LanguageService.normalize_language_code('MR') == 'mr'


if __name__ == '__main__':
    pytest.main([__file__])