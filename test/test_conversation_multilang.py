"""
Tests for multi-language conversation flow functionality.

This module tests the language-aware conversation features including:
- Language selection in conversation state
- Multi-language conversation prompts
- Language preference persistence in conversation state
- Language-aware conversation flows
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from conversation_graph import NewsConversationGraph, ConversationState
from language_service import LanguageService


class TestMultiLanguageConversationFlow:
    """Test class for multi-language conversation flow functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.conversation_graph = NewsConversationGraph()
    
    def test_initial_language_selection_stage(self):
        """Test that conversation starts with language selection stage."""
        result = self.conversation_graph.process_conversation("hello")
        
        assert result['stage'] == 'language_selection'
        assert result['language_confirmed'] == False
        assert 'language would you prefer' in result['response']
    
    def test_english_language_selection(self):
        """Test selecting English language."""
        result = self.conversation_graph.process_conversation("English")
        
        assert result['stage'] == 'collecting'
        assert result['language'] == 'en'
        assert result['language_confirmed'] == True
        assert 'English' in result['response']
        assert 'topic' in result['response'].lower()
    
    def test_hindi_language_selection(self):
        """Test selecting Hindi language."""
        result = self.conversation_graph.process_conversation("Hindi")
        
        assert result['stage'] == 'collecting'
        assert result['language'] == 'hi'
        assert result['language_confirmed'] == True
        assert 'Hindi' in result['response']
    
    def test_marathi_language_selection(self):
        """Test selecting Marathi language."""
        result = self.conversation_graph.process_conversation("Marathi")
        
        assert result['stage'] == 'collecting'
        assert result['language'] == 'mr'
        assert result['language_confirmed'] == True
        assert 'Marathi' in result['response']
    
    def test_hindi_native_language_detection(self):
        """Test detecting Hindi from native script."""
        result = self.conversation_graph.process_conversation("हिंदी")
        
        assert result['language'] == 'hi'
        assert result['language_confirmed'] == True
    
    def test_marathi_native_language_detection(self):
        """Test detecting Marathi from native script."""
        result = self.conversation_graph.process_conversation("मराठी")
        
        assert result['language'] == 'mr'
        assert result['language_confirmed'] == True
    
    def test_language_persistence_across_conversation(self):
        """Test that language preference persists across conversation turns."""
        # First turn - select Hindi
        state1 = self.conversation_graph.process_conversation("Hindi")
        assert state1['language'] == 'hi'
        
        # Second turn - add topic (should maintain Hindi)
        state2 = self.conversation_graph.process_conversation("technology", state1)
        assert state2['language'] == 'hi'
        assert state2['language_confirmed'] == True
        assert 'technology' in state2['topics']
    
    def test_hindi_conversation_prompts(self):
        """Test that Hindi prompts are used when Hindi is selected."""
        # Select Hindi
        state1 = self.conversation_graph.process_conversation("Hindi")
        
        # Add a topic - should get Hindi response
        state2 = self.conversation_graph.process_conversation("प्रौद्योगिकी", state1)
        
        # Response should contain Hindi text
        assert any(hindi_char in state2['response'] for hindi_char in ['आप', 'में', 'के', 'है'])
    
    def test_marathi_conversation_prompts(self):
        """Test that Marathi prompts are used when Marathi is selected."""
        # Select Marathi
        state1 = self.conversation_graph.process_conversation("Marathi")
        
        # Add a topic - should get Marathi response
        state2 = self.conversation_graph.process_conversation("तंत्रज्ञान", state1)
        
        # Response should contain Marathi text
        assert any(marathi_char in state2['response'] for marathi_char in ['तुम्ही', 'मध्ये', 'च्या', 'आहे'])
    
    def test_topic_collection_with_language_preference(self):
        """Test topic collection maintains language preference."""
        # Start with English
        state = self.conversation_graph.process_conversation("English")
        
        # Add multiple topics
        state = self.conversation_graph.process_conversation("technology", state)
        state = self.conversation_graph.process_conversation("sports", state)
        
        assert state['language'] == 'en'
        assert len(state['topics']) == 2
        assert 'technology' in state['topics']
        assert 'sports' in state['topics']
    
    def test_search_trigger_with_language_preference(self):
        """Test search trigger maintains language preference."""
        # Start with Hindi
        state = self.conversation_graph.process_conversation("Hindi")
        
        # Add topic and trigger search
        state = self.conversation_graph.process_conversation("समाचार", state)
        state = self.conversation_graph.process_conversation("no", state)
        
        assert state['stage'] == 'searching'
        assert state['language'] == 'hi'
        assert 'समाचार' in state['topics']
    
    def test_hindi_stop_words(self):
        """Test Hindi stop words for search trigger."""
        # Start with Hindi
        state = self.conversation_graph.process_conversation("Hindi")
        
        # Add topic and use Hindi stop word
        state = self.conversation_graph.process_conversation("खेल", state)
        state = self.conversation_graph.process_conversation("नहीं", state)
        
        assert state['stage'] == 'searching'
        assert state['language'] == 'hi'
    
    def test_marathi_stop_words(self):
        """Test Marathi stop words for search trigger."""
        # Start with Marathi
        state = self.conversation_graph.process_conversation("Marathi")
        
        # Add topic and use Marathi stop word
        state = self.conversation_graph.process_conversation("क्रीडा", state)
        state = self.conversation_graph.process_conversation("नाही", state)
        
        assert state['stage'] == 'searching'
        assert state['language'] == 'mr'
    
    def test_language_detection_methods(self):
        """Test language detection helper methods."""
        # Test direct language detection
        assert self.conversation_graph._detect_language_preference("english") == 'en'
        assert self.conversation_graph._detect_language_preference("hindi") == 'hi'
        assert self.conversation_graph._detect_language_preference("marathi") == 'mr'
        
        # Test native script detection
        assert self.conversation_graph._detect_language_preference("हिंदी") == 'hi'
        assert self.conversation_graph._detect_language_preference("मराठी") == 'mr'
        
        # Test indicator words
        assert self.conversation_graph._detect_language_preference("नमस्ते") == 'hi'
        assert self.conversation_graph._detect_language_preference("नमस्कार") == 'mr'
        
        # Test no detection
        assert self.conversation_graph._detect_language_preference("random text") is None
    
    def test_get_language_from_state(self):
        """Test getting language from conversation state."""
        state_with_lang = {'language': 'hi', 'language_confirmed': True}
        state_without_lang = {}
        
        assert self.conversation_graph.get_language_from_state(state_with_lang) == 'hi'
        assert self.conversation_graph.get_language_from_state(state_without_lang) == 'en'  # Default
    
    def test_set_language_preference(self):
        """Test setting language preference in state."""
        state = {}
        
        # Set valid language
        updated_state = self.conversation_graph.set_language_preference(state, 'hi')
        assert updated_state['language'] == 'hi'
        assert updated_state['language_confirmed'] == True
        
        # Set invalid language (should fallback to English)
        updated_state = self.conversation_graph.set_language_preference(state, 'fr')
        assert updated_state['language'] == 'en'
        assert updated_state['language_confirmed'] == True
    
    def test_is_language_confirmed(self):
        """Test checking if language is confirmed."""
        confirmed_state = {'language_confirmed': True}
        unconfirmed_state = {'language_confirmed': False}
        empty_state = {}
        
        assert self.conversation_graph.is_language_confirmed(confirmed_state) == True
        assert self.conversation_graph.is_language_confirmed(unconfirmed_state) == False
        assert self.conversation_graph.is_language_confirmed(empty_state) == False
    
    def test_reset_conversation_state(self):
        """Test resetting conversation state."""
        # Reset with language
        state_with_lang = self.conversation_graph.reset_conversation_state('hi')
        assert state_with_lang['language'] == 'hi'
        assert state_with_lang['language_confirmed'] == True
        assert state_with_lang['stage'] == 'collecting'
        
        # Reset without language
        state_without_lang = self.conversation_graph.reset_conversation_state()
        assert state_without_lang['language'] == 'en'
        assert state_without_lang['language_confirmed'] == False
        assert state_without_lang['stage'] == 'language_selection'
        
        # Reset with invalid language
        state_invalid_lang = self.conversation_graph.reset_conversation_state('fr')
        assert state_invalid_lang['stage'] == 'language_selection'
        assert state_invalid_lang['language_confirmed'] == False
    
    def test_should_search_news_with_language(self):
        """Test search trigger check with language preference."""
        search_ready_state = {
            'stage': 'searching',
            'topics': ['technology'],
            'language': 'hi'
        }
        
        not_ready_state = {
            'stage': 'collecting',
            'topics': ['technology'],
            'language': 'hi'
        }
        
        assert self.conversation_graph.should_search_news(search_ready_state) == True
        assert self.conversation_graph.should_search_news(not_ready_state) == False
    
    def test_error_handling_with_language_preference(self):
        """Test error handling maintains language preference."""
        # Mock an error in the graph processing
        with patch.object(self.conversation_graph.graph, 'invoke') as mock_invoke:
            mock_invoke.side_effect = Exception("Test error")
            
            # Start with a state that has language preference
            initial_state = {
                'language': 'hi',
                'language_confirmed': True,
                'topics': ['test'],
                'stage': 'collecting'
            }
            
            result = self.conversation_graph.process_conversation("test input", initial_state)
            
            # Should maintain language preference even after error
            assert result['language'] == 'hi'
            # The error response should be in Hindi or contain error-related text
            assert ('error' in result['response'].lower() or 
                    'try again' in result['response'].lower() or
                    'कृपया' in result['response'] or  # Hindi "please"
                    'विषय' in result['response'])  # Hindi "topic"
    
    def test_language_prompts_initialization(self):
        """Test that language prompts are properly initialized."""
        # Check that all required languages have prompts
        required_languages = ['en', 'hi', 'mr']
        for lang in required_languages:
            assert lang in self.conversation_graph.language_prompts
            
            # Check that all required prompt keys exist
            required_keys = ['welcome', 'language_set', 'topic_added', 'topic_exists', 'search_ready', 'need_topic', 'ask_topic']
            for key in required_keys:
                assert key in self.conversation_graph.language_prompts[lang]
    
    def test_conversation_flow_integration_with_language_service(self):
        """Test integration with LanguageService for validation."""
        # Test that conversation graph uses LanguageService for validation
        with patch.object(LanguageService, 'validate_language') as mock_validate:
            mock_validate.return_value = True
            
            state = self.conversation_graph.reset_conversation_state('hi')
            
            # Should have called validation (indirectly through get_fallback_language)
            assert state['language'] == 'hi'


if __name__ == '__main__':
    pytest.main([__file__])