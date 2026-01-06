#!/usr/bin/env python3
"""
Test script to verify database migration functionality.
"""

import os
import sqlite3
import tempfile
from migrate_db import migrate_database, verify_migration

def create_old_schema_database(db_path):
    """Create a database with the old schema (without sentiment and language columns)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the old schema
    cursor.execute('''
        CREATE TABLE news_article (
            id INTEGER PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            url VARCHAR(1000) NOT NULL,
            summary TEXT,
            full_content TEXT,
            topic VARCHAR(200) NOT NULL,
            session_id VARCHAR(100) NOT NULL,
            created_at DATETIME
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE conversation_session (
            id INTEGER PRIMARY KEY,
            session_id VARCHAR(100) UNIQUE NOT NULL,
            state TEXT,
            topics TEXT,
            created_at DATETIME,
            updated_at DATETIME
        )
    ''')
    
    # Insert some test data
    cursor.execute('''
        INSERT INTO news_article (title, url, summary, full_content, topic, session_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
    ''', (
        "Test Article",
        "https://example.com/test",
        "Test summary",
        "Test content",
        "technology",
        "test_session"
    ))
    
    conn.commit()
    conn.close()
    print(f"Created old schema database at {db_path}")

def test_migration():
    """Test the migration process."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    try:
        # Set the database URL environment variable
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
        
        print("Step 1: Creating database with old schema...")
        create_old_schema_database(db_path)
        
        # Verify old schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(news_article)")
        old_columns = [row[1] for row in cursor.fetchall()]
        print(f"Old schema columns: {old_columns}")
        
        # Verify we can read old data
        cursor.execute("SELECT title, topic FROM news_article")
        old_data = cursor.fetchall()
        print(f"Old data: {old_data}")
        conn.close()
        
        print("\nStep 2: Running migration...")
        migrate_database()
        
        print("\nStep 3: Verifying migration...")
        success = verify_migration()
        
        if success:
            # Check new schema
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(news_article)")
            new_columns = [row[1] for row in cursor.fetchall()]
            print(f"New schema columns: {new_columns}")
            
            # Verify old data is preserved and new columns have defaults
            cursor.execute("SELECT title, topic, sentiment, language, summary_language FROM news_article")
            new_data = cursor.fetchall()
            print(f"Migrated data: {new_data}")
            conn.close()
            
            print("\n✅ Migration test PASSED!")
            return True
        else:
            print("\n❌ Migration test FAILED!")
            return False
            
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']

if __name__ == "__main__":
    test_migration()