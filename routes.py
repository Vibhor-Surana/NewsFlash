import logging
from flask import render_template, request, jsonify, session, send_from_directory
from app import app, db
from models import ConversationSession, NewsArticle
from conversation_graph import NewsConversationGraph
from news_service import NewsService
from article_extractor import ArticleExtractor
from tts_service import TTSService
from session_manager import SessionManager
import uuid
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Initialize services
conversation_graph = NewsConversationGraph()
news_service = NewsService()
article_extractor = ArticleExtractor()
tts_service = TTSService()

@app.route('/')
def index():
    """Main page route"""
    try:
        # Generate or get session ID
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
            SessionManager.set_session_id(session['session_id'])
            logger.info(f"Created new session: {session['session_id']}")
        
        # Initialize session defaults (language preferences, etc.)
        SessionManager.initialize_session_defaults()
        
        # Get or create conversation session
        conv_session = ConversationSession.query.filter_by(session_id=session['session_id']).first()
        if not conv_session:
            conv_session = ConversationSession()
            conv_session.session_id = session['session_id']
            conv_session.state = '{}'
            conv_session.topics = '[]'
            db.session.add(conv_session)
            db.session.commit()
            logger.info(f"Created new conversation session for: {session['session_id']}")
        
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'error': 'No session found'}), 400
        
        # Get conversation session
        conv_session = ConversationSession.query.filter_by(session_id=session_id).first()
        if not conv_session:
            return jsonify({'error': 'Conversation session not found'}), 400
        
        # Get current state
        current_state = conv_session.get_state()
        current_state.update({
            'topics': conv_session.get_topics(),
            'user_input': user_message
        })
        
        # Process conversation
        result = conversation_graph.process_conversation(user_message, current_state)
        
        # Update conversation session
        conv_session.set_topics(result.get('topics', []))
        conv_session.set_state(result)
        conv_session.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        logger.info(f"Chat processed for session {session_id}: {result}")
        
        response_data = {
            'response': result.get('response', 'I apologize, but I encountered an error.'),
            'topics': result.get('topics', []),
            'should_search': result.get('next_action') == 'search',
            'stage': result.get('stage', 'collecting')
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in chat route: {e}")
        return jsonify({'error': 'An error occurred processing your message'}), 500

@app.route('/search', methods=['POST'])
def search():
    """Enhanced search API with language and sentiment support"""
    try:
        # Check if request has JSON content type or force parse
        try:
            data = request.get_json(force=True)
        except Exception:
            data = None
            
        if data is None:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Get search parameters
        query = data.get('query', '').strip()
        language = data.get('language', 'en')
        max_results = data.get('max_results', 5)
        
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        # Validate max_results
        try:
            max_results = int(max_results)
            if max_results < 1 or max_results > 20:
                max_results = 5
        except (ValueError, TypeError):
            max_results = 5
        
        # Validate language using language service
        from language_service import LanguageService
        validated_language = LanguageService.get_fallback_language(language)
        
        if validated_language != language:
            logger.info(f"Language {language} not supported, falling back to {validated_language}")
        
        logger.info(f"Searching news for query: '{query}' in language: {validated_language}, max_results: {max_results}")
        
        # Search for news with language and sentiment support
        try:
            articles = news_service.search_news(query, max_results, validated_language)
            
            # Enhance articles with sentiment analysis if not already present
            enhanced_articles = []
            for article in articles:
                try:
                    # Generate summary with sentiment if not already done
                    if not article.get('sentiment'):
                        summary_data = news_service.generate_summary_with_sentiment(
                            article.get('body', ''), 
                            article.get('title', ''), 
                            validated_language
                        )
                        article['summary'] = summary_data.get('summary', article.get('summary', ''))
                        article['sentiment'] = summary_data.get('sentiment', 'neutral')
                    
                    # Ensure all required fields are present
                    enhanced_article = {
                        'title': article.get('title', 'No title'),
                        'url': article.get('url', ''),
                        'summary': article.get('summary', ''),
                        'sentiment': article.get('sentiment', 'neutral'),
                        'language': validated_language,
                        'date': article.get('date', ''),
                        'source': article.get('source', ''),
                        'topic': query
                    }
                    enhanced_articles.append(enhanced_article)
                    
                except Exception as e:
                    logger.warning(f"Error enhancing article with sentiment: {e}")
                    # Add article with default sentiment if enhancement fails
                    enhanced_article = {
                        'title': article.get('title', 'No title'),
                        'url': article.get('url', ''),
                        'summary': article.get('summary', article.get('body', '')[:200]),
                        'sentiment': 'neutral',
                        'language': validated_language,
                        'date': article.get('date', ''),
                        'source': article.get('source', ''),
                        'topic': query
                    }
                    enhanced_articles.append(enhanced_article)
            
            logger.info(f"Successfully processed {len(enhanced_articles)} articles with sentiment data")
            
            return jsonify({
                'success': True,
                'query': query,
                'language': validated_language,
                'total_results': len(enhanced_articles),
                'articles': enhanced_articles
            })
            
        except Exception as search_error:
            logger.error(f"Error during news search: {search_error}")
            return jsonify({
                'error': f'Search failed: {str(search_error)}',
                'query': query,
                'language': validated_language
            }), 500
        
    except Exception as e:
        logger.error(f"Error in search route: {e}")
        return jsonify({'error': 'An error occurred while processing the search request'}), 500

@app.route('/search_news', methods=['POST'])
def search_news():
    """Search for news articles with language support"""
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'error': 'No session found'}), 400
        
        # Get conversation session
        conv_session = ConversationSession.query.filter_by(session_id=session_id).first()
        if not conv_session:
            return jsonify({'error': 'Conversation session not found'}), 400
        
        topics = conv_session.get_topics()
        if not topics:
            return jsonify({'error': 'No topics to search'}), 400
        
        # Get language preference from request or session
        data = request.get_json() or {}
        language = data.get('language') or SessionManager.get_language_preference()
        
        # Validate language
        from language_service import LanguageService
        validated_language = LanguageService.get_fallback_language(language)
        
        logger.info(f"Searching news for topics: {topics} in language: {validated_language}")
        
        # Search for news with language support
        news_results = news_service.search_multiple_topics(topics, language=validated_language)
        
        # Save articles to database
        saved_count = 0
        for topic, articles in news_results.items():
            for article in articles:
                try:
                    news_article = NewsArticle()
                    news_article.title = str(article['title'])[:500] if article.get('title') else 'No title'
                    news_article.url = str(article['url'])[:1000] if article.get('url') else ''
                    news_article.summary = str(article.get('summary', ''))[:2000] if article.get('summary') else ''
                    news_article.sentiment = str(article.get('sentiment', 'neutral'))[:20]
                    news_article.language = validated_language
                    news_article.summary_language = validated_language
                    news_article.topic = str(topic)[:200]
                    news_article.session_id = session_id
                    db.session.add(news_article)
                    saved_count += 1
                except Exception as e:
                    logger.warning(f"Failed to save article: {e}")
                    continue
        
        try:
            db.session.commit()
            logger.info(f"Saved {saved_count} articles to database")
        except Exception as e:
            logger.error(f"Failed to commit articles to database: {e}")
            db.session.rollback()
        
        return jsonify({
            'success': True,
            'results': news_results,
            'language': validated_language
        })
        
    except Exception as e:
        logger.error(f"Error in search_news route: {e}")
        return jsonify({'error': 'An error occurred while searching for news'}), 500

@app.route('/load_more/<topic>')
def load_more(topic):
    """Load more articles for a specific topic"""
    try:
        # Search for more articles
        more_articles = news_service.search_news(topic, max_results=5)
        
        # Save to database
        session_id = session.get('session_id')
        if session_id:
            for article in more_articles:
                try:
                    news_article = NewsArticle()
                    news_article.title = str(article['title'])[:500] if article.get('title') else 'No title'
                    news_article.url = str(article['url'])[:1000] if article.get('url') else ''
                    news_article.summary = str(article.get('summary', ''))[:2000] if article.get('summary') else ''
                    news_article.topic = str(topic)[:200]
                    news_article.session_id = session_id
                    db.session.add(news_article)
                except Exception as e:
                    logger.warning(f"Failed to save article in load_more: {e}")
                    continue
            try:
                db.session.commit()
            except Exception as e:
                logger.error(f"Failed to commit load_more articles: {e}")
                db.session.rollback()
        
        return jsonify({
            'success': True,
            'articles': more_articles
        })
        
    except Exception as e:
        logger.error(f"Error loading more articles for topic {topic}: {e}")
        return jsonify({'error': 'An error occurred while loading more articles'}), 500

@app.route('/full_article', methods=['POST'])
def get_full_article():
    """Get full article content"""
    try:
        data = request.get_json()
        url = data.get('url')
        title = data.get('title', '')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        logger.info(f"Extracting full article from: {url}")
        
        # Extract full article
        article_data = article_extractor.get_readable_article(url, title)
        
        # Log extraction results for debugging
        logger.info(f"Article extraction completed - Content length: {len(article_data['content'])}, Formatted: {article_data['formatted']}")
        
        return jsonify({
            'success': True,
            'content': article_data['content'],
            'formatted': article_data['formatted']
        })
        
    except Exception as e:
        logger.error(f"Error extracting full article: {e}")
        return jsonify({'error': 'An error occurred while extracting the article'}), 500

@app.route('/tts', methods=['POST'])
def text_to_speech():
    """Generate text-to-speech audio with language support"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        language = data.get('language', None)
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        # Get language preference from session if not provided in request
        if not language:
            language = SessionManager.get_language_preference()
        
        # Validate language using language service
        from language_service import LanguageService
        validated_language = LanguageService.get_fallback_language(language)
        
        logger.info(f"Generating TTS for text of length: {len(text)} in language: {validated_language}")
        
        # Generate TTS with language support
        audio_url = tts_service.text_to_speech(text, validated_language)
        
        if audio_url:
            return jsonify({
                'success': True,
                'audio_url': audio_url,
                'language': validated_language
            })
        else:
            # Return specific error message for TTS failures
            error_msg = f'Failed to generate audio in {validated_language}'
            if validated_language != 'en':
                error_msg += '. Fallback to English also failed.'
            return jsonify({'error': error_msg}), 500
        
    except Exception as e:
        logger.error(f"Error in TTS route: {e}")
        return jsonify({'error': 'An error occurred while generating audio'}), 500

@app.route('/static/audio/<filename>')
def serve_audio(filename):
    """Serve audio files"""
    try:
        return send_from_directory(os.path.join(app.root_path, 'static', 'audio'), filename)
    except Exception as e:
        logger.error(f"Error serving audio file {filename}: {e}")
        return "Audio file not found", 404

@app.route('/set-language', methods=['POST'])
def set_language():
    """Set user language preference"""
    try:
        # Check if request has JSON content type or force parse
        try:
            data = request.get_json(force=True)
        except Exception:
            data = None
            
        if data is None:
            return jsonify({'error': 'Request body is required'}), 400
        
        language = data.get('language', '')
        
        # Validate language parameter type
        if not isinstance(language, str):
            return jsonify({'error': 'Language must be a string'}), 400
        
        language = language.strip()
        
        if not language:
            return jsonify({'error': 'Language is required'}), 400
        
        # Use session manager to set language preference
        if not SessionManager.set_language_preference(language):
            return jsonify({'success': False, 'error': f'Unsupported language: {language}'}), 400
        
        # Get language name for response
        from language_service import LanguageService
        language_name = LanguageService.get_language_name(language)
        
        logger.info(f"Language preference set to: {language} for session: {SessionManager.get_session_id()}")
        
        return jsonify({
            'success': True,
            'language': language.lower(),
            'message': f'Language preference set to {language_name}'
        })
        
    except Exception as e:
        logger.error(f"Error setting language preference: {e}")
        return jsonify({'error': 'An error occurred while setting language preference'}), 500

@app.route('/get-languages', methods=['GET'])
def get_languages():
    """Get supported languages"""
    try:
        from language_service import LanguageService
        
        languages = LanguageService.get_supported_languages()
        current_language = SessionManager.get_language_preference()
        
        return jsonify({
            'success': True,
            'languages': languages,
            'current_language': current_language
        })
        
    except Exception as e:
        logger.error(f"Error getting supported languages: {e}")
        return jsonify({'error': 'An error occurred while getting supported languages'}), 500

@app.route('/session-info', methods=['GET'])
def get_session_info():
    """Get comprehensive session information"""
    try:
        session_info = SessionManager.get_session_info()
        
        return jsonify({
            'success': True,
            'session_info': session_info
        })
        
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        return jsonify({'error': 'An error occurred while getting session information'}), 500

@app.route('/reset_conversation', methods=['POST'])
def reset_conversation():
    """Reset the conversation session"""
    try:
        session_id = session.get('session_id')
        if session_id:
            conv_session = ConversationSession.query.filter_by(session_id=session_id).first()
            if conv_session:
                conv_session.set_topics([])
                conv_session.set_state({})
                conv_session.updated_at = datetime.now(timezone.utc)
                db.session.commit()
                logger.info(f"Reset conversation for session: {session_id}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error resetting conversation: {e}")
        return jsonify({'error': 'An error occurred while resetting the conversation'}), 500

@app.route('/favicon.ico')
def favicon():
    """Return 404 for favicon requests"""
    return '', 404

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"404 error: {request.url}")
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {error}")
    db.session.rollback()
    return render_template('index.html'), 500

@app.teardown_appcontext
def close_db(error):
    """Close database connection on app context teardown"""
    if error:
        db.session.rollback()
    try:
        db.session.close()
    except Exception:
        pass
