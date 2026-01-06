"""
Unit tests for multi-language TTS service functionality.

Tests the enhanced TTS service with language support, validation,
and fallback mechanisms.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
from tts_service import TTSService
from language_service import LanguageService


class TestMultiLanguageTTS(unittest.TestCase):
    """Test cases for multi-language TTS functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tts_service = TTSService()
        self.test_text = "This is a test message for TTS generation."
        self.test_text_hindi = "यह टीटीएस जेनरेशन के लिए एक परीक्षण संदेश है।"
        self.test_text_marathi = "हा TTS निर्मितीसाठी एक चाचणी संदेश आहे."
    
    def test_initialization_with_default_language(self):
        """Test TTS service initialization with default language."""
        tts = TTSService()
        self.assertEqual(tts.default_language, 'en')
        self.assertFalse(tts.slow)
    
    def test_initialization_with_custom_language(self):
        """Test TTS service initialization with custom language."""
        tts = TTSService(language='hi', slow=True)
        self.assertEqual(tts.default_language, 'hi')
        self.assertTrue(tts.slow)
    
    def test_initialization_with_invalid_language(self):
        """Test TTS service initialization with invalid language falls back to default."""
        tts = TTSService(language='invalid')
        self.assertEqual(tts.default_language, 'en')
    
    def test_set_language_valid(self):
        """Test setting a valid language."""
        self.tts_service.set_language('hi')
        self.assertEqual(self.tts_service.default_language, 'hi')
        
        self.tts_service.set_language('mr')
        self.assertEqual(self.tts_service.default_language, 'mr')
    
    def test_set_language_invalid(self):
        """Test setting an invalid language falls back to default."""
        original_lang = self.tts_service.default_language
        self.tts_service.set_language('invalid')
        self.assertEqual(self.tts_service.default_language, 'en')
    
    def test_get_supported_languages(self):
        """Test getting supported languages."""
        languages = self.tts_service.get_supported_languages()
        self.assertIsInstance(languages, dict)
        self.assertIn('en', languages)
        self.assertIn('hi', languages)
        self.assertIn('mr', languages)
        
        # Check language metadata
        self.assertEqual(languages['en']['name'], 'English')
        self.assertEqual(languages['hi']['name'], 'Hindi')
        self.assertEqual(languages['mr']['name'], 'Marathi')
    
    def test_get_target_language_with_parameter(self):
        """Test getting target language when parameter is provided."""
        target = self.tts_service._get_target_language('hi')
        self.assertEqual(target, 'hi')
        
        target = self.tts_service._get_target_language('mr')
        self.assertEqual(target, 'mr')
    
    def test_get_target_language_without_parameter(self):
        """Test getting target language when no parameter is provided."""
        self.tts_service.set_language('hi')
        target = self.tts_service._get_target_language()
        self.assertEqual(target, 'hi')
    
    def test_get_target_language_invalid(self):
        """Test getting target language with invalid parameter falls back to default."""
        target = self.tts_service._get_target_language('invalid')
        self.assertEqual(target, 'en')
    
    def test_get_tts_language_code(self):
        """Test getting TTS language codes."""
        self.assertEqual(self.tts_service._get_tts_language_code('en'), 'en')
        self.assertEqual(self.tts_service._get_tts_language_code('hi'), 'hi')
        self.assertEqual(self.tts_service._get_tts_language_code('mr'), 'mr')
    
    def test_get_tts_language_code_invalid(self):
        """Test getting TTS language code for invalid language."""
        code = self.tts_service._get_tts_language_code('invalid')
        self.assertEqual(code, 'en')  # Should fallback to default
    
    @patch('tts_service.gTTS')
    @patch('os.makedirs')
    def test_text_to_speech_english(self, mock_makedirs, mock_gtts):
        """Test TTS generation in English."""
        mock_tts_instance = Mock()
        mock_gtts.return_value = mock_tts_instance
        
        result = self.tts_service.text_to_speech(self.test_text, 'en')
        
        self.assertIsNotNone(result)
        self.assertTrue(result.startswith('/static/audio/'))
        self.assertTrue(result.endswith('.mp3'))
        mock_gtts.assert_called_once()
        mock_tts_instance.save.assert_called_once()
    
    @patch('tts_service.gTTS')
    @patch('os.makedirs')
    def test_text_to_speech_hindi(self, mock_makedirs, mock_gtts):
        """Test TTS generation in Hindi."""
        mock_tts_instance = Mock()
        mock_gtts.return_value = mock_tts_instance
        
        result = self.tts_service.text_to_speech(self.test_text_hindi, 'hi')
        
        self.assertIsNotNone(result)
        self.assertTrue('tts_hi_' in result)
        mock_gtts.assert_called_once()
        mock_tts_instance.save.assert_called_once()
    
    @patch('tts_service.gTTS')
    @patch('os.makedirs')
    def test_text_to_speech_marathi(self, mock_makedirs, mock_gtts):
        """Test TTS generation in Marathi."""
        mock_tts_instance = Mock()
        mock_gtts.return_value = mock_tts_instance
        
        result = self.tts_service.text_to_speech(self.test_text_marathi, 'mr')
        
        self.assertIsNotNone(result)
        self.assertTrue('tts_mr_' in result)
        mock_gtts.assert_called_once()
        mock_tts_instance.save.assert_called_once()
    
    @patch('tts_service.gTTS')
    @patch('os.makedirs')
    def test_text_to_speech_fallback_language(self, mock_makedirs, mock_gtts):
        """Test TTS generation with fallback to default language."""
        mock_tts_instance = Mock()
        mock_gtts.return_value = mock_tts_instance
        
        # Test with invalid language should fallback to English
        result = self.tts_service.text_to_speech(self.test_text, 'invalid')
        
        self.assertIsNotNone(result)
        self.assertTrue('tts_en_' in result)
        mock_gtts.assert_called_once()
    
    def test_text_to_speech_empty_text(self):
        """Test TTS generation with empty text."""
        result = self.tts_service.text_to_speech("")
        self.assertIsNone(result)
        
        result = self.tts_service.text_to_speech("   ")
        self.assertIsNone(result)
        
        result = self.tts_service.text_to_speech(None)
        self.assertIsNone(result)
    
    @patch('tts_service.gTTS')
    @patch('os.makedirs')
    def test_text_to_speech_long_text_truncation(self, mock_makedirs, mock_gtts):
        """Test TTS generation with long text gets truncated."""
        mock_tts_instance = Mock()
        mock_gtts.return_value = mock_tts_instance
        
        long_text = "A" * 6000  # Longer than 5000 character limit
        result = self.tts_service.text_to_speech(long_text, 'en')
        
        self.assertIsNotNone(result)
        # Check that gTTS was called with truncated text
        call_args = mock_gtts.call_args[1]
        self.assertLess(len(call_args['text']), 5100)  # Should be truncated + message
        self.assertIn("Text truncated", call_args['text'])
    
    @patch('tts_service.gTTS')
    @patch('os.makedirs')
    def test_generate_tts_with_fallback_success(self, mock_makedirs, mock_gtts):
        """Test successful TTS generation without fallback."""
        mock_tts_instance = Mock()
        mock_gtts.return_value = mock_tts_instance
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = self.tts_service._generate_tts_with_fallback(
                self.test_text, 'hi', temp_path
            )
            self.assertTrue(result)
            mock_gtts.assert_called_once_with(text=self.test_text, lang='hi', slow=False)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('tts_service.gTTS')
    @patch('os.makedirs')
    def test_generate_tts_with_fallback_failure_and_recovery(self, mock_makedirs, mock_gtts):
        """Test TTS generation with fallback when primary language fails."""
        # First call fails, second call (fallback) succeeds
        mock_tts_instance_success = Mock()
        mock_gtts.side_effect = [Exception("Primary language failed"), mock_tts_instance_success]
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = self.tts_service._generate_tts_with_fallback(
                self.test_text, 'hi', temp_path
            )
            self.assertTrue(result)
            self.assertEqual(mock_gtts.call_count, 2)  # Primary + fallback
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('tts_service.gTTS')
    @patch('os.makedirs')
    def test_generate_tts_with_fallback_complete_failure(self, mock_makedirs, mock_gtts):
        """Test TTS generation when both primary and fallback fail."""
        mock_gtts.side_effect = Exception("TTS service unavailable")
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = self.tts_service._generate_tts_with_fallback(
                self.test_text, 'hi', temp_path
            )
            self.assertFalse(result)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('tts_service.TTSService.text_to_speech')
    def test_get_audio_url_with_language(self, mock_text_to_speech):
        """Test getting audio URL with language parameter."""
        mock_text_to_speech.return_value = "/static/audio/test.mp3"
        
        result = self.tts_service.get_audio_url(self.test_text, 'hi')
        
        self.assertEqual(result, "/static/audio/test.mp3")
        mock_text_to_speech.assert_called_once_with(self.test_text, 'hi')
    
    @patch('tts_service.TTSService.text_to_speech')
    def test_get_audio_url_without_language(self, mock_text_to_speech):
        """Test getting audio URL without language parameter."""
        mock_text_to_speech.return_value = "/static/audio/test.mp3"
        
        result = self.tts_service.get_audio_url(self.test_text)
        
        self.assertEqual(result, "/static/audio/test.mp3")
        mock_text_to_speech.assert_called_once_with(self.test_text, None)
    
    def test_clean_text_for_tts_markdown_removal(self):
        """Test text cleaning removes markdown formatting."""
        markdown_text = "This is **bold** and *italic* text with _underscores_."
        cleaned = self.tts_service._clean_text_for_tts(markdown_text)
        self.assertNotIn('**', cleaned)
        self.assertNotIn('*', cleaned)
        self.assertNotIn('_', cleaned)
    
    def test_clean_text_for_tts_url_removal(self):
        """Test text cleaning removes URLs."""
        text_with_url = "Check this link: https://example.com for more info."
        cleaned = self.tts_service._clean_text_for_tts(text_with_url)
        self.assertNotIn('https://example.com', cleaned)
    
    def test_clean_text_for_tts_whitespace_normalization(self):
        """Test text cleaning normalizes whitespace."""
        messy_text = "This   has    multiple\n\nspaces   and\tlines."
        cleaned = self.tts_service._clean_text_for_tts(messy_text)
        self.assertNotIn('   ', cleaned)
        self.assertNotIn('\n\n', cleaned)
        self.assertNotIn('\t', cleaned)


if __name__ == '__main__':
    unittest.main()