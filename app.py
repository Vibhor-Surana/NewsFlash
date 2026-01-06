import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,  # Changed from DEBUG to reduce noise
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///news_app.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

# Import routes
import routes

logger = logging.getLogger(__name__)

# Validate configuration before starting
try:
    from config import Config
    Config.validate_config()
    logger.info("Configuration validation passed")
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    logger.error("Please check your .env file and ensure all required API keys are set")
    raise

with app.app_context():
    # Import models to ensure tables are created
    import models
    
    # Run database migration for existing databases
    try:
        from migrate_db import migrate_database
        migrate_database()
    except Exception as e:
        logger.warning(f"Migration failed, proceeding with create_all: {e}")
    
    # Create all tables (this is safe for new databases and won't affect existing ones)
    db.create_all()

logger.info("Flask application initialized successfully")