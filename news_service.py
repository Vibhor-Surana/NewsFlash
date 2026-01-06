import logging
from typing import List, Dict, Any
from duckduckgo_search import DDGS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from config import Config
from language_service import LanguageService
from error_handler import (
    ErrorHandler, FallbackManager, with_language_fallback, with_sentiment_fallback, 
    with_retry, handle_language_operation, handle_sentiment_operation,
    LanguageError, SentimentAnalysisError, AIServiceError
)
import os

# Set environment variables for LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = Config.LANGSMITH_ENDPOINT
os.environ["LANGCHAIN_API_KEY"] = Config.LANGSMITH_API_KEY
os.environ["LANGCHAIN_PROJECT"] = Config.LANGSMITH_PROJECT

logger = logging.getLogger(__name__)

class NewsService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=Config.GEMINI_API_KEY,
            temperature=0.1
        )
        self.ddgs = DDGS()
        self._init_prompt_templates()
        logger.info("NewsService initialized successfully")
    
    def _init_prompt_templates(self):
        """Initialize language-specific prompt templates for sentiment analysis"""
        self.prompt_templates = {
            'en': ChatPromptTemplate.from_template(
                """Create a 2-sentence summary and analyze sentiment (positive/negative/neutral) for this news article:
                
                Title: {title}
                Article: {article_text}
                
                Format your response as:
                Summary: [your summary]
                Sentiment: [positive/negative/neutral]"""
            ),
            'hi': ChatPromptTemplate.from_template(
                """इस समाचार लेख का 2-वाक्य सारांश बनाएं और भावना (सकारात्मक/नकारात्मक/तटस्थ) का विश्लेषण करें:
                
                शीर्षक: {title}
                लेख: {article_text}
                
                अपना उत्तर इस प्रारूप में दें:
                सारांश: [आपका सारांश]
                भावना: [सकारात्मक/नकारात्मक/तटस्थ]"""
            ),
            'mr': ChatPromptTemplate.from_template(
                """या बातमी लेखाचा 2-वाक्य सारांश तयार करा आणि भावना (सकारात्मक/नकारात्मक/तटस्थ) चे विश्लेषण करा:
                
                शीर्षक: {title}
                लेख: {article_text}
                
                तुमचे उत्तर या स्वरूपात द्या:
                सारांश: [तुमचा सारांश]
                भावना: [सकारात्मक/नकारात्मक/तटस्थ]"""
            )
        }
    
    def get_sentiment_prompt_template(self, language: str = 'en') -> ChatPromptTemplate:
        """Get the appropriate prompt template for the specified language with fallback"""
        # Validate and normalize language code
        normalized_language = LanguageService.get_fallback_language(language)
        return self.prompt_templates.get(normalized_language, self.prompt_templates['en'])
    
    @with_sentiment_fallback("neutral")
    @with_language_fallback()
    @with_retry()
    def analyze_sentiment(self, text: str, language: str = 'en') -> str:
        """Analyze sentiment of text with comprehensive error handling and fallbacks"""
        try:
            # For very short text, default to neutral
            if len(text.strip()) < 20:
                logger.debug("Text too short for sentiment analysis, returning neutral")
                return 'neutral'
            
            # Validate and get fallback language if needed
            target_language = LanguageService.get_fallback_language(language)
            if target_language != language:
                ErrorHandler.log_language_error(
                    "analyze_sentiment", language, 
                    Exception(f"Language not supported"), target_language
                )
            
            # Use the sentiment analysis prompt template
            prompt_template = self.get_sentiment_prompt_template(target_language)
            
            # Rate limiting: Add delay between requests
            import time
            time.sleep(Config.RATE_LIMIT_DELAY)
            
            chain = prompt_template | self.llm
            result = chain.invoke({
                "title": "Sentiment Analysis",
                "article_text": text[:800]  # Limit text to reduce token usage
            })
            
            if hasattr(result, 'content') and result.content:
                # Parse sentiment from response
                sentiment = self._parse_sentiment_from_response(result.content)
                logger.info(f"Analyzed sentiment: {sentiment} (language: {target_language})")
                return sentiment
            else:
                raise SentimentAnalysisError("No content in sentiment analysis response")
                
        except Exception as e:
            # Let the decorator handle the fallback
            raise SentimentAnalysisError(f"Sentiment analysis failed: {e}")
    
    def _parse_sentiment_from_response(self, response_text: str) -> str:
        """Parse sentiment from AI response text"""
        response_lower = response_text.lower()
        
        # Look for sentiment indicators in different languages
        if any(word in response_lower for word in ['positive', 'सकारात्मक', 'सकारात्मक']):
            return 'positive'
        elif any(word in response_lower for word in ['negative', 'नकारात्मक', 'नकारात्मक']):
            return 'negative'
        elif any(word in response_lower for word in ['neutral', 'तटस्थ', 'तटस्थ']):
            return 'neutral'
        else:
            # If no clear sentiment found, try to extract from "Sentiment:" line
            lines = response_text.split('\n')
            for line in lines:
                if 'sentiment:' in line.lower() or 'भावना:' in line.lower():
                    line_lower = line.lower()
                    if 'positive' in line_lower or 'सकारात्मक' in line_lower:
                        return 'positive'
                    elif 'negative' in line_lower or 'नकारात्मक' in line_lower:
                        return 'negative'
                    elif 'neutral' in line_lower or 'तटस्थ' in line_lower:
                        return 'neutral'
            
            # Default fallback
            return 'neutral'
    
    def generate_summary_with_sentiment(self, article_text: str, title: str, language: str = 'en') -> dict:
        """Generate summary and sentiment analysis in a single API call with comprehensive error handling"""
        try:
            # Skip AI analysis for very short articles or if disabled
            if len(article_text) < Config.AI_SUMMARY_MIN_LENGTH or not Config.USE_AI_SUMMARY:
                return {
                    'summary': FallbackManager.create_fallback_summary(article_text),
                    'sentiment': FallbackManager.get_sentiment_fallback(),
                    'language': LanguageService.get_fallback_language(language)
                }
            
            # Use comprehensive error handling for language operations
            return handle_language_operation(
                "generate_summary_with_sentiment",
                language,
                self._generate_summary_with_sentiment_for_language,
                article_text, title
            )
                
        except Exception as e:
            # Final fallback with comprehensive error logging
            target_language = LanguageService.get_fallback_language(language)
            
            if "429" in str(e) or "quota" in str(e).lower():
                ErrorHandler.log_ai_service_error("generate_summary_with_sentiment", e)
                logger.warning(f"Rate limit hit, using fallback for: {title[:50]}...")
            else:
                ErrorHandler.log_language_error("generate_summary_with_sentiment", target_language, e)
            
            return {
                'summary': FallbackManager.create_fallback_summary(article_text),
                'sentiment': FallbackManager.get_sentiment_fallback(),
                'language': target_language
            }
    
    @with_retry()
    def _generate_summary_with_sentiment_for_language(self, article_text: str, title: str, language: str) -> dict:
        """Internal method to generate summary and sentiment for a specific language with retry logic"""
        try:
            # Rate limiting: Add delay between requests
            import time
            time.sleep(Config.RATE_LIMIT_DELAY)
            
            prompt_template = self.get_sentiment_prompt_template(language)
            
            chain = prompt_template | self.llm
            result = chain.invoke({
                "title": title[:200],  # Limit title length
                "article_text": article_text[:800]  # Limit text to reduce memory usage
            })
            
            if hasattr(result, 'content') and result.content:
                # Parse both summary and sentiment from response
                summary, sentiment = self._parse_summary_and_sentiment(result.content)
                logger.info(f"Generated summary and sentiment for article in {language}: {title[:50]}...")
                return {
                    'summary': summary or FallbackManager.create_fallback_summary(article_text),
                    'sentiment': sentiment or FallbackManager.get_sentiment_fallback(),
                    'language': language
                }
            else:
                raise AIServiceError("No content in AI response")
                
        except Exception as e:
            # Enhanced error logging
            ErrorHandler.log_ai_service_error("_generate_summary_with_sentiment_for_language", e)
            raise AIServiceError(f"Failed to generate summary and sentiment: {e}")
    
    def _parse_summary_and_sentiment(self, response_text: str) -> tuple:
        """Parse both summary and sentiment from AI response"""
        summary = None
        sentiment = None
        
        lines = response_text.split('\n')
        
        for line in lines:
            line_stripped = line.strip()
            
            # Look for summary line
            if line_stripped.lower().startswith('summary:') or line_stripped.startswith('सारांश:'):
                summary = line_stripped.split(':', 1)[1].strip() if ':' in line_stripped else None
            
            # Look for sentiment line
            elif line_stripped.lower().startswith('sentiment:') or line_stripped.startswith('भावना:'):
                sentiment_text = line_stripped.split(':', 1)[1].strip() if ':' in line_stripped else None
                if sentiment_text:
                    sentiment = self._parse_sentiment_from_response(sentiment_text)
        
        # If parsing failed, try to extract from full response
        if not summary:
            # Look for content after "Summary:" or "सारांश:"
            summary_start = -1
            for i, line in enumerate(lines):
                if 'summary:' in line.lower() or 'सारांश:' in line.lower():
                    summary_start = i
                    break
            
            if summary_start >= 0 and summary_start + 1 < len(lines):
                # Take next few lines as summary
                summary_lines = []
                for i in range(summary_start + 1, min(summary_start + 4, len(lines))):
                    if lines[i].strip() and not lines[i].lower().startswith('sentiment:') and not lines[i].startswith('भावना:'):
                        summary_lines.append(lines[i].strip())
                    else:
                        break
                summary = ' '.join(summary_lines) if summary_lines else None
        
        if not sentiment:
            sentiment = self._parse_sentiment_from_response(response_text)
        
        return summary, sentiment

    def search_news(self, topic: str, max_results: int = 5, language: str = 'en') -> List[Dict[str, Any]]:
        """Search for news articles on a given topic using DuckDuckGo with language support"""
        try:
            logger.info(f"Searching for news on topic: {topic} (language: {language})")
            
            # Validate and get fallback language if needed
            target_language = LanguageService.get_fallback_language(language)
            if target_language != language:
                logger.info(f"Language {language} not supported for search, using {target_language}")
            
            # Search for news using DuckDuckGo
            search_query = f"{topic} news"
            results = list(self.ddgs.news(keywords=search_query, max_results=max_results, safesearch='moderate'))
            
            news_articles = []
            for result in results:
                article = {
                    'title': str(result.get('title', 'No title'))[:500],
                    'url': str(result.get('url', ''))[:1000],
                    'body': str(result.get('body', ''))[:2000],
                    'date': str(result.get('date', '')),
                    'source': str(result.get('source', ''))[:200],
                    'topic': topic,
                    'language': target_language
                }
                
                # Generate AI-powered summary using Gemini with language support
                try:
                    if article['body'] and len(article['body']) > 50:
                        summary = self.generate_summary(article['body'], article['title'], target_language)
                        article['summary'] = str(summary)[:2000] if summary else article['body'][:200]
                    else:
                        article['summary'] = article['body'] if article['body'] else 'No summary available'
                except Exception as e:
                    logger.error(f"Error generating summary for article: {e}")
                    article['summary'] = article['body'][:200] + "..." if len(article['body']) > 200 else article['body']
                
                news_articles.append(article)
                logger.debug(f"Added article: {article['title']}")
            
            logger.info(f"Found {len(news_articles)} articles for topic: {topic} (language: {target_language})")
            return news_articles
            
        except Exception as e:
            logger.error(f"Error searching news for topic {topic}: {e}")
            return []

    def generate_summary(self, article_text: str, title: str, language: str = 'en', include_sentiment: bool = False) -> str:
        """Generate a concise summary of the article using Gemini with comprehensive error handling
        
        Args:
            article_text: The article content to summarize
            title: The article title
            language: Language for the summary (en, hi, mr)
            include_sentiment: Whether to include sentiment analysis (for backward compatibility)
        
        Returns:
            Summary text (or dict with summary and sentiment if include_sentiment=True)
        """
        if include_sentiment:
            # Use the new combined method
            return self.generate_summary_with_sentiment(article_text, title, language)
        
        try:
            # Skip AI summary for very short articles or if disabled
            if len(article_text) < Config.AI_SUMMARY_MIN_LENGTH or not Config.USE_AI_SUMMARY:
                return FallbackManager.create_fallback_summary(article_text)
            
            # Use comprehensive error handling for language operations
            return handle_language_operation(
                "generate_summary",
                language,
                self._generate_summary_for_language,
                article_text, title
            )
            
        except Exception as e:
            # Final fallback with comprehensive error logging
            target_language = LanguageService.get_fallback_language(language)
            
            if "429" in str(e) or "quota" in str(e).lower():
                ErrorHandler.log_ai_service_error("generate_summary", e)
                logger.warning(f"Rate limit hit, using fallback summary for: {title[:50]}...")
            else:
                ErrorHandler.log_language_error("generate_summary", target_language, e)
            
            return FallbackManager.create_fallback_summary(article_text)
    
    @with_retry()
    def _generate_summary_for_language(self, article_text: str, title: str, language: str) -> str:
        """Internal method to generate summary for a specific language with retry logic"""
        try:
            # Rate limiting: Add delay between requests
            import time
            time.sleep(Config.RATE_LIMIT_DELAY)
            
            # Use language-specific template if available, otherwise use simple English template
            if language != 'en':
                # For non-English, use the sentiment template but only return summary
                result = self._generate_summary_with_sentiment_for_language(article_text, title, language)
                return result['summary']
            else:
                # Use original simple template for English-only summary
                prompt_template = ChatPromptTemplate.from_template(
                    """Create a 2-sentence summary of this news article:
                    
                    Title: {title}
                    Article: {article_text}
                    
                    Summary:"""
                )
                
                chain = prompt_template | self.llm
                result = chain.invoke({
                    "title": title[:200],  # Limit title length
                    "article_text": article_text[:800]  # Limit text to reduce memory usage
                })
                
                if hasattr(result, 'content') and result.content:
                    summary = result.content.strip()
                    logger.info(f"Generated AI summary for article in {language}: {title[:50]}...")
                    return summary
                else:
                    raise AIServiceError("No content in AI summary response")
                    
        except Exception as e:
            # Enhanced error logging
            ErrorHandler.log_ai_service_error("_generate_summary_for_language", e)
            raise AIServiceError(f"Failed to generate summary: {e}")
    
    def _create_fallback_summary(self, article_text: str) -> str:
        """Create a fallback summary without AI - deprecated, use FallbackManager instead"""
        logger.warning("Using deprecated _create_fallback_summary, consider using FallbackManager.create_fallback_summary")
        return FallbackManager.create_fallback_summary(article_text)

    def search_multiple_topics(self, topics: List[str], max_results_per_topic: int = 5, language: str = 'en') -> Dict[str, List[Dict[str, Any]]]:
        """Search for news on multiple topics with language support"""
        all_results = {}
        
        # Validate and get fallback language if needed
        target_language = LanguageService.get_fallback_language(language)
        if target_language != language:
            logger.info(f"Language {language} not supported for multi-topic search, using {target_language}")
        
        for topic in topics:
            logger.info(f"Searching news for topic: {topic} (language: {target_language})")
            try:
                articles = self.search_news(topic, max_results_per_topic, target_language)
                all_results[topic] = articles
                logger.info(f"Found {len(articles)} articles for {topic}")
            except Exception as e:
                logger.error(f"Error searching for topic {topic}: {e}")
                all_results[topic] = []
        
        return all_results
