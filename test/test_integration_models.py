#!/usr/bin/env python3
"""
Integration test to verify the enhanced models work with the actual application.
"""

import os
import tempfile
from app import app, db
from models import NewsArticle, ConversationSession

def test_integration():
    """Test that the enhanced models work with the actual Flask app."""
    # Create a temporary database for testing
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # Configure the app to use the test database
    original_db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True
    
    try:
        with app.app_context():
            # Create tables
            db.create_all()
            
            print("Testing NewsArticle model with enhanced fields...")
            
            # Test creating an article with default values
            article1 = NewsArticle(
                title="Test Article 1",
                url="https://example.com/test1",
                summary="Test summary 1",
                full_content="Test content 1",
                topic="technology",
                session_id="test_session_1"
            )
            
            db.session.add(article1)
            db.session.commit()
            
            print(f"✅ Created article with defaults: sentiment={article1.sentiment}, language={article1.language}")
            
            # Test creating an article with custom values
            article2 = NewsArticle(
                title="Artículo de Prueba",
                url="https://ejemplo.com/prueba",
                summary="Test summary in English",
                full_content="Contenido en español",
                topic="tecnología",
                session_id="test_session_2",
                sentiment="positive",
                language="es",
                summary_language="en"
            )
            
            db.session.add(article2)
            db.session.commit()
            
            print(f"✅ Created article with custom values: sentiment={article2.sentiment}, language={article2.language}, summary_language={article2.summary_language}")
            
            # Test querying by sentiment
            positive_articles = NewsArticle.query.filter_by(sentiment='positive').all()
            neutral_articles = NewsArticle.query.filter_by(sentiment='neutral').all()
            
            print(f"✅ Query by sentiment: {len(positive_articles)} positive, {len(neutral_articles)} neutral")
            
            # Test querying by language
            english_articles = NewsArticle.query.filter_by(language='en').all()
            spanish_articles = NewsArticle.query.filter_by(language='es').all()
            
            print(f"✅ Query by language: {len(english_articles)} English, {len(spanish_articles)} Spanish")
            
            # Test that ConversationSession still works
            session = ConversationSession(session_id="integration_test")
            session.set_topics(["technology", "science"])
            session.set_state({"step": "testing"})
            
            db.session.add(session)
            db.session.commit()
            
            retrieved_session = ConversationSession.query.filter_by(session_id="integration_test").first()
            print(f"✅ ConversationSession works: topics={retrieved_session.get_topics()}, state={retrieved_session.get_state()}")
            
            print("\n🎉 All integration tests passed!")
            return True
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False
        
    finally:
        # Restore original configuration
        if original_db_uri:
            app.config['SQLALCHEMY_DATABASE_URI'] = original_db_uri
        
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)

if __name__ == "__main__":
    test_integration()