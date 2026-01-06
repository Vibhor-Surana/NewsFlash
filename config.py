import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys - REQUIRED: Set these in your .env file
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    
    # Validate required API keys
    @classmethod
    def validate_config(cls):
        missing_keys = []
        if not cls.GEMINI_API_KEY:
            missing_keys.append("GEMINI_API_KEY")
        if not cls.LANGSMITH_API_KEY:
            missing_keys.append("LANGSMITH_API_KEY")
        
        if missing_keys:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}. Please set them in your .env file.")
        
        # Validate language configuration
        if cls.DEFAULT_LANGUAGE not in cls.SUPPORTED_LANGUAGES:
            raise ValueError(f"DEFAULT_LANGUAGE '{cls.DEFAULT_LANGUAGE}' is not in SUPPORTED_LANGUAGES. Must be one of: {list(cls.SUPPORTED_LANGUAGES.keys())}")
        
        return True
    
    # Language helper methods
    @classmethod
    def get_supported_languages(cls):
        """Get list of supported languages with metadata"""
        return cls.SUPPORTED_LANGUAGES
    
    @classmethod
    def is_language_supported(cls, language_code):
        """Check if a language code is supported"""
        return language_code in cls.SUPPORTED_LANGUAGES
    
    @classmethod
    def get_language_info(cls, language_code):
        """Get language information for a given code"""
        return cls.SUPPORTED_LANGUAGES.get(language_code, cls.SUPPORTED_LANGUAGES[cls.DEFAULT_LANGUAGE])
    
    @classmethod
    def get_tts_language_code(cls, language_code):
        """Get TTS language code for a given language"""
        lang_info = cls.get_language_info(language_code)
        return lang_info.get('tts_code', 'en')
    
    # LangSmith Configuration
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "news-website")
    LANGSMITH_ENDPOINT = "https://api.smith.langchain.com"
    
    # Application Settings
    NEWS_RESULTS_PER_TOPIC = 5
    LOAD_MORE_COUNT = 5
    
    # TTS Settings
    TTS_LANGUAGE = 'en'
    TTS_SLOW = False
    
    # Language Settings
    DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
    SUPPORTED_LANGUAGES = {
        'en': {'name': 'English', 'native': 'English', 'tts_code': 'en'},
        'hi': {'name': 'Hindi', 'native': 'हिंदी', 'tts_code': 'hi'},
        'mr': {'name': 'Marathi', 'native': 'मराठी', 'tts_code': 'mr'}
    }
    LANGUAGE_FALLBACK_ENABLED = os.getenv("LANGUAGE_FALLBACK_ENABLED", "true").lower() == "true"
    
    # Sentiment Analysis Settings
    SENTIMENT_ANALYSIS_ENABLED = os.getenv("SENTIMENT_ANALYSIS_ENABLED", "true").lower() == "true"
    SENTIMENT_DEFAULT = "neutral"  # Default sentiment when analysis fails
    SENTIMENT_DISPLAY_ENABLED = os.getenv("SENTIMENT_DISPLAY_ENABLED", "true").lower() == "true"
    
    # AI Settings
    USE_AI_SUMMARY = os.getenv("USE_AI_SUMMARY", "true").lower() == "true"
    AI_SUMMARY_MIN_LENGTH = 150  # Only use AI for articles longer than this
    RATE_LIMIT_DELAY = 2  # Seconds between AI requests
    
    # Error Handling Settings
    MAX_RETRY_ATTEMPTS = 3  # Maximum retry attempts for AI operations
    RETRY_DELAY = 1  # Base delay between retries (exponential backoff)
    ENABLE_FALLBACK_LOGGING = True  # Enable detailed fallback logging
    SENTIMENT_FALLBACK_ENABLED = True  # Enable sentiment analysis fallbacks
    LANGUAGE_FALLBACK_ENABLED = True  # Enable language fallbacks
