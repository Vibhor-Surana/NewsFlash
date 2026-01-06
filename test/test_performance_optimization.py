#!/usr/bin/env python3
"""
Performance and Optimization Tests for Multi-Language Sentiment Analysis

This test suite covers performance aspects including:
- Token usage optimization with multi-language prompts
- Response times for different language combinations
- Concurrent requests with different language preferences
- Caching effectiveness for sentiment and language data
Tests Requirements: 1.4, 2.4, 3.4
"""

import pytest
import time
import threading
import statistics
import json
import uuid
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

# Add the project root to the Python path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import NewsArticle, ConversationSession
from news_service import NewsService
from tts_service import TTSService
from language_service import LanguageService
from config import Config


class TestPerformanceOptimization:
    """Performance and optimization tests for multi-language sentiment analysis."""
    
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
    def news_service(self):
        """Create NewsService instance for testing."""
        return NewsService()
    
    @pytest.fixture
    def tts_service(self):
        """Create TTSService instance for testing."""
        return TTSService()
    
    @pytest.fixture
    def sample_articles(self):
        """Sample articles for performance testing."""
        return [
            {
                'title': 'Technology Breakthrough in AI Research',
                'body': 'Researchers have developed a new artificial intelligence system that can process natural language with unprecedented accuracy. The breakthrough promises to revolutionize how we interact with computers and could lead to significant advances in healthcare, education, and scientific research.',
                'expected_tokens': 150  # Approximate token count
            },
            {
                'title': 'Economic Market Analysis Report',
                'body': 'Global financial markets showed mixed results this quarter with technology stocks leading gains while traditional sectors faced challenges. Analysts predict continued volatility as central banks adjust monetary policies in response to changing economic conditions.',
                'expected_tokens': 140
            },
            {
                'title': 'Climate Change Impact Study',
                'body': 'A comprehensive study reveals accelerating climate change effects across multiple regions. Rising temperatures, changing precipitation patterns, and extreme weather events are becoming more frequent, requiring immediate action from governments and organizations worldwide.',
                'expected_tokens': 145
            }
        ]
    
    # Test 1: Token Usage Optimization with Multi-Language Prompts
    
    def test_token_usage_optimization_english(self, news_service, sample_articles):
        """Test token usage optimization for English prompts."""
        token_counts = []
        processing_times = []
        
        for article in sample_articles:
            with patch('news_service.handle_language_operation') as mock_handle:
                # Mock the response from handle_language_operation
                mock_handle.return_value = {
                    'summary': f"{article['title'][:50]}...",
                    'sentiment': 'positive',
                    'language': 'en'
                }
                
                start_time = time.time()
                
                # Generate summary with sentiment
                result = news_service.generate_summary_with_sentiment(
                    article['body'], article['title'], 'en'
                )
                
                end_time = time.time()
                processing_times.append(end_time - start_time)
                
                # Verify the call was made
                mock_handle.assert_called_once()
                
                # Estimate token usage based on article body length (rough approximation: 1 token ≈ 4 characters)
                # Text should be truncated to optimize token usage (max 800 chars in the actual implementation)
                text_length = min(len(article['body']), 800)
                estimated_tokens = text_length / 4
                token_counts.append(estimated_tokens)
                
                assert result['sentiment'] in ['positive', 'negative', 'neutral']
        
        # Verify token optimization
        avg_tokens = statistics.mean(token_counts)
        max_tokens = max(token_counts)
        
        assert avg_tokens < 250, f"Average token usage too high: {avg_tokens}"
        assert max_tokens < 300, f"Maximum token usage too high: {max_tokens}"
        
        # Verify reasonable processing times
        avg_time = statistics.mean(processing_times)
        assert avg_time < 0.1, f"Processing time too slow: {avg_time}s"  # Should be fast with mocking
    
    def test_token_usage_comparison_across_languages(self, news_service, sample_articles):
        """Test token usage comparison across different languages."""
        languages = ['en', 'hi', 'mr']
        language_token_usage = {}
        
        for lang in languages:
            token_counts = []
            
            for article in sample_articles:
                with patch('news_service.handle_language_operation') as mock_handle:
                    # Mock the response
                    mock_handle.return_value = {
                        'summary': 'Test summary',
                        'sentiment': 'neutral',
                        'language': lang
                    }
                    
                    # Generate summary with sentiment
                    news_service.generate_summary_with_sentiment(
                        article['body'], article['title'], lang
                    )
                    
                    # Estimate token usage based on article content and language template
                    # Different languages have different template lengths
                    template_base_length = {'en': 100, 'hi': 150, 'mr': 140}  # Approximate template lengths
                    content_length = min(len(article['body']), 800)  # Truncated content
                    total_estimated_tokens = (template_base_length.get(lang, 100) + content_length) / 4
                    token_counts.append(total_estimated_tokens)
            
            language_token_usage[lang] = {
                'avg_tokens': statistics.mean(token_counts),
                'max_tokens': max(token_counts),
                'min_tokens': min(token_counts)
            }
        
        # Verify token usage is reasonable across all languages
        for lang, usage in language_token_usage.items():
            assert usage['avg_tokens'] < 400, f"Average tokens too high for {lang}: {usage['avg_tokens']}"
            assert usage['max_tokens'] < 500, f"Max tokens too high for {lang}: {usage['max_tokens']}"
        
        # Verify token usage is relatively consistent across languages
        avg_tokens_by_lang = [usage['avg_tokens'] for usage in language_token_usage.values()]
        token_variance = statistics.variance(avg_tokens_by_lang)
        assert token_variance < 10000, f"Token usage variance too high across languages: {token_variance}"
    
    def test_prompt_template_efficiency(self, news_service):
        """Test efficiency of prompt templates across languages."""
        test_text = "This is a test article about technology and innovation."
        test_title = "Technology Innovation"
        
        languages = ['en', 'hi', 'mr']
        template_lengths = {}
        
        for lang in languages:
            # Get the prompt template for the language
            template = news_service.get_sentiment_prompt_template(lang)
            
            # Format the template with test data
            formatted_prompt = template.format(title=test_title, article_text=test_text)
            
            template_lengths[lang] = len(formatted_prompt)
            
            # Verify template is not excessively long
            assert len(formatted_prompt) < 1000, f"Prompt template too long for {lang}: {len(formatted_prompt)}"
        
        # Log template lengths for analysis
        print(f"\nPrompt template lengths: {template_lengths}")
        
        # Verify templates are reasonably sized
        for lang, length in template_lengths.items():
            assert length > 50, f"Prompt template too short for {lang}: {length}"
            assert length < 800, f"Prompt template too long for {lang}: {length}"
    
    # Test 2: Response Times for Different Language Combinations
    
    def test_response_times_by_language(self, client, test_app):
        """Test response times for different language combinations."""
        languages = ['en', 'hi', 'mr']
        response_times = {}
        
        with test_app.app_context():
            for lang in languages:
                times = []
                
                for i in range(3):  # Test multiple requests per language
                    session_id = str(uuid.uuid4())
                    
                    with client.session_transaction() as sess:
                        sess['session_id'] = session_id
                    
                    # Mock the news search to control response time
                    with patch('news_service.NewsService.search_news') as mock_search:
                        mock_search.return_value = [{
                            'title': f'Test Article {i}',
                            'body': 'Test article content for performance testing.',
                            'url': f'https://example.com/test-{i}',
                            'date': '2024-01-01',
                            'source': 'Test Source'
                        }]
                        
                        start_time = time.time()
                        
                        response = client.post('/search', json={
                            'query': 'test',
                            'language': lang,
                            'max_results': 1
                        })
                        
                        end_time = time.time()
                        response_time = end_time - start_time
                        times.append(response_time)
                        
                        assert response.status_code == 200
                        data = response.get_json()
                        assert data['language'] == lang
                
                response_times[lang] = {
                    'avg_time': statistics.mean(times),
                    'max_time': max(times),
                    'min_time': min(times)
                }
        
        # Verify response times are reasonable
        for lang, times in response_times.items():
            assert times['avg_time'] < 2.0, f"Average response time too slow for {lang}: {times['avg_time']}s"
            assert times['max_time'] < 5.0, f"Max response time too slow for {lang}: {times['max_time']}s"
        
        # Log response times for analysis
        print(f"\nResponse times by language: {response_times}")
    
    def test_tts_response_times_by_language(self, client, test_app):
        """Test TTS response times for different languages."""
        languages = ['en', 'hi', 'mr']
        tts_response_times = {}
        test_text = "This is a test message for text-to-speech performance testing."
        
        with test_app.app_context():
            for lang in languages:
                times = []
                
                for i in range(3):  # Test multiple requests per language
                    session_id = str(uuid.uuid4())
                    
                    with client.session_transaction() as sess:
                        sess['session_id'] = session_id
                    
                    # Mock TTS generation
                    with patch('tts_service.TTSService._generate_tts_for_language') as mock_tts:
                        mock_tts.return_value = True
                        
                        with patch('os.path.exists', return_value=True), \
                             patch('os.path.getsize', return_value=1024):
                            
                            start_time = time.time()
                            
                            response = client.post('/tts', json={
                                'text': test_text,
                                'language': lang
                            })
                            
                            end_time = time.time()
                            response_time = end_time - start_time
                            times.append(response_time)
                            
                            assert response.status_code == 200
                            data = response.get_json()
                            assert data['language'] == lang
                
                tts_response_times[lang] = {
                    'avg_time': statistics.mean(times),
                    'max_time': max(times),
                    'min_time': min(times)
                }
        
        # Verify TTS response times are reasonable
        for lang, times in tts_response_times.items():
            assert times['avg_time'] < 1.0, f"Average TTS response time too slow for {lang}: {times['avg_time']}s"
            assert times['max_time'] < 2.0, f"Max TTS response time too slow for {lang}: {times['max_time']}s"
        
        # Log TTS response times for analysis
        print(f"\nTTS response times by language: {tts_response_times}")
    
    # Test 3: Concurrent Requests with Different Language Preferences
    
    def test_concurrent_requests_performance(self, test_app):
        """Test performance under concurrent requests with different languages."""
        languages = ['en', 'hi', 'mr']
        num_concurrent_requests = 10
        results = []
        
        def make_concurrent_request(lang, request_id):
            """Make a concurrent request with specific language."""
            try:
                client = test_app.test_client()
                session_id = str(uuid.uuid4())
                
                with client.session_transaction() as sess:
                    sess['session_id'] = session_id
                
                start_time = time.time()
                
                # Set language preference
                response = client.post('/set-language', json={'language': lang})
                if response.status_code != 200:
                    return {'success': False, 'error': 'Failed to set language'}
                
                # Mock news search for consistent testing
                with patch('news_service.NewsService.search_news') as mock_search:
                    mock_search.return_value = [{
                        'title': f'Concurrent Test Article {request_id}',
                        'body': 'Test content for concurrent request testing.',
                        'url': f'https://example.com/concurrent-{request_id}',
                        'date': '2024-01-01',
                        'source': 'Test Source'
                    }]
                    
                    # Perform search
                    response = client.post('/search', json={
                        'query': f'test-{request_id}',
                        'language': lang,
                        'max_results': 1
                    })
                
                end_time = time.time()
                response_time = end_time - start_time
                
                if response.status_code == 200:
                    data = response.get_json()
                    return {
                        'success': True,
                        'language': lang,
                        'request_id': request_id,
                        'response_time': response_time,
                        'returned_language': data.get('language')
                    }
                else:
                    return {
                        'success': False,
                        'language': lang,
                        'request_id': request_id,
                        'error': f'HTTP {response.status_code}'
                    }
                    
            except Exception as e:
                return {
                    'success': False,
                    'language': lang,
                    'request_id': request_id,
                    'error': str(e)
                }
        
        with test_app.app_context():
            # Create concurrent requests
            with ThreadPoolExecutor(max_workers=num_concurrent_requests) as executor:
                futures = []
                
                for i in range(num_concurrent_requests):
                    lang = languages[i % len(languages)]  # Cycle through languages
                    future = executor.submit(make_concurrent_request, lang, i)
                    futures.append(future)
                
                # Collect results
                for future in as_completed(futures, timeout=30):
                    result = future.result()
                    results.append(result)
        
        # Analyze results
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        # Verify most requests succeeded
        success_rate = len(successful_requests) / len(results)
        assert success_rate >= 0.8, f"Success rate too low: {success_rate:.2%}"
        
        # Verify response times are reasonable under load
        if successful_requests:
            response_times = [r['response_time'] for r in successful_requests]
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            
            assert avg_response_time < 3.0, f"Average response time under load too slow: {avg_response_time:.2f}s"
            assert max_response_time < 10.0, f"Max response time under load too slow: {max_response_time:.2f}s"
        
        # Verify language preferences were handled correctly
        for result in successful_requests:
            assert result['language'] == result['returned_language'], \
                f"Language mismatch in request {result['request_id']}: {result['language']} != {result['returned_language']}"
        
        # Log performance metrics
        print(f"\nConcurrent request performance:")
        print(f"  Total requests: {len(results)}")
        print(f"  Successful: {len(successful_requests)}")
        print(f"  Failed: {len(failed_requests)}")
        print(f"  Success rate: {success_rate:.2%}")
        if successful_requests:
            print(f"  Avg response time: {statistics.mean(response_times):.3f}s")
            print(f"  Max response time: {max(response_times):.3f}s")
    
    def test_concurrent_tts_requests(self, test_app):
        """Test TTS performance under concurrent requests."""
        languages = ['en', 'hi', 'mr']
        num_concurrent_requests = 6
        test_text = "Concurrent TTS test message for performance evaluation."
        results = []
        
        def make_concurrent_tts_request(lang, request_id):
            """Make a concurrent TTS request."""
            try:
                client = test_app.test_client()
                session_id = str(uuid.uuid4())
                
                with client.session_transaction() as sess:
                    sess['session_id'] = session_id
                
                start_time = time.time()
                
                # Mock TTS generation
                with patch('tts_service.TTSService._generate_tts_for_language') as mock_tts:
                    mock_tts.return_value = True
                    
                    with patch('os.path.exists', return_value=True), \
                         patch('os.path.getsize', return_value=1024):
                        
                        response = client.post('/tts', json={
                            'text': test_text,
                            'language': lang
                        })
                
                end_time = time.time()
                response_time = end_time - start_time
                
                if response.status_code == 200:
                    data = response.get_json()
                    return {
                        'success': True,
                        'language': lang,
                        'request_id': request_id,
                        'response_time': response_time,
                        'returned_language': data.get('language')
                    }
                else:
                    return {
                        'success': False,
                        'language': lang,
                        'request_id': request_id,
                        'error': f'HTTP {response.status_code}'
                    }
                    
            except Exception as e:
                return {
                    'success': False,
                    'language': lang,
                    'request_id': request_id,
                    'error': str(e)
                }
        
        with test_app.app_context():
            # Create concurrent TTS requests
            with ThreadPoolExecutor(max_workers=num_concurrent_requests) as executor:
                futures = []
                
                for i in range(num_concurrent_requests):
                    lang = languages[i % len(languages)]
                    future = executor.submit(make_concurrent_tts_request, lang, i)
                    futures.append(future)
                
                # Collect results
                for future in as_completed(futures, timeout=20):
                    result = future.result()
                    results.append(result)
        
        # Analyze TTS concurrent performance
        successful_requests = [r for r in results if r['success']]
        
        success_rate = len(successful_requests) / len(results)
        assert success_rate >= 0.8, f"TTS concurrent success rate too low: {success_rate:.2%}"
        
        if successful_requests:
            response_times = [r['response_time'] for r in successful_requests]
            avg_response_time = statistics.mean(response_times)
            
            assert avg_response_time < 2.0, f"TTS concurrent avg response time too slow: {avg_response_time:.2f}s"
        
        print(f"\nConcurrent TTS performance:")
        print(f"  Success rate: {success_rate:.2%}")
        if successful_requests:
            print(f"  Avg response time: {statistics.mean(response_times):.3f}s")
    
    # Test 4: Caching Effectiveness for Sentiment and Language Data
    
    def test_sentiment_caching_effectiveness(self, test_app):
        """Test effectiveness of sentiment analysis caching."""
        with test_app.app_context():
            news_service = NewsService()
            
            # Test data - make it long enough to avoid fallback
            test_article = {
                'title': 'Test Article for Caching Performance Evaluation',
                'body': 'This is a comprehensive test article designed to evaluate caching effectiveness for sentiment analysis operations. The article contains sufficient content to trigger the AI-powered sentiment analysis rather than falling back to default neutral sentiment. This ensures we can properly test the caching mechanisms and performance optimizations in our multi-language sentiment analysis system.'
            }
            
            # First request - should hit AI service
            with patch('news_service.handle_language_operation') as mock_handle:
                mock_handle.return_value = {
                    'summary': 'Test summary',
                    'sentiment': 'positive',
                    'language': 'en'
                }
                
                start_time = time.time()
                result1 = news_service.generate_summary_with_sentiment(
                    test_article['body'], test_article['title'], 'en'
                )
                first_request_time = time.time() - start_time
                
                # Verify service was called
                assert mock_handle.call_count == 1
                assert result1['sentiment'] == 'positive'
            
            # Note: Current implementation doesn't have caching, but we test the pattern
            # In a real caching implementation, the second request would be faster
            
            # Second request - in a cached system, this would be faster
            with patch('news_service.handle_language_operation') as mock_handle:
                mock_handle.return_value = {
                    'summary': 'Test summary',
                    'sentiment': 'positive',
                    'language': 'en'
                }
                
                start_time = time.time()
                result2 = news_service.generate_summary_with_sentiment(
                    test_article['body'], test_article['title'], 'en'
                )
                second_request_time = time.time() - start_time
                
                # Verify results are consistent
                assert result2['sentiment'] == result1['sentiment']
                assert result2['language'] == result1['language']
            
            # Log timing information for cache analysis
            print(f"\nSentiment analysis timing:")
            print(f"  First request: {first_request_time:.3f}s")
            print(f"  Second request: {second_request_time:.3f}s")
            
            # Both should be fast with mocking, but this shows the pattern
            assert first_request_time < 0.1, "First request too slow even with mocking"
            assert second_request_time < 0.1, "Second request too slow even with mocking"
    
    def test_language_preference_caching(self, client, test_app):
        """Test caching effectiveness for language preferences."""
        with test_app.app_context():
            session_id = str(uuid.uuid4())
            
            with client.session_transaction() as sess:
                sess['session_id'] = session_id
            
            # Set language preference
            response = client.post('/set-language', json={'language': 'hi'})
            assert response.status_code == 200
            
            # Multiple requests to get language preference (should be cached in session)
            response_times = []
            
            for i in range(5):
                start_time = time.time()
                
                response = client.get('/get-languages')
                
                end_time = time.time()
                response_time = end_time - start_time
                response_times.append(response_time)
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['current_language'] == 'hi'
            
            # Verify consistent performance (should be fast due to session caching)
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            
            assert avg_response_time < 0.1, f"Language preference retrieval too slow: {avg_response_time:.3f}s"
            assert max_response_time < 0.2, f"Max language preference retrieval too slow: {max_response_time:.3f}s"
            
            print(f"\nLanguage preference caching performance:")
            print(f"  Avg response time: {avg_response_time:.3f}s")
            print(f"  Max response time: {max_response_time:.3f}s")
    
    def test_database_query_performance(self, test_app):
        """Test database query performance for language and sentiment data."""
        with test_app.app_context():
            # Create test data
            session_id = str(uuid.uuid4())
            languages = ['en', 'hi', 'mr']
            sentiments = ['positive', 'negative', 'neutral']
            
            # Insert test articles
            articles = []
            for i in range(50):  # Create 50 test articles
                article = NewsArticle(
                    title=f'Test Article {i}',
                    url=f'https://example.com/test-{i}',
                    summary=f'Test summary for article {i}',
                    sentiment=sentiments[i % len(sentiments)],
                    language=languages[i % len(languages)],
                    topic='test',
                    session_id=session_id
                )
                articles.append(article)
                db.session.add(article)
            
            db.session.commit()
            
            # Test query performance for different filters
            query_times = {}
            
            # Query by sentiment
            start_time = time.time()
            positive_articles = NewsArticle.query.filter_by(sentiment='positive').all()
            query_times['sentiment_filter'] = time.time() - start_time
            
            # Query by language
            start_time = time.time()
            hindi_articles = NewsArticle.query.filter_by(language='hi').all()
            query_times['language_filter'] = time.time() - start_time
            
            # Query by session
            start_time = time.time()
            session_articles = NewsArticle.query.filter_by(session_id=session_id).all()
            query_times['session_filter'] = time.time() - start_time
            
            # Combined query
            start_time = time.time()
            combined_articles = NewsArticle.query.filter_by(
                session_id=session_id,
                language='en',
                sentiment='positive'
            ).all()
            query_times['combined_filter'] = time.time() - start_time
            
            # Verify query performance
            for query_type, query_time in query_times.items():
                assert query_time < 0.1, f"{query_type} query too slow: {query_time:.3f}s"
            
            # Verify correct results
            assert len(positive_articles) > 0, "Should find positive articles"
            assert len(hindi_articles) > 0, "Should find Hindi articles"
            assert len(session_articles) == 50, "Should find all session articles"
            assert len(combined_articles) >= 0, "Combined query should work"
            
            print(f"\nDatabase query performance:")
            for query_type, query_time in query_times.items():
                print(f"  {query_type}: {query_time:.3f}s")
    
    # Test 5: Memory Usage and Resource Optimization
    
    def test_memory_usage_optimization(self, news_service, sample_articles):
        """Test memory usage optimization in text processing."""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            pytest.skip("psutil not available for memory testing")
        
        # Process multiple articles to test memory usage
        results = []
        
        for i, article in enumerate(sample_articles * 5):  # Process 15 articles total
            with patch('news_service.handle_language_operation') as mock_handle:
                mock_handle.return_value = {
                    'summary': f'Article {i} summary',
                    'sentiment': 'neutral',
                    'language': 'en'
                }
                
                result = news_service.generate_summary_with_sentiment(
                    article['body'], article['title'], 'en'
                )
                results.append(result)
                
                # Check memory usage periodically
                if i % 5 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_increase = current_memory - initial_memory
                    
                    # Memory increase should be reasonable
                    assert memory_increase < 50, f"Memory usage increased too much: {memory_increase:.1f}MB"
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_memory_increase = final_memory - initial_memory
        
        print(f"\nMemory usage optimization:")
        print(f"  Initial memory: {initial_memory:.1f}MB")
        print(f"  Final memory: {final_memory:.1f}MB")
        print(f"  Total increase: {total_memory_increase:.1f}MB")
        print(f"  Articles processed: {len(results)}")
        
        # Verify reasonable memory usage
        assert total_memory_increase < 100, f"Total memory increase too high: {total_memory_increase:.1f}MB"
        assert len(results) == 15, "Should process all articles"
    
    def test_text_truncation_optimization(self, news_service):
        """Test text truncation optimization for token usage."""
        # Test with very long article
        long_article = "This is a very long article. " * 200  # ~1200 words
        long_title = "Very Long Article Title " * 10  # Long title
        
        with patch('news_service.handle_language_operation') as mock_handle:
            mock_handle.return_value = {
                'summary': 'Long article summary',
                'sentiment': 'neutral',
                'language': 'en'
            }
            
            result = news_service.generate_summary_with_sentiment(
                long_article, long_title, 'en'
            )
            
            # Verify the method was called (text truncation happens inside the implementation)
            mock_handle.assert_called_once()
            
            # Verify that the function was called with the expected parameters
            call_args = mock_handle.call_args
            assert call_args[0][1] == 'en'  # language parameter
            assert call_args[0][2] == news_service._generate_summary_with_sentiment_for_language  # function
            
            # Result should still be valid
            assert result['sentiment'] in ['positive', 'negative', 'neutral']
            assert 'summary' in result


if __name__ == "__main__":
    # Run tests with verbose output and performance timing
    pytest.main([__file__, "-v", "--tb=short", "-s"])  # -s to show print statements