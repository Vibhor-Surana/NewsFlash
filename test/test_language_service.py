"""
Unit tests for the Language Service module.

Tests cover:
- Language validation
- Language code mapping
- Fallback mechanisms
- Utility functions
"""

import unittest
from language_service import (
    LanguageService,
    validate_language,
    get_supported_languages,
    get_default_language,
    normalize_language_code
)


class TestLanguageService(unittest.TestCase):
    """Test cases for LanguageService class."""
    
    def test_get_supported_languages(self):
        """Test getting supported languages returns correct structure."""
        languages = LanguageService.get_supported_languages()
        
        # Should contain all enabled languages
        self.assertIn('en', languages)
        self.assertIn('hi', languages)
        self.assertIn('mr', languages)
        
        # Each language should have required metadata
        for code, lang_data in languages.items():
            self.assertIn('name', lang_data)
            self.assertIn('native', lang_data)
            self.assertIn('tts_code', lang_data)
            self.assertIsInstance(lang_data['name'], str)
            self.assertIsInstance(lang_data['native'], str)
            self.assertIsInstance(lang_data['tts_code'], str)
    
    def test_validate_language_valid_codes(self):
        """Test validation with valid language codes."""
        # Test supported languages
        self.assertTrue(LanguageService.validate_language('en'))
        self.assertTrue(LanguageService.validate_language('hi'))
        self.assertTrue(LanguageService.validate_language('mr'))
        
        # Test case insensitivity
        self.assertTrue(LanguageService.validate_language('EN'))
        self.assertTrue(LanguageService.validate_language('Hi'))
        self.assertTrue(LanguageService.validate_language('MR'))
        
        # Test with whitespace
        self.assertTrue(LanguageService.validate_language(' en '))
        self.assertTrue(LanguageService.validate_language(' hi '))
    
    def test_validate_language_invalid_codes(self):
        """Test validation with invalid language codes."""
        # Test unsupported languages
        self.assertFalse(LanguageService.validate_language('fr'))
        self.assertFalse(LanguageService.validate_language('de'))
        self.assertFalse(LanguageService.validate_language('es'))
        
        # Test invalid inputs
        self.assertFalse(LanguageService.validate_language(''))
        self.assertFalse(LanguageService.validate_language(None))
        self.assertFalse(LanguageService.validate_language(123))
        self.assertFalse(LanguageService.validate_language([]))
        self.assertFalse(LanguageService.validate_language({}))
    
    def test_get_default_language(self):
        """Test getting default language."""
        default = LanguageService.get_default_language()
        self.assertEqual(default, 'en')
        self.assertIsInstance(default, str)
    
    def test_get_language_name(self):
        """Test getting English names of languages."""
        self.assertEqual(LanguageService.get_language_name('en'), 'English')
        self.assertEqual(LanguageService.get_language_name('hi'), 'Hindi')
        self.assertEqual(LanguageService.get_language_name('mr'), 'Marathi')
        
        # Test case insensitivity
        self.assertEqual(LanguageService.get_language_name('EN'), 'English')
        
        # Test invalid codes
        self.assertIsNone(LanguageService.get_language_name('fr'))
        self.assertIsNone(LanguageService.get_language_name(''))
        self.assertIsNone(LanguageService.get_language_name(None))
    
    def test_get_native_name(self):
        """Test getting native names of languages."""
        self.assertEqual(LanguageService.get_native_name('en'), 'English')
        self.assertEqual(LanguageService.get_native_name('hi'), 'हिंदी')
        self.assertEqual(LanguageService.get_native_name('mr'), 'मराठी')
        
        # Test case insensitivity
        self.assertEqual(LanguageService.get_native_name('HI'), 'हिंदी')
        
        # Test invalid codes
        self.assertIsNone(LanguageService.get_native_name('fr'))
        self.assertIsNone(LanguageService.get_native_name(''))
    
    def test_get_tts_code(self):
        """Test getting TTS codes for languages."""
        self.assertEqual(LanguageService.get_tts_code('en'), 'en')
        self.assertEqual(LanguageService.get_tts_code('hi'), 'hi')
        self.assertEqual(LanguageService.get_tts_code('mr'), 'mr')
        
        # Test case insensitivity
        self.assertEqual(LanguageService.get_tts_code('EN'), 'en')
        
        # Test invalid codes
        self.assertIsNone(LanguageService.get_tts_code('fr'))
        self.assertIsNone(LanguageService.get_tts_code(''))
    
    def test_get_language_codes(self):
        """Test getting list of language codes."""
        codes = LanguageService.get_language_codes()
        
        self.assertIsInstance(codes, list)
        self.assertIn('en', codes)
        self.assertIn('hi', codes)
        self.assertIn('mr', codes)
        
        # Should only contain enabled languages
        for code in codes:
            self.assertTrue(LanguageService.validate_language(code))
    
    def test_normalize_language_code(self):
        """Test language code normalization."""
        # Test valid codes
        self.assertEqual(LanguageService.normalize_language_code('en'), 'en')
        self.assertEqual(LanguageService.normalize_language_code('EN'), 'en')
        self.assertEqual(LanguageService.normalize_language_code(' Hi '), 'hi')
        self.assertEqual(LanguageService.normalize_language_code('MR'), 'mr')
        
        # Test invalid codes
        self.assertIsNone(LanguageService.normalize_language_code('fr'))
        self.assertIsNone(LanguageService.normalize_language_code(''))
        self.assertIsNone(LanguageService.normalize_language_code(None))
        self.assertIsNone(LanguageService.normalize_language_code(123))
    
    def test_get_fallback_language(self):
        """Test fallback language functionality."""
        # Valid languages should return themselves
        self.assertEqual(LanguageService.get_fallback_language('en'), 'en')
        self.assertEqual(LanguageService.get_fallback_language('hi'), 'hi')
        self.assertEqual(LanguageService.get_fallback_language('mr'), 'mr')
        
        # Case insensitive
        self.assertEqual(LanguageService.get_fallback_language('EN'), 'en')
        
        # Invalid languages should return default
        self.assertEqual(LanguageService.get_fallback_language('fr'), 'en')
        self.assertEqual(LanguageService.get_fallback_language(''), 'en')
        self.assertEqual(LanguageService.get_fallback_language(None), 'en')
        self.assertEqual(LanguageService.get_fallback_language('invalid'), 'en')


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions."""
    
    def test_validate_language_function(self):
        """Test standalone validate_language function."""
        self.assertTrue(validate_language('en'))
        self.assertTrue(validate_language('hi'))
        self.assertFalse(validate_language('fr'))
        self.assertFalse(validate_language(''))
    
    def test_get_supported_languages_function(self):
        """Test standalone get_supported_languages function."""
        languages = get_supported_languages()
        self.assertIsInstance(languages, dict)
        self.assertIn('en', languages)
        self.assertIn('hi', languages)
        self.assertIn('mr', languages)
    
    def test_get_default_language_function(self):
        """Test standalone get_default_language function."""
        default = get_default_language()
        self.assertEqual(default, 'en')
    
    def test_normalize_language_code_function(self):
        """Test standalone normalize_language_code function."""
        self.assertEqual(normalize_language_code('EN'), 'en')
        self.assertEqual(normalize_language_code(' hi '), 'hi')
        self.assertIsNone(normalize_language_code('fr'))


class TestLanguageServiceEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def test_empty_and_whitespace_inputs(self):
        """Test handling of empty and whitespace-only inputs."""
        empty_inputs = ['', '   ', '\t', '\n', '  \t\n  ']
        
        for empty_input in empty_inputs:
            self.assertFalse(LanguageService.validate_language(empty_input))
            self.assertIsNone(LanguageService.normalize_language_code(empty_input))
            self.assertEqual(LanguageService.get_fallback_language(empty_input), 'en')
    
    def test_non_string_inputs(self):
        """Test handling of non-string inputs."""
        non_string_inputs = [123, [], {}, None, True, False, 3.14]
        
        for non_string_input in non_string_inputs:
            self.assertFalse(LanguageService.validate_language(non_string_input))
            self.assertIsNone(LanguageService.normalize_language_code(non_string_input))
            self.assertEqual(LanguageService.get_fallback_language(non_string_input), 'en')
    
    def test_unicode_handling(self):
        """Test handling of unicode characters in language codes."""
        unicode_inputs = ['हिंदी', 'मराठी', 'English', '中文']
        
        for unicode_input in unicode_inputs:
            # These should not be valid language codes (we expect ISO codes)
            self.assertFalse(LanguageService.validate_language(unicode_input))
    
    def test_language_metadata_consistency(self):
        """Test that all language metadata is consistent."""
        languages = LanguageService.SUPPORTED_LANGUAGES
        
        for code, lang_data in languages.items():
            # Each language should have all required fields
            required_fields = ['name', 'native', 'tts_code', 'enabled']
            for field in required_fields:
                self.assertIn(field, lang_data, f"Language {code} missing field {field}")
            
            # TTS code should match language code for our supported languages
            self.assertEqual(lang_data['tts_code'], code)
            
            # Name and native should be non-empty strings
            self.assertIsInstance(lang_data['name'], str)
            self.assertIsInstance(lang_data['native'], str)
            self.assertTrue(len(lang_data['name']) > 0)
            self.assertTrue(len(lang_data['native']) > 0)


if __name__ == '__main__':
    unittest.main()