import pytest
import json
from unittest.mock import patch, MagicMock
from app import app, db
from models import ConversationSession
import uuid

class TestSearchAPI:
    """Test cases for the enhanced /search API endpoint"""
    
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
    
    def test_search_endpoint_exists(self, client):
        """Test that the /search endpoint exists and accepts POST requests"""
        response = client.post('/search', json={'query': 'test'})
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_search_requires_json_body(self, client):
        """Test that search endpoint requires JSON body"""
        response = client.post('/search')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Request body is required' in data['error']
    
    def test_search_requires_query_parameter(self, client):
        """Test that search endpoint requires query parameter"""
        response = client.post('/search', json={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Query parameter is required' in data['error']
    
    def test_search_rejects_empty_query(self, client):
        """Test that search endpoint rejects empty query"""
        response = client.post('/search', json={'query': '   '})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Query parameter is required' in data['error']
    
    @patch('routes.news_service.search_news')
    def test_search_with_valid_query(self, mock_search, client, mock_session):
        """Test search with valid query returns articles with sentiment"""
        # Mock news service response
        mock_articles = [
            {
                'title': 'Test Article 1',
                'url': 'https://example.com/1',
                'body': 'This is a positive news article about technology advancement.',
                'summary': 'Technology advances positively.',
                'sentiment': 'positive',
                'date': '2024-01-01',
                'source': 'Test Source'
            },
            {
                'title': 'Test Article 2', 
                'url': 'https://example.com/2',
                'body': 'This is concerning news about economic downturn.',
                'summary': 'Economic concerns arise.',
                'sentiment': 'negative',
                'date': '2024-01-02',
                'source': 'News Source'
            }
        ]
        mock_search.return_value = mock_articles
        
        response = client.post('/search', json={'query': 'technology'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['query'] == 'technology'
        assert data['language'] == 'en'  # Default language
        assert data['total_results'] == 2
        assert len(data['articles']) == 2
        
        # Check that articles include sentiment data
        for article in data['articles']:
            assert 'sentiment' in article
            assert article['sentiment'] in ['positive', 'negative', 'neutral']
            assert 'title' in article
            assert 'url' in article
            assert 'summary' in article
            assert 'language' in article
    
    @patch('routes.news_service.search_news')
    def test_search_with_language_parameter(self, mock_search, client, mock_session):
        """Test search with language parameter"""
        mock_articles = [{
            'title': 'हिंदी समाचार',
            'url': 'https://example.com/hindi',
            'body': 'यह एक सकारात्मक समाचार है।',
            'summary': 'सकारात्मक समाचार।',
            'sentiment': 'positive',
            'date': '2024-01-01',
            'source': 'हिंदी स्रोत'
        }]
        mock_search.return_value = mock_articles
        
        response = client.post('/search', json={
            'query': 'technology',
            'language': 'hi'
        })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['language'] == 'hi'
        assert len(data['articles']) == 1
        assert data['articles'][0]['language'] == 'hi'
    
    @patch('routes.news_service.search_news')
    def test_search_with_invalid_language_falls_back(self, mock_search, client, mock_session):
        """Test search with invalid language falls back to supported language"""
        mock_articles = [{
            'title': 'Test Article',
            'url': 'https://example.com/test',
            'body': 'Test content.',
            'summary': 'Test summary.',
            'sentiment': 'neutral',
            'date': '2024-01-01',
            'source': 'Test Source'
        }]
        mock_search.return_value = mock_articles
        
        response = client.post('/search', json={
            'query': 'technology',
            'language': 'invalid_lang'
        })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['language'] == 'en'  # Should fallback to English
    
    @patch('routes.news_service.search_news')
    def test_search_with_max_results_parameter(self, mock_search, client, mock_session):
        """Test search with max_results parameter"""
        mock_articles = [{'title': f'Article {i}', 'url': f'https://example.com/{i}', 
                         'body': 'Content', 'summary': 'Summary', 'sentiment': 'neutral',
                         'date': '2024-01-01', 'source': 'Source'} for i in range(3)]
        mock_search.return_value = mock_articles
        
        response = client.post('/search', json={
            'query': 'technology',
            'max_results': 3
        })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['total_results'] == 3
        
        # Verify mock was called with correct max_results
        mock_search.assert_called_once_with('technology', 3, 'en')
    
    @patch('routes.news_service.search_news')
    def test_search_validates_max_results_bounds(self, mock_search, client, mock_session):
        """Test search validates max_results parameter bounds"""
        mock_articles = []
        mock_search.return_value = mock_articles
        
        # Test with too high max_results
        response = client.post('/search', json={
            'query': 'technology',
            'max_results': 100
        })
        assert response.status_code == 200
        # Should be clamped to 5 (default)
        mock_search.assert_called_with('technology', 5, 'en')
        
        mock_search.reset_mock()
        
        # Test with negative max_results
        response = client.post('/search', json={
            'query': 'technology',
            'max_results': -1
        })
        assert response.status_code == 200
        # Should be clamped to 5 (default)
        mock_search.assert_called_with('technology', 5, 'en')
    
    @patch('routes.news_service.search_news')
    @patch('routes.news_service.generate_summary_with_sentiment')
    def test_search_enhances_articles_without_sentiment(self, mock_sentiment, mock_search, client, mock_session):
        """Test search enhances articles that don't have sentiment data"""
        # Mock article without sentiment
        mock_articles = [{
            'title': 'Test Article',
            'url': 'https://example.com/test',
            'body': 'Test content without sentiment.',
            'summary': 'Test summary.',
            'date': '2024-01-01',
            'source': 'Test Source'
            # No sentiment field
        }]
        mock_search.return_value = mock_articles
        
        # Mock sentiment analysis response
        mock_sentiment.return_value = {
            'summary': 'Enhanced summary.',
            'sentiment': 'positive'
        }
        
        response = client.post('/search', json={'query': 'technology'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['articles']) == 1
        
        article = data['articles'][0]
        assert article['sentiment'] == 'positive'
        assert article['summary'] == 'Enhanced summary.'
        
        # Verify sentiment analysis was called
        mock_sentiment.assert_called_once()
    
    @patch('routes.news_service.search_news')
    def test_search_handles_news_service_error(self, mock_search, client, mock_session):
        """Test search handles news service errors gracefully"""
        mock_search.side_effect = Exception("News service error")
        
        response = client.post('/search', json={'query': 'technology'})
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Search failed' in data['error']
        assert data['query'] == 'technology'
        assert data['language'] == 'en'
    
    @patch('routes.news_service.search_news')
    @patch('routes.news_service.generate_summary_with_sentiment')
    def test_search_handles_sentiment_enhancement_error(self, mock_sentiment, mock_search, client, mock_session):
        """Test search handles sentiment enhancement errors gracefully"""
        # Mock article without sentiment
        mock_articles = [{
            'title': 'Test Article',
            'url': 'https://example.com/test',
            'body': 'Test content.',
            'summary': 'Test summary.',
            'date': '2024-01-01',
            'source': 'Test Source'
        }]
        mock_search.return_value = mock_articles
        
        # Mock sentiment analysis to fail
        mock_sentiment.side_effect = Exception("Sentiment analysis error")
        
        response = client.post('/search', json={'query': 'technology'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['articles']) == 1
        
        # Should fallback to neutral sentiment
        article = data['articles'][0]
        assert article['sentiment'] == 'neutral'
    
    def test_search_method_not_allowed(self, client):
        """Test that GET method is not allowed on /search endpoint"""
        response = client.get('/search')
        assert response.status_code == 405  # Method Not Allowed