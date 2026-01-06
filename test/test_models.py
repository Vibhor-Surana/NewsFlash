#!/usr/bin/env python3
"""
Tests for enhanced database models with sentiment and language support.
"""

import pytest
import tempfile
import os
from datetime import datetime, timezone
from app import app, db
from models import NewsArticle, ConversationSession


@pytest.fixture
def test_app():
    """Create a test Flask application with in-memory database."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.app_context():
        # Import models to ensure they're available
        import models
        # Create all tables with the current schema (including new columns)
        db.create_all()
        yield app
        db.drop_all()
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return test_app.test_client()


class TestNewsArticleModel:
    """Test cases for the enhanced NewsArticle model."""
    
    def test_create_article_with_default_values(self, test_app):
        """Test creating an article with default sentiment and language values."""
        with test_app.app_context():
            article = NewsArticle(
                title="Test Article",
                url="https://example.com/test",
                summary="Test summary",
                full_content="Test content",
                topic="technology",
                session_id="test_session_123"
            )
            
            db.session.add(article)
            db.session.commit()
            
            # Check default values
            assert article.sentiment == 'neutral'
            assert article.language == 'en'
            assert article.summary_language == 'en'
            assert article.id is not None
            assert isinstance(article.created_at, datetime)
    
    def test_create_article_with_custom_sentiment_and_language(self, test_app):
        """Test creating an article with custom sentiment and language values."""
        with test_app.app_context():
            article = NewsArticle(
                title="Artículo de Prueba",
                url="https://ejemplo.com/prueba",
                summary="Resumen de prueba",
                full_content="Contenido de prueba",
                topic="tecnología",
                session_id="test_session_456",
                sentiment="positive",
                language="es",
                summary_language="en"
            )
            
            db.session.add(article)
            db.session.commit()
            
            # Verify custom values
            assert article.sentiment == 'positive'
            assert article.language == 'es'
            assert article.summary_language == 'en'
            assert article.title == "Artículo de Prueba"
    
    def test_sentiment_values(self, test_app):
        """Test different sentiment values."""
        with test_app.app_context():
            sentiments = ['positive', 'negative', 'neutral']
            
            for i, sentiment in enumerate(sentiments):
                article = NewsArticle(
                    title=f"Test Article {i}",
                    url=f"https://example.com/test{i}",
                    summary=f"Test summary {i}",
                    full_content=f"Test content {i}",
                    topic="test",
                    session_id=f"test_session_{i}",
                    sentiment=sentiment
                )
                
                db.session.add(article)
            
            db.session.commit()
            
            # Verify all articles were created with correct sentiments
            articles = NewsArticle.query.all()
            assert len(articles) == 3
            
            retrieved_sentiments = [article.sentiment for article in articles]
            assert set(retrieved_sentiments) == set(sentiments)
    
    def test_language_codes(self, test_app):
        """Test different language codes."""
        with test_app.app_context():
            languages = [
                ('en', 'English'),
                ('es', 'Spanish'),
                ('fr', 'French'),
                ('de', 'German'),
                ('zh', 'Chinese')
            ]
            
            for i, (lang_code, lang_name) in enumerate(languages):
                article = NewsArticle(
                    title=f"Test Article in {lang_name}",
                    url=f"https://example.com/test{i}",
                    summary=f"Test summary in {lang_name}",
                    full_content=f"Test content in {lang_name}",
                    topic="multilingual",
                    session_id=f"test_session_{i}",
                    language=lang_code,
                    summary_language='en'  # All summaries in English
                )
                
                db.session.add(article)
            
            db.session.commit()
            
            # Verify all articles were created with correct languages
            articles = NewsArticle.query.all()
            assert len(articles) == 5
            
            retrieved_languages = [article.language for article in articles]
            expected_languages = [lang[0] for lang in languages]
            assert set(retrieved_languages) == set(expected_languages)
            
            # All summaries should be in English
            summary_languages = [article.summary_language for article in articles]
            assert all(lang == 'en' for lang in summary_languages)
    
    def test_query_by_sentiment(self, test_app):
        """Test querying articles by sentiment."""
        with test_app.app_context():
            # Create articles with different sentiments
            articles_data = [
                ("Positive News", "positive"),
                ("Negative News", "negative"),
                ("Neutral News", "neutral"),
                ("Another Positive", "positive")
            ]
            
            for title, sentiment in articles_data:
                article = NewsArticle(
                    title=title,
                    url=f"https://example.com/{title.lower().replace(' ', '-')}",
                    summary=f"Summary for {title}",
                    full_content=f"Content for {title}",
                    topic="news",
                    session_id="test_session",
                    sentiment=sentiment
                )
                db.session.add(article)
            
            db.session.commit()
            
            # Query by sentiment
            positive_articles = NewsArticle.query.filter_by(sentiment='positive').all()
            negative_articles = NewsArticle.query.filter_by(sentiment='negative').all()
            neutral_articles = NewsArticle.query.filter_by(sentiment='neutral').all()
            
            assert len(positive_articles) == 2
            assert len(negative_articles) == 1
            assert len(neutral_articles) == 1
            
            # Verify titles
            positive_titles = [article.title for article in positive_articles]
            assert "Positive News" in positive_titles
            assert "Another Positive" in positive_titles
    
    def test_query_by_language(self, test_app):
        """Test querying articles by language."""
        with test_app.app_context():
            # Create articles in different languages
            articles_data = [
                ("English Article", "en"),
                ("Spanish Article", "es"),
                ("French Article", "fr"),
                ("Another English", "en")
            ]
            
            for title, language in articles_data:
                article = NewsArticle(
                    title=title,
                    url=f"https://example.com/{title.lower().replace(' ', '-')}",
                    summary=f"Summary for {title}",
                    full_content=f"Content for {title}",
                    topic="multilingual",
                    session_id="test_session",
                    language=language
                )
                db.session.add(article)
            
            db.session.commit()
            
            # Query by language
            english_articles = NewsArticle.query.filter_by(language='en').all()
            spanish_articles = NewsArticle.query.filter_by(language='es').all()
            french_articles = NewsArticle.query.filter_by(language='fr').all()
            
            assert len(english_articles) == 2
            assert len(spanish_articles) == 1
            assert len(french_articles) == 1
            
            # Verify titles
            english_titles = [article.title for article in english_articles]
            assert "English Article" in english_titles
            assert "Another English" in english_titles


class TestConversationSessionModel:
    """Test cases for the ConversationSession model (ensure it still works)."""
    
    def test_conversation_session_unchanged(self, test_app):
        """Test that ConversationSession model still works as expected."""
        with test_app.app_context():
            session = ConversationSession(
                session_id="test_session_123"
            )
            
            # Test topics functionality
            test_topics = ["technology", "science", "politics"]
            session.set_topics(test_topics)
            
            # Test state functionality
            test_state = {"current_step": "gathering_topics", "user_preferences": {"language": "en"}}
            session.set_state(test_state)
            
            db.session.add(session)
            db.session.commit()
            
            # Retrieve and verify
            retrieved_session = ConversationSession.query.filter_by(session_id="test_session_123").first()
            assert retrieved_session is not None
            assert retrieved_session.get_topics() == test_topics
            assert retrieved_session.get_state() == test_state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])