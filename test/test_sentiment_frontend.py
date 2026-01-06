#!/usr/bin/env python3
"""
Frontend tests for sentiment indicator functionality.
Tests the sentiment display components and their integration with article rendering.
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import json
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import NewsArticle, ConversationSession
from datetime import datetime, timezone

class TestSentimentFrontend:
    """Test sentiment indicator display and functionality."""
    
    @pytest.fixture(scope="class")
    def app(self):
        """Create test Flask app."""
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Create Chrome WebDriver instance."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    @pytest.fixture
    def test_articles(self, app):
        """Create test articles with different sentiments."""
        with app.app_context():
            # Create test session
            session = ConversationSession(
                session_id='test_sentiment_session',
                topics='["technology", "politics"]'
            )
            db.session.add(session)
            
            # Create articles with different sentiments
            articles = [
                NewsArticle(
                    title="Amazing Tech Breakthrough Changes Everything",
                    url="https://example.com/positive",
                    summary="This revolutionary technology will transform our lives for the better.",
                    topic="technology",
                    session_id='test_sentiment_session',
                    sentiment='positive',
                    language='en'
                ),
                NewsArticle(
                    title="Economic Crisis Hits Global Markets Hard",
                    url="https://example.com/negative",
                    summary="Markets plummet as economic uncertainty spreads worldwide.",
                    topic="politics",
                    session_id='test_sentiment_session',
                    sentiment='negative',
                    language='en'
                ),
                NewsArticle(
                    title="Weather Report for Tomorrow",
                    url="https://example.com/neutral",
                    summary="Tomorrow will be partly cloudy with temperatures around 70 degrees.",
                    topic="weather",
                    session_id='test_sentiment_session',
                    sentiment='neutral',
                    language='en'
                )
            ]
            
            for article in articles:
                db.session.add(article)
            
            db.session.commit()
            return articles
    
    def test_sentiment_indicator_display(self, app, driver, test_articles):
        """Test that sentiment indicators are displayed correctly."""
        with app.test_client() as client:
            # Start the app in a separate thread for testing
            import threading
            import time
            
            def run_app():
                app.run(host='127.0.0.1', port=5555, debug=False, use_reloader=False)
            
            app_thread = threading.Thread(target=run_app, daemon=True)
            app_thread.start()
            time.sleep(2)  # Give the server time to start
            
            try:
                # Navigate to the application
                driver.get("http://127.0.0.1:5555")
                
                # Wait for page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "chat-input"))
                )
                
                # Simulate adding topics and searching for news
                chat_input = driver.find_element(By.ID, "chat-input")
                chat_input.send_keys("technology politics")
                
                send_btn = driver.find_element(By.ID, "send-btn")
                send_btn.click()
                
                # Wait for response and search
                time.sleep(3)
                
                # Trigger news search
                search_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "search-btn"))
                )
                search_btn.click()
                
                # Wait for articles to load
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "news-article"))
                )
                
                # Check for sentiment indicators
                sentiment_indicators = driver.find_elements(By.CLASS_NAME, "sentiment-indicator")
                assert len(sentiment_indicators) > 0, "No sentiment indicators found"
                
                # Test positive sentiment indicator
                positive_indicators = driver.find_elements(By.CSS_SELECTOR, ".sentiment-indicator.positive")
                if positive_indicators:
                    positive_indicator = positive_indicators[0]
                    assert "positive" in positive_indicator.get_attribute("class")
                    
                    # Check for positive icon
                    positive_icon = positive_indicator.find_element(By.CSS_SELECTOR, ".sentiment-icon.fas.fa-smile")
                    assert positive_icon is not None
                    
                    # Check for positive text
                    positive_text = positive_indicator.find_element(By.CLASS_NAME, "sentiment-text")
                    assert positive_text.text.upper() == "POSITIVE"
                
                # Test negative sentiment indicator
                negative_indicators = driver.find_elements(By.CSS_SELECTOR, ".sentiment-indicator.negative")
                if negative_indicators:
                    negative_indicator = negative_indicators[0]
                    assert "negative" in negative_indicator.get_attribute("class")
                    
                    # Check for negative icon
                    negative_icon = negative_indicator.find_element(By.CSS_SELECTOR, ".sentiment-icon.fas.fa-frown")
                    assert negative_icon is not None
                    
                    # Check for negative text
                    negative_text = negative_indicator.find_element(By.CLASS_NAME, "sentiment-text")
                    assert negative_text.text.upper() == "NEGATIVE"
                
                # Test neutral sentiment indicator
                neutral_indicators = driver.find_elements(By.CSS_SELECTOR, ".sentiment-indicator.neutral")
                if neutral_indicators:
                    neutral_indicator = neutral_indicators[0]
                    assert "neutral" in neutral_indicator.get_attribute("class")
                    
                    # Check for neutral icon
                    neutral_icon = neutral_indicator.find_element(By.CSS_SELECTOR, ".sentiment-icon.fas.fa-meh")
                    assert neutral_icon is not None
                    
                    # Check for neutral text
                    neutral_text = neutral_indicator.find_element(By.CLASS_NAME, "sentiment-text")
                    assert neutral_text.text.upper() == "NEUTRAL"
                
            except Exception as e:
                print(f"Test failed with error: {e}")
                # Take screenshot for debugging
                driver.save_screenshot("sentiment_test_failure.png")
                raise
    
    def test_sentiment_tooltip_functionality(self, app, driver, test_articles):
        """Test sentiment indicator tooltip hover effects."""
        with app.test_client() as client:
            # Start the app
            import threading
            import time
            
            def run_app():
                app.run(host='127.0.0.1', port=5556, debug=False, use_reloader=False)
            
            app_thread = threading.Thread(target=run_app, daemon=True)
            app_thread.start()
            time.sleep(2)
            
            try:
                driver.get("http://127.0.0.1:5556")
                
                # Navigate to articles
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "chat-input"))
                )
                
                chat_input = driver.find_element(By.ID, "chat-input")
                chat_input.send_keys("technology")
                
                send_btn = driver.find_element(By.ID, "send-btn")
                send_btn.click()
                time.sleep(2)
                
                search_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "search-btn"))
                )
                search_btn.click()
                
                # Wait for articles
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "sentiment-indicator"))
                )
                
                # Test tooltip hover
                sentiment_indicator = driver.find_element(By.CLASS_NAME, "sentiment-indicator")
                
                # Hover over the sentiment indicator
                actions = ActionChains(driver)
                actions.move_to_element(sentiment_indicator).perform()
                
                # Wait for tooltip to appear
                time.sleep(1)
                
                # Check if tooltip is visible (this might need adjustment based on CSS)
                tooltip = sentiment_indicator.find_element(By.CLASS_NAME, "sentiment-tooltip")
                assert tooltip is not None
                
                # Check tooltip text content
                tooltip_text = tooltip.text
                assert len(tooltip_text) > 0, "Tooltip should have text content"
                assert "sentiment" in tooltip_text.lower(), "Tooltip should mention sentiment"
                
            except Exception as e:
                print(f"Tooltip test failed with error: {e}")
                driver.save_screenshot("tooltip_test_failure.png")
                raise
    
    def test_responsive_sentiment_display(self, app, driver, test_articles):
        """Test sentiment indicators on mobile/responsive layout."""
        with app.test_client() as client:
            # Start the app
            import threading
            import time
            
            def run_app():
                app.run(host='127.0.0.1', port=5557, debug=False, use_reloader=False)
            
            app_thread = threading.Thread(target=run_app, daemon=True)
            app_thread.start()
            time.sleep(2)
            
            try:
                # Set mobile viewport
                driver.set_window_size(375, 667)  # iPhone size
                
                driver.get("http://127.0.0.1:5557")
                
                # Navigate to articles
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "chat-input"))
                )
                
                chat_input = driver.find_element(By.ID, "chat-input")
                chat_input.send_keys("technology")
                
                send_btn = driver.find_element(By.ID, "send-btn")
                send_btn.click()
                time.sleep(2)
                
                search_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "search-btn"))
                )
                search_btn.click()
                
                # Wait for articles
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "sentiment-indicator"))
                )
                
                # Check that sentiment indicators are still visible and properly sized
                sentiment_indicators = driver.find_elements(By.CLASS_NAME, "sentiment-indicator")
                assert len(sentiment_indicators) > 0, "Sentiment indicators should be visible on mobile"
                
                for indicator in sentiment_indicators:
                    # Check that indicator is visible
                    assert indicator.is_displayed(), "Sentiment indicator should be visible on mobile"
                    
                    # Check that it has reasonable size (not too small)
                    size = indicator.size
                    assert size['width'] > 20, "Sentiment indicator should have reasonable width on mobile"
                    assert size['height'] > 15, "Sentiment indicator should have reasonable height on mobile"
                
            except Exception as e:
                print(f"Responsive test failed with error: {e}")
                driver.save_screenshot("responsive_test_failure.png")
                raise
            finally:
                # Reset window size
                driver.set_window_size(1920, 1080)
    
    def test_sentiment_integration_with_article_data(self, app, driver, test_articles):
        """Test that sentiment indicators correctly reflect article sentiment data."""
        with app.test_client() as client:
            # Start the app
            import threading
            import time
            
            def run_app():
                app.run(host='127.0.0.1', port=5558, debug=False, use_reloader=False)
            
            app_thread = threading.Thread(target=run_app, daemon=True)
            app_thread.start()
            time.sleep(2)
            
            try:
                driver.get("http://127.0.0.1:5558")
                
                # Navigate to articles
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "chat-input"))
                )
                
                chat_input = driver.find_element(By.ID, "chat-input")
                chat_input.send_keys("technology politics weather")
                
                send_btn = driver.find_element(By.ID, "send-btn")
                send_btn.click()
                time.sleep(2)
                
                search_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "search-btn"))
                )
                search_btn.click()
                
                # Wait for articles
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "news-article"))
                )
                
                # Get all articles
                articles = driver.find_elements(By.CLASS_NAME, "news-article")
                
                # Verify that each article has a sentiment indicator
                for article in articles:
                    sentiment_indicator = article.find_element(By.CLASS_NAME, "sentiment-indicator")
                    assert sentiment_indicator is not None, "Each article should have a sentiment indicator"
                    
                    # Check that the sentiment indicator has the correct classes
                    classes = sentiment_indicator.get_attribute("class")
                    assert any(sentiment in classes for sentiment in ['positive', 'negative', 'neutral']), \
                        "Sentiment indicator should have a sentiment class"
                    
                    # Check that it has the required elements
                    icon = sentiment_indicator.find_element(By.CLASS_NAME, "sentiment-icon")
                    text = sentiment_indicator.find_element(By.CLASS_NAME, "sentiment-text")
                    tooltip = sentiment_indicator.find_element(By.CLASS_NAME, "sentiment-tooltip")
                    
                    assert icon is not None, "Sentiment indicator should have an icon"
                    assert text is not None, "Sentiment indicator should have text"
                    assert tooltip is not None, "Sentiment indicator should have a tooltip"
                    
                    # Verify text content matches sentiment
                    text_content = text.text.upper()
                    if 'positive' in classes:
                        assert text_content == 'POSITIVE'
                    elif 'negative' in classes:
                        assert text_content == 'NEGATIVE'
                    elif 'neutral' in classes:
                        assert text_content == 'NEUTRAL'
                
            except Exception as e:
                print(f"Integration test failed with error: {e}")
                driver.save_screenshot("integration_test_failure.png")
                raise


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])