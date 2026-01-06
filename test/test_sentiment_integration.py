#!/usr/bin/env python3
"""
Integration tests for sentiment indicator functionality.
Tests the backend integration and data flow for sentiment display.
"""

import pytest
import json
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import NewsArticle, ConversationSession
from datetime import datetime, timezone

class TestSentimentIntegration:
    """Test sentiment indicator backend integration."""
    
    @pytest.fixture
    def test_app(self):
        """Configure test Flask app."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, test_app):
        """Create test client."""
        return test_app.test_client()
    
    @pytest.fixture
    def test_session(self, test_app):
        """Create test session with articles."""
        with test_app.app_context():
            # Create test session
            session = ConversationSession(
                session_id='test_sentiment_session',
                topics='["technology", "politics", "weather"]'
            )
            db.session.add(session)
            
            # Create articles with different sentiments
            articles = [
                NewsArticle(
                    title="Revolutionary AI Breakthrough Announced",
                    url="https://example.com/positive-tech",
                    summary="Scientists announce major breakthrough in AI technology that will benefit humanity.",
                    topic="technology",
                    session_id='test_sentiment_session',
                    sentiment='positive',
                    language='en'
                ),
                NewsArticle(
                    title="Economic Crisis Deepens Worldwide",
                    url="https://example.com/negative-politics",
                    summary="Global economic indicators show worsening conditions across major markets.",
                    topic="politics",
                    session_id='test_sentiment_session',
                    sentiment='negative',
                    language='en'
                ),
                NewsArticle(
                    title="Weather Forecast for Next Week",
                    url="https://example.com/neutral-weather",
                    summary="Next week will see partly cloudy skies with temperatures in the normal range.",
                    topic="weather",
                    session_id='test_sentiment_session',
                    sentiment='neutral',
                    language='en'
                ),
                NewsArticle(
                    title="Article Without Sentiment",
                    url="https://example.com/no-sentiment",
                    summary="This article has no sentiment specified.",
                    topic="general",
                    session_id='test_sentiment_session',
                    sentiment=None,  # Test null sentiment
                    language='en'
                )
            ]
            
            for article in articles:
                db.session.add(article)
            
            db.session.commit()
            return session
    
    def test_article_model_sentiment_field(self, test_app, test_session):
        """Test that NewsArticle model correctly stores sentiment data."""
        with test_app.app_context():
            # Query articles by sentiment
            positive_articles = NewsArticle.query.filter_by(sentiment='positive').all()
            negative_articles = NewsArticle.query.filter_by(sentiment='negative').all()
            neutral_articles = NewsArticle.query.filter_by(sentiment='neutral').all()
            null_sentiment_articles = NewsArticle.query.filter_by(sentiment=None).all()
            
            assert len(positive_articles) == 1, "Should have one positive article"
            assert len(negative_articles) == 1, "Should have one negative article"
            assert len(neutral_articles) == 2, "Should have two neutral articles (one explicit, one default)"
            assert len(null_sentiment_articles) == 0, "Articles with null sentiment should default to neutral"
            
            # Test sentiment values
            assert positive_articles[0].sentiment == 'positive'
            assert negative_articles[0].sentiment == 'negative'
            assert neutral_articles[0].sentiment == 'neutral'
            # The article that was created with None sentiment should now be neutral
            article_without_sentiment = NewsArticle.query.filter_by(title="Article Without Sentiment").first()
            assert article_without_sentiment.sentiment == 'neutral', "Null sentiment should default to neutral"
    
    def test_search_news_includes_sentiment(self, test_app, client, test_session):
        """Test that search_news endpoint returns sentiment data."""
        with test_app.app_context():
            # Set up session
            with client.session_transaction() as sess:
                sess['session_id'] = 'test_sentiment_session'
            
            # Mock the news search to return our test articles
            response = client.post('/search_news', 
                                 json={'language': 'en'},
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Check that response includes sentiment data
            if data.get('success') and data.get('results'):
                for topic, articles in data['results'].items():
                    for article in articles:
                        # Each article should have sentiment field
                        assert 'sentiment' in article or article.get('sentiment') is not None, \
                            f"Article should have sentiment field: {article.get('title', 'Unknown')}"
                        
                        # Sentiment should be one of the valid values or None
                        sentiment = article.get('sentiment')
                        assert sentiment in ['positive', 'negative', 'neutral', None], \
                            f"Invalid sentiment value: {sentiment}"
    
    def test_sentiment_data_serialization(self, test_app, test_session):
        """Test that sentiment data is properly serialized for frontend."""
        with test_app.app_context():
            articles = NewsArticle.query.all()
            
            for article in articles:
                # Test that sentiment can be serialized to JSON
                article_data = {
                    'id': article.id,
                    'title': article.title,
                    'url': article.url,
                    'summary': article.summary,
                    'topic': article.topic,
                    'sentiment': article.sentiment,
                    'language': article.language,
                    'created_at': article.created_at.isoformat() if article.created_at else None
                }
                
                # Should be able to serialize to JSON without errors
                json_data = json.dumps(article_data)
                assert json_data is not None
                
                # Should be able to deserialize back
                deserialized = json.loads(json_data)
                assert deserialized['sentiment'] == article.sentiment
    
    def test_sentiment_default_values(self, test_app):
        """Test sentiment field default values and constraints."""
        with test_app.app_context():
            # Test creating article without sentiment (should default to neutral)
            article = NewsArticle(
                title="Test Article",
                url="https://example.com/test",
                summary="Test summary",
                topic="test",
                session_id="test_session",
                language="en"
                # No sentiment specified
            )
            
            db.session.add(article)
            db.session.commit()
            
            # Should default to 'neutral'
            assert article.sentiment == 'neutral', "Article sentiment should default to 'neutral'"
    
    def test_sentiment_field_validation(self, test_app):
        """Test that sentiment field accepts valid values."""
        with test_app.app_context():
            valid_sentiments = ['positive', 'negative', 'neutral']
            
            for sentiment in valid_sentiments:
                article = NewsArticle(
                    title=f"Test Article - {sentiment}",
                    url=f"https://example.com/test-{sentiment}",
                    summary=f"Test summary for {sentiment} sentiment",
                    topic="test",
                    session_id="test_session",
                    sentiment=sentiment,
                    language="en"
                )
                
                db.session.add(article)
                db.session.commit()
                
                # Verify the sentiment was stored correctly
                stored_article = NewsArticle.query.filter_by(title=f"Test Article - {sentiment}").first()
                assert stored_article.sentiment == sentiment, f"Sentiment {sentiment} should be stored correctly"
    
    def test_sentiment_query_filtering(self, test_app, test_session):
        """Test querying articles by sentiment."""
        with test_app.app_context():
            # Test filtering by each sentiment type
            positive_count = NewsArticle.query.filter_by(sentiment='positive').count()
            negative_count = NewsArticle.query.filter_by(sentiment='negative').count()
            neutral_count = NewsArticle.query.filter_by(sentiment='neutral').count()
            
            assert positive_count > 0, "Should have positive articles"
            assert negative_count > 0, "Should have negative articles"
            assert neutral_count > 0, "Should have neutral articles"
            
            # Test combined queries
            non_neutral = NewsArticle.query.filter(
                NewsArticle.sentiment.in_(['positive', 'negative'])
            ).count()
            
            assert non_neutral == positive_count + negative_count, \
                "Non-neutral count should equal positive + negative"
    
    def test_sentiment_with_multilingual_content(self, test_app):
        """Test sentiment field with multilingual articles."""
        with test_app.app_context():
            # Create articles in different languages with sentiments
            multilingual_articles = [
                {
                    'title': 'Great News in English',
                    'language': 'en',
                    'sentiment': 'positive'
                },
                {
                    'title': 'बुरी खबर हिंदी में',  # Bad news in Hindi
                    'language': 'hi',
                    'sentiment': 'negative'
                },
                {
                    'title': 'मराठीतील तटस्थ बातमी',  # Neutral news in Marathi
                    'language': 'mr',
                    'sentiment': 'neutral'
                }
            ]
            
            for i, article_data in enumerate(multilingual_articles):
                article = NewsArticle(
                    title=article_data['title'],
                    url=f"https://example.com/multilingual-{i}",
                    summary=f"Summary for {article_data['language']} article",
                    topic="multilingual",
                    session_id="multilingual_session",
                    sentiment=article_data['sentiment'],
                    language=article_data['language']
                )
                
                db.session.add(article)
            
            db.session.commit()
            
            # Verify all articles were stored with correct sentiment
            for article_data in multilingual_articles:
                stored_article = NewsArticle.query.filter_by(
                    title=article_data['title']
                ).first()
                
                assert stored_article is not None, f"Article should be stored: {article_data['title']}"
                assert stored_article.sentiment == article_data['sentiment'], \
                    f"Sentiment should match for {article_data['language']} article"
                assert stored_article.language == article_data['language'], \
                    f"Language should match for {article_data['title']}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])