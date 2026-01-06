#!/usr/bin/env python3
"""
Database migration script to add sentiment and language support to existing NewsArticle table.
This script safely adds new columns to existing databases without losing data.
"""

import os
import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_path():
    """Get the database path from environment or use default."""
    database_url = os.environ.get("DATABASE_URL", "sqlite:///news_app.db")
    if database_url.startswith("sqlite:///"):
        return database_url[10:]  # Remove sqlite:/// prefix
    else:
        raise ValueError("Migration script currently only supports SQLite databases")

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in the specified table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def migrate_database():
    """Perform database migration to add sentiment and language fields."""
    db_path = get_database_path()
    
    if not os.path.exists(db_path):
        logger.info(f"Database file {db_path} does not exist. No migration needed.")
        return
    
    logger.info(f"Starting database migration for {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if NewsArticle table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='news_article'")
        if not cursor.fetchone():
            logger.info("NewsArticle table does not exist. No migration needed.")
            conn.close()
            return
        
        migrations_performed = []
        
        # Add sentiment column if it doesn't exist
        if not check_column_exists(cursor, 'news_article', 'sentiment'):
            cursor.execute("ALTER TABLE news_article ADD COLUMN sentiment VARCHAR(20) DEFAULT 'neutral'")
            migrations_performed.append("Added sentiment column")
            logger.info("Added sentiment column to news_article table")
        
        # Add language column if it doesn't exist
        if not check_column_exists(cursor, 'news_article', 'language'):
            cursor.execute("ALTER TABLE news_article ADD COLUMN language VARCHAR(5) DEFAULT 'en'")
            migrations_performed.append("Added language column")
            logger.info("Added language column to news_article table")
        
        # Add summary_language column if it doesn't exist
        if not check_column_exists(cursor, 'news_article', 'summary_language'):
            cursor.execute("ALTER TABLE news_article ADD COLUMN summary_language VARCHAR(5) DEFAULT 'en'")
            migrations_performed.append("Added summary_language column")
            logger.info("Added summary_language column to news_article table")
        
        # Commit the changes
        conn.commit()
        
        if migrations_performed:
            logger.info(f"Migration completed successfully. Changes: {', '.join(migrations_performed)}")
        else:
            logger.info("No migration needed. All columns already exist.")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def verify_migration():
    """Verify that the migration was successful."""
    db_path = get_database_path()
    
    if not os.path.exists(db_path):
        logger.info("Database file does not exist. Nothing to verify.")
        return True
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if all required columns exist
        required_columns = ['sentiment', 'language', 'summary_language']
        cursor.execute("PRAGMA table_info(news_article)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        if missing_columns:
            logger.error(f"Migration verification failed. Missing columns: {missing_columns}")
            return False
        
        logger.info("Migration verification successful. All required columns exist.")
        return True
        
    except Exception as e:
        logger.error(f"Migration verification failed: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    try:
        migrate_database()
        if verify_migration():
            logger.info("Database migration completed and verified successfully.")
        else:
            logger.error("Database migration verification failed.")
            exit(1)
    except Exception as e:
        logger.error(f"Migration script failed: {e}")
        exit(1)