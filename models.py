from app import db
from datetime import datetime, timezone
import json

class ConversationSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    state = db.Column(db.Text)  # JSON string to store conversation state
    topics = db.Column(db.Text)  # JSON string to store collected topics
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def get_topics(self):
        if self.topics:
            return json.loads(self.topics)
        return []
    
    def set_topics(self, topics_list):
        self.topics = json.dumps(topics_list)
    
    def get_state(self):
        if self.state:
            return json.loads(self.state)
        return {}
    
    def set_state(self, state_dict):
        self.state = json.dumps(state_dict)

class NewsArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    url = db.Column(db.String(1000), nullable=False)
    summary = db.Column(db.Text)
    full_content = db.Column(db.Text)
    topic = db.Column(db.String(200), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    sentiment = db.Column(db.String(20), default='neutral')
    language = db.Column(db.String(5), default='en')
    summary_language = db.Column(db.String(5), default='en')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
