# 📰 NewsFlash - AI-Powered Multilingual News Assistant

<div align="center">

![NewsFlash Banner](https://img.shields.io/badge/NewsFlash-AI%20News%20Assistant-2563eb?style=for-the-badge&logo=newspaper&logoColor=white)

A sophisticated, production-ready news aggregation platform that combines real-time news search with advanced AI capabilities including intelligent conversation management, multilingual content generation, sentiment analysis, and text-to-speech functionality.

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.2-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.27-4CAF50?style=flat&logo=chainlink&logoColor=white)](https://www.langchain.com/)
[![Google Gemini](https://img.shields.io/badge/Gemini-1.5%20Flash-4285F4?style=flat&logo=google&logoColor=white)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat)](LICENSE)

[Features](#-key-features) • [Demo](#-demo) • [Installation](#-installation) • [Architecture](#-architecture) • [API Documentation](#-api-documentation) • [Contributing](#-contributing)

</div>

---

## 🌟 Key Features

### 🤖 Intelligent Conversational AI
- **State-Based Conversation Management**: Built with LangGraph for complex conversation workflows
- **Context-Aware Interactions**: Maintains conversation state across sessions using SQLAlchemy
- **Natural Language Understanding**: Powered by Google Gemini 1.5 Flash for topic extraction and intent recognition
- **Multi-Stage Conversation Flow**: Guides users through language selection → topic collection → news search
- **LangSmith Integration**: Full conversation tracing and monitoring for production optimization

### 📰 Advanced News Aggregation
- **Real-Time News Search**: DuckDuckGo Search API integration for up-to-date news articles
- **Multi-Topic Support**: Search and aggregate news from multiple topics simultaneously
- **Intelligent Content Extraction**: Three-tier extraction system:
  - Primary: Newspaper3k for specialized news article parsing
  - Fallback: Trafilatura for robust web content extraction
  - Final: BeautifulSoup for maximum compatibility
- **Source Attribution**: Automatic extraction of source names, publication dates, and metadata
- **Infinite Scroll**: Progressive loading with configurable batch sizes

### 🌍 Comprehensive Multilingual Support
- **3 Supported Languages**: English, Hindi (हिंदी), and Marathi (मराठी)
- **AI-Powered Translation**: Context-aware summary generation in target languages
- **Language-Specific Prompts**: Optimized prompt templates for each supported language
- **Intelligent Fallback System**: Automatic English fallback with detailed error logging
- **Session Persistence**: Language preferences maintained across user sessions
- **Native Language Names**: UI displays language names in their native scripts

### 💭 Advanced Sentiment Analysis
- **Real-Time Sentiment Detection**: AI-powered analysis of article emotional tone
- **Multi-Lingual Sentiment**: Sentiment analysis works across all supported languages
- **Visual Indicators**: Color-coded badges (green=positive, yellow=neutral, red=negative)
- **Confidence-Based Results**: Intelligent fallback to neutral for ambiguous content
- **Batch Processing**: Efficient sentiment analysis for multiple articles

### 🎧 High-Quality Text-to-Speech
- **Google TTS Integration**: Natural-sounding speech synthesis via gTTS
- **Multi-Language Audio**: Supports English, Hindi, and Marathi audio generation
- **Smart Content Cleaning**: Automatic removal of markdown, URLs, and special characters
- **Playback Controls**: Built-in audio player with play/stop functionality
- **Audio Caching**: Generated audio files cached for improved performance
- **Full Article Reading**: TTS support for both summaries and complete article content

### 🎨 Modern, Responsive UI
- **Professional Design System**: Clean, news-inspired interface with custom CSS variables
- **Dark/Light Theme**: User-selectable theme with localStorage persistence
- **Responsive Layout**: Mobile-first design using Bootstrap 5.3
- **Accessibility Features**: WCAG-compliant with keyboard navigation and ARIA labels
- **Compact Mode**: Optional condensed layout for information density
- **Loading States**: Skeleton screens and progress indicators for better UX
- **Error Handling**: User-friendly error messages with retry mechanisms

### 🔒 Production-Ready Features
- **Comprehensive Error Handling**: Custom exception hierarchy with fallback strategies
- **Rate Limiting**: Configurable delays between AI API calls
- **Database Migrations**: Automated schema updates with backward compatibility
- **Environment-Based Config**: Support for development, staging, and production
- **Logging System**: UTF-8 encoded logs with multiple handlers
- **Session Management**: Secure session handling with Flask sessions
- **Proxy Support**: Ready for deployment behind reverse proxies

---

## 🚀 Demo

### Conversation Flow
```
User: "Hindi"
Bot: "Great! I'll provide news summaries in Hindi. What topic would you like to search for?"

User: "artificial intelligence"
Bot: "Added 'artificial intelligence' to your search topics. Do you want to search about anything else?"

User: "climate change"
Bot: "Added 'climate change'. Do you want to search about anything else?"

User: "no"
Bot: "Great! I'll search for news on these topics: artificial intelligence, climate change..."

[News articles displayed with Hindi summaries and sentiment indicators]
```

### Sample Features
- 🔍 **Smart Search**: "Show me news about technology and sports"
- 🌐 **Language Switch**: Select Hindi/Marathi for instant translated summaries
- 😊 **Sentiment**: Visual badges showing article emotional tone
- 🎤 **Listen**: Click speaker icon to hear articles in your language
- 📱 **Responsive**: Works seamlessly on desktop, tablet, and mobile

---

## 🛠️ Installation

### Prerequisites
- **Python 3.8+** (Recommended: Python 3.10+)
- **pip** package manager
- **Git** for version control
- **API Keys**:
  - Google Gemini API key ([Get it here](https://makersuite.google.com/app/apikey))
  - LangSmith API key ([Get it here](https://smith.langchain.com/))

### Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Vibhor-Surana/NewsFlash.git
   cd NewsFlash
   ```

2. **Create Virtual Environment** (Recommended)
   ```bash
   # Windows
   python -m venv news2
   news2\Scripts\activate

   # Linux/Mac
   python3 -m venv news2
   source news2/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your favorite editor
   # Add your API keys and configure settings
   ```

   **Required `.env` Configuration:**
   ```env
   # API Keys - REQUIRED
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   LANGSMITH_API_KEY=your_actual_langsmith_api_key_here
   
   # LangSmith Configuration
   LANGSMITH_PROJECT=news-website
   
   # Language Settings
   DEFAULT_LANGUAGE=en
   LANGUAGE_FALLBACK_ENABLED=true
   
   # Sentiment Analysis
   SENTIMENT_ANALYSIS_ENABLED=true
   SENTIMENT_DISPLAY_ENABLED=true
   
   # AI Settings
   USE_AI_SUMMARY=true
   
   # Database (optional, defaults to SQLite)
   DATABASE_URL=sqlite:///news_app.db
   
   # Session Secret (optional, auto-generated for dev)
   SESSION_SECRET=your_secure_secret_key_here
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```
   
   The application will:
   - Validate your API keys
   - Initialize the database automatically
   - Start the Flask development server
   - Open at `http://localhost:5000`

6. **Access the Application**
   ```
   Open your browser and navigate to: http://localhost:5000
   ```

### Production Deployment

For production deployment, use a WSGI server like Gunicorn:

```bash
# Install Gunicorn (already in requirements.txt)
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# Or use the provided Procfile for platforms like Heroku
web: gunicorn app:app
```

**Environment Configuration for Production:**
- Set `DATABASE_URL` to your PostgreSQL connection string
- Use a strong `SESSION_SECRET` (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
- Enable SSL/TLS for API endpoints
- Configure proper CORS settings if needed

---

---

## 📱 Usage Guide

### Getting Started with NewsFlash

1. **Initial Conversation**
   - The chat assistant will greet you and ask for language preference
   - Select your preferred language: English, Hindi, or Marathi
   - Start adding topics you're interested in

2. **Adding Topics**
   ```
   Example conversation:
   You: "artificial intelligence"
   Bot: "Added 'artificial intelligence' to your search topics..."
   
   You: "climate change"  
   Bot: "Added 'climate change'..."
   
   You: "no"
   Bot: "Searching for news..."
   ```

3. **Browsing News**
   - Articles appear organized by your topics
   - Each article shows:
     - Title and source
     - AI-generated summary in your language
     - Sentiment badge (positive/negative/neutral)
     - Publication date
     - Action buttons (Read Full, Listen)

4. **Interactive Features**
   - **Read Full Article**: Opens modal with complete article content
   - **Listen**: Plays AI-generated speech in your selected language
   - **Load More**: Fetches additional articles for each topic
   - **Reset Chat**: Starts a new conversation

### Language Selection

Change your language preference anytime using the dropdown in the header:
- 🇬🇧 **English** - Default language
- 🇮🇳 **हिंदी (Hindi)** - Devanagari script support
- 🇮🇳 **मराठी (Marathi)** - Regional language support

**Note**: Language changes apply to new searches and summaries.

### Understanding Sentiment Badges

- 🟢 **Positive** - Uplifting, optimistic, or good news
- 🟡 **Neutral** - Factual reporting without strong emotion
- 🔴 **Negative** - Concerning, problematic, or distressing content

### Chat Commands & Keywords

**Topic Input**: Simply type any topic name
```
"technology", "sports", "politics", "economy", "health", etc.
```

**Stop Adding Topics**: Use any of these phrases
```
"no", "n", "done", "stop", "search", "नहीं" (Hindi), "नाही" (Marathi)
```

**Reset Conversation**: Click the "Reset Chat" button to start fresh

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Chat Widget │  │ News Display │  │ Language     │      │
│  │  (Real-time) │  │  (Articles)  │  │ Selector     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                           ↕ HTTPS/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                    Flask Application Layer                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Routes     │  │   Session    │  │    Error     │      │
│  │  (Endpoints) │  │   Manager    │  │   Handler    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Conversation │  │     News     │  │   Language   │      │
│  │    Graph     │  │   Service    │  │   Service    │      │
│  │ (LangGraph)  │  │  (Search &   │  │ (Multilang)  │      │
│  │              │  │  Summarize)  │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │     TTS      │  │   Article    │  │   Session    │      │
│  │   Service    │  │  Extractor   │  │   Manager    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│                  External Services & Data                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │Google Gemini │  │  DuckDuckGo  │  │    gTTS      │      │
│  │  (AI Model)  │  │   (Search)   │  │   (Audio)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │  LangSmith   │  │  SQLAlchemy  │                         │
│  │  (Tracing)   │  │  (Database)  │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. **Conversation Management** (`conversation_graph.py`)
- **LangGraph State Machine**: Multi-stage conversation flow
- **State Stages**:
  - `language_selection`: Choose preferred language
  - `collecting`: Gather news topics from user
  - `searching`: Execute news search
  - `completed`: Display results
- **Language Detection**: Automatic language preference detection
- **Topic Validation**: Prevents duplicate topic entries
- **Context Persistence**: Maintains conversation state across requests

#### 2. **News Service** (`news_service.py`)
- **DuckDuckGo Integration**: Real-time news search API
- **AI Summarization**: Google Gemini-powered content summarization
- **Sentiment Analysis**: Emotion detection in articles
- **Multi-Language Support**: Summary generation in 3 languages
- **Rate Limiting**: Configurable delays between API calls
- **Fallback Strategies**: Graceful degradation when services fail

#### 3. **Language Service** (`language_service.py`)
- **Language Registry**: Centralized language configuration
- **Validation**: Language code validation and normalization
- **TTS Mapping**: Language-to-voice mapping for audio
- **Fallback Logic**: Intelligent English fallback system
- **Native Names**: Support for displaying names in native scripts

#### 4. **Article Extraction** (`article_extractor.py`)
- **Three-Tier System**:
  1. **Newspaper3k**: Specialized news article parser (primary)
  2. **Trafilatura**: Robust web content extraction (fallback)
  3. **BeautifulSoup**: HTML parsing (final fallback)
- **Content Cleaning**: Removes ads, navigation, and non-article content
- **Metadata Extraction**: Extracts dates, authors, and source information
- **Error Recovery**: Automatic fallback between extraction methods

#### 5. **TTS Service** (`tts_service.py`)
- **gTTS Integration**: Google Text-to-Speech API
- **Language-Aware**: Automatically uses correct voice for language
- **Content Preprocessing**: Removes markdown, URLs, special characters
- **Audio Caching**: Stores generated MP3 files for reuse
- **Error Handling**: Graceful fallback when TTS fails

#### 6. **Error Handler** (`error_handler.py`)
- **Custom Exception Hierarchy**:
  - `NewsFlashError` (base)
  - `LanguageError`
  - `SentimentAnalysisError`
  - `AIServiceError`
  - `TTSError`
- **Decorators**: `@with_retry`, `@with_language_fallback`, `@with_sentiment_fallback`
- **Centralized Logging**: Structured error logging with context
- **Fallback Management**: Automatic fallback strategies for all operations

#### 7. **Session Manager** (`session_manager.py`)
- **Flask Session Integration**: Secure session management
- **Language Persistence**: Stores user language preferences
- **Session Defaults**: Initializes session with default values
- **Cross-Request State**: Maintains state across HTTP requests

### Database Schema

#### ConversationSession Model
```python
- id: Primary key
- session_id: Unique session identifier (UUID)
- state: JSON-encoded conversation state
- topics: JSON-encoded list of topics
- created_at: Timestamp
- updated_at: Timestamp
```

#### NewsArticle Model
```python
- id: Primary key
- title: Article title
- url: Article URL
- summary: AI-generated summary
- full_content: Complete article text
- topic: Associated search topic
- session_id: Link to conversation session
- sentiment: positive/negative/neutral
- language: Article language code
- summary_language: Summary language code
- created_at: Timestamp
```

### API Endpoints

#### Chat Endpoints
- **POST `/chat`**: Process conversation messages
  - Input: `{message: string}`
  - Output: `{response: string, topics: array, should_search: boolean, stage: string}`

#### Search Endpoints
- **POST `/search`**: Search for news articles
  - Input: `{query: string, language: string, max_results: number}`
  - Output: `{articles: array, query: string, language: string, total_results: number}`

#### Article Endpoints
- **POST `/article/full`**: Extract full article content
  - Input: `{url: string}`
  - Output: `{success: boolean, full_text: string, url: string}`

#### TTS Endpoints
- **POST `/tts`**: Generate text-to-speech audio
  - Input: `{text: string, language: string}`
  - Output: `{success: boolean, audio_url: string, language: string}`

#### Language Endpoints
- **GET `/languages`**: Get supported languages
  - Output: `{languages: object}`

- **POST `/language/set`**: Set language preference
  - Input: `{language: string}`
  - Output: `{success: boolean, language: string}`

#### Session Endpoints
- **POST `/session/reset`**: Reset conversation session
  - Output: `{success: boolean, message: string}`

---

## 🔧 Configuration

### Environment Variables

All configuration is managed through environment variables in the `.env` file:

```env
# ============ API Keys (REQUIRED) ============
GEMINI_API_KEY=your_gemini_api_key
LANGSMITH_API_KEY=your_langsmith_api_key

# ============ LangSmith Configuration ============
LANGSMITH_PROJECT=news-website
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# ============ Language Settings ============
DEFAULT_LANGUAGE=en                    # Default: en
LANGUAGE_FALLBACK_ENABLED=true         # Enable auto-fallback to English

# ============ Sentiment Analysis ============
SENTIMENT_ANALYSIS_ENABLED=true        # Enable sentiment detection
SENTIMENT_DISPLAY_ENABLED=true         # Show sentiment badges in UI
SENTIMENT_DEFAULT=neutral              # Default sentiment when analysis fails
SENTIMENT_FALLBACK_ENABLED=true        # Enable sentiment fallback

# ============ AI Configuration ============
USE_AI_SUMMARY=true                    # Use AI for summarization
AI_SUMMARY_MIN_LENGTH=150              # Min article length for AI summary
RATE_LIMIT_DELAY=2                     # Seconds between AI API calls
MAX_RETRY_ATTEMPTS=3                   # Max retries for failed AI requests
RETRY_DELAY=1                          # Base delay for retry backoff

# ============ News Search ============
NEWS_RESULTS_PER_TOPIC=5               # Articles per topic (initial load)
LOAD_MORE_COUNT=5                      # Articles per "Load More" click

# ============ TTS Settings ============
TTS_LANGUAGE=en                        # Default TTS language
TTS_SLOW=false                         # Use slow speech rate

# ============ Database ============
DATABASE_URL=sqlite:///news_app.db     # SQLite for development
# DATABASE_URL=postgresql://user:pass@host:5432/dbname  # PostgreSQL for production

# ============ Security ============
SESSION_SECRET=your_secret_key_here    # Flask session secret (auto-generated if not set)

# ============ Error Handling ============
ENABLE_FALLBACK_LOGGING=true           # Enable detailed fallback logging
```

### Application Configuration (`config.py`)

The `Config` class provides:
- API key validation at startup
- Language configuration management
- Feature toggles (sentiment, AI summary)
- Helper methods for language operations
- Production-ready defaults

---

## 🧪 Testing

The project includes comprehensive test suites:

### Test Categories

1. **Unit Tests**
   - `test/test_language_service.py`: Language validation and utilities
   - `test/test_models.py`: Database model tests
   - `test/test_session_manager.py`: Session management tests

2. **Integration Tests**
   - `test/test_integration_models.py`: Database integration
   - `test/test_language_api.py`: Language API endpoints
   - `test/test_sentiment_integration.py`: Sentiment analysis flow
   - `test/test_tts_multilang.py`: Multi-language TTS

3. **End-to-End Tests**
   - `test/test_complete_flow.py`: Full user journey
   - `test/test_e2e_language_sentiment_workflow.py`: Complete workflow
   - `test/test_frontend.py`: Frontend functionality

4. **Error Handling Tests**
   - `test/test_error_handling.py`: Error handling mechanisms
   - `test/test_language_error_scenarios.py`: Language fallback
   - `test/test_sentiment_error_scenarios.py`: Sentiment fallback

### Running Tests

```bash
# Run all tests
python -m pytest test/

# Run specific test file
python -m pytest test/test_language_service.py

# Run with coverage
python -m pytest --cov=. test/

# Run quick sanity test
python test/quick_test.py
```

---

## 📚 Technology Stack Deep Dive

### Backend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Flask** | 3.1.2 | Web framework and routing |
| **SQLAlchemy** | 2.0.43 | ORM and database management |
| **LangChain** | 0.3.27 | AI application framework |
| **LangGraph** | 0.6.6 | State machine for conversations |
| **Google Gemini** | 1.5-flash | AI model for summarization |
| **gTTS** | 2.5.4 | Text-to-speech generation |
| **DuckDuckGo Search** | 8.1.1 | News search API |
| **Trafilatura** | 2.0.0 | Web content extraction |
| **Newspaper3k** | 0.2.8 | News article parsing |
| **BeautifulSoup4** | 4.13.5 | HTML parsing |

### Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Bootstrap** | 5.3.0 | UI framework and components |
| **Font Awesome** | 6.4.0 | Icon library |
| **Inter Font** | Latest | Typography |
| **Vanilla JavaScript** | ES6+ | Client-side functionality |

### Development Tools

| Tool | Purpose |
|------|---------|
| **pytest** | Testing framework |
| **python-dotenv** | Environment variable management |
| **Gunicorn** | Production WSGI server |
| **LangSmith** | AI monitoring and tracing |

---

## 📖 API Documentation

### REST API Reference

#### 1. Chat API

**Endpoint**: `POST /chat`

**Description**: Process user messages in the conversational interface.

**Request Body**:
```json
{
  "message": "artificial intelligence"
}
```

**Response**:
```json
{
  "response": "Added 'artificial intelligence' to your search topics...",
  "topics": ["artificial intelligence"],
  "should_search": false,
  "stage": "collecting"
}
```

**Status Codes**:
- `200`: Success
- `400`: Invalid request (empty message)
- `500`: Server error

---

#### 2. Search API

**Endpoint**: `POST /search`

**Description**: Search for news articles on a specific topic.

**Request Body**:
```json
{
  "query": "technology",
  "language": "en",
  "max_results": 5
}
```

**Response**:
```json
{
  "success": true,
  "query": "technology",
  "language": "en",
  "total_results": 5,
  "articles": [
    {
      "title": "Article Title",
      "url": "https://example.com/article",
      "summary": "AI-generated summary...",
      "sentiment": "positive",
      "language": "en",
      "date": "2024-01-07",
      "source": "Example News",
      "topic": "technology"
    }
  ]
}
```

**Parameters**:
- `query` (required): Search topic
- `language` (optional): Language code (en/hi/mr), defaults to `en`
- `max_results` (optional): Number of results (1-20), defaults to `5`

---

#### 3. Full Article API

**Endpoint**: `POST /article/full`

**Description**: Extract complete article content from URL.

**Request Body**:
```json
{
  "url": "https://example.com/article"
}
```

**Response**:
```json
{
  "success": true,
  "full_text": "Complete article content...",
  "url": "https://example.com/article"
}
```

---

#### 4. Text-to-Speech API

**Endpoint**: `POST /tts`

**Description**: Generate audio file for text content.

**Request Body**:
```json
{
  "text": "Text to convert to speech",
  "language": "en"
}
```

**Response**:
```json
{
  "success": true,
  "audio_url": "/static/audio/tts_en_abc123.mp3",
  "language": "en"
}
```

---

#### 5. Languages API

**Endpoint**: `GET /languages`

**Description**: Get list of supported languages.

**Response**:
```json
{
  "languages": {
    "en": {
      "name": "English",
      "native": "English",
      "tts_code": "en",
      "enabled": true
    },
    "hi": {
      "name": "Hindi",
      "native": "हिंदी",
      "tts_code": "hi",
      "enabled": true
    },
    "mr": {
      "name": "Marathi",
      "native": "मराठी",
      "tts_code": "mr",
      "enabled": true
    }
  }
}
```

---

#### 6. Session Reset API

**Endpoint**: `POST /session/reset`

**Description**: Reset the current conversation session.

**Response**:
```json
{
  "success": true,
  "message": "Session reset successfully"
}
```

---

## 🚀 Deployment

### Deployment Platforms

#### Heroku

1. **Create Heroku App**
   ```bash
   heroku create your-app-name
   ```

2. **Set Environment Variables**
   ```bash
   heroku config:set GEMINI_API_KEY=your_key
   heroku config:set LANGSMITH_API_KEY=your_key
   heroku config:set SESSION_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
   ```

3. **Deploy**
   ```bash
   git push heroku main
   ```

4. **Scale Dynos**
   ```bash
   heroku ps:scale web=1
   ```

#### Docker

**Dockerfile** (create in project root):
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run with gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

**Build and Run**:
```bash
# Build image
docker build -t newsflash .

# Run container
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  -e LANGSMITH_API_KEY=your_key \
  newsflash
```

#### VPS (Ubuntu/Debian)

1. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip nginx
   ```

2. **Setup Application**
   ```bash
   cd /var/www/
   git clone https://github.com/Vibhor-Surana/NewsFlash.git
   cd NewsFlash
   pip3 install -r requirements.txt
   ```

3. **Configure Nginx**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /static {
           alias /var/www/NewsFlash/static;
       }
   }
   ```

4. **Create Systemd Service**
   ```ini
   [Unit]
   Description=NewsFlash Application
   After=network.target
   
   [Service]
   User=www-data
   WorkingDirectory=/var/www/NewsFlash
   Environment="PATH=/usr/bin"
   ExecStart=/usr/local/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
   
   [Install]
   WantedBy=multi-user.target
   ```

5. **Start Service**
   ```bash
   sudo systemctl start newsflash
   sudo systemctl enable newsflash
   ```

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Ways to Contribute

1. **Report Bugs**: Open an issue with detailed reproduction steps
2. **Suggest Features**: Propose new features or improvements
3. **Submit Pull Requests**: Fix bugs or implement features
4. **Improve Documentation**: Help make docs clearer and more comprehensive
5. **Add Tests**: Increase test coverage
6. **Translate**: Add support for more languages

### Development Setup

1. **Fork the Repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/NewsFlash.git
   cd NewsFlash
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Follow PEP 8 style guidelines
   - Add tests for new features
   - Update documentation

4. **Test Your Changes**
   ```bash
   python -m pytest test/
   ```

5. **Commit and Push**
   ```bash
   git add .
   git commit -m "Add: your feature description"
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Describe your changes
   - Reference related issues
   - Wait for code review

### Code Style Guidelines

- **Python**: Follow PEP 8
- **JavaScript**: Use ES6+ syntax
- **Comments**: Add docstrings for functions
- **Naming**: Use descriptive variable names
- **Testing**: Write tests for new features

---

##  Acknowledgments

### Technologies & Services
- **Google Gemini**: Powerful AI model for summarization and sentiment analysis
- **LangChain & LangGraph**: Excellent framework for building AI applications
- **Flask**: Robust and flexible web framework
- **DuckDuckGo**: Privacy-focused search API
- **Bootstrap**: Professional UI components

### Inspiration
- News websites: BBC, CNN, Reuters for design inspiration
- Open-source community for countless tools and libraries

---

## 🗺️ Roadmap

### Planned Features

#### Short Term (v1.1)
- [ ] More languages (Spanish, French, German)
- [ ] Article bookmarking system
- [ ] User authentication
- [ ] Personalized news feed
- [ ] Dark mode improvements

#### Medium Term (v1.2)
- [ ] Mobile apps (React Native)
- [ ] Advanced sentiment visualization
- [ ] News categorization by topics
- [ ] RSS feed support
- [ ] Export articles as PDF

#### Long Term (v2.0)
- [ ] Real-time news alerts
- [ ] Social sharing features
- [ ] Comment system
- [ ] News trending analysis
- [ ] ML-powered recommendations

### Completed
- [x] Multi-language support (English, Hindi, Marathi)
- [x] Sentiment analysis
- [x] Text-to-speech
- [x] Conversational AI interface
- [x] Responsive design

---

<div align="center">

**Built with ❤️ by [Vibhor Surana](https://github.com/Vibhor-Surana)**

[Report Bug](https://github.com/Vibhor-Surana/NewsFlash/issues) · [Request Feature](https://github.com/Vibhor-Surana/NewsFlash/issues) · [View Demo](https://github.com/Vibhor-Surana/NewsFlash)

</div>
- Screen reader compatibility
- Reduced motion support
- Focus indicators

## 🔧 Configuration

### Environment Variables
- `GEMINI_API_KEY`: Google Gemini API key for AI features
- `LANGSMITH_API_KEY`: LangSmith API key for conversation tracing
- `USE_AI_SUMMARY`: Enable/disable AI summarization (default: true)
- `DEFAULT_LANGUAGE`: Default language for summaries (en, hi, mr) (default: en)
- `LANGUAGE_FALLBACK_ENABLED`: Enable fallback to English for language failures (default: true)
- `SENTIMENT_ANALYSIS_ENABLED`: Enable sentiment analysis for articles (default: true)
- `SENTIMENT_DISPLAY_ENABLED`: Show sentiment indicators in UI (default: true)

### Customization
- **News Results**: Modify `NEWS_RESULTS_PER_TOPIC` in `config.py`
- **TTS Settings**: Adjust language and speed in `config.py`
- **Language Support**: Configure supported languages in `SUPPORTED_LANGUAGES`
- **Sentiment Settings**: Customize sentiment categories and fallback behavior
- **Rate Limiting**: Configure `RATE_LIMIT_DELAY` for API calls

## 📊 Performance Features

### Optimization
- **Lazy Loading**: Articles load progressively
- **Caching**: Session-based conversation state
- **Rate Limiting**: Intelligent API request management
- **Error Handling**: Graceful fallbacks for all services

### Monitoring
- **Logging**: Comprehensive application logging
- **LangSmith Integration**: AI conversation tracing
- **Error Tracking**: Detailed error reporting

## 🔧 Troubleshooting

### Language Issues
- **Language not working**: Check that `DEFAULT_LANGUAGE` is set to a supported language code (en, hi, mr)
- **TTS not working in Hindi/Marathi**: Ensure your browser supports the language, fallback to English will occur automatically
- **Summaries in wrong language**: Check language selector in header, preference is session-based

### Sentiment Analysis Issues
- **No sentiment indicators**: Check that `SENTIMENT_ANALYSIS_ENABLED=true` in your `.env` file
- **All articles show neutral**: This is normal fallback behavior when sentiment analysis fails
- **Sentiment seems incorrect**: Sentiment analysis is AI-generated and may not always be perfect

### Configuration Issues
- **Missing environment variables**: Copy `.env.example` to `.env` and fill in required values
- **Language fallback not working**: Ensure `LANGUAGE_FALLBACK_ENABLED=true` in configuration

## 🌐 Browser Support

- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile**: iOS Safari, Chrome Mobile, Samsung Internet
- **Features**: ES6+, Fetch API, CSS Grid, Flexbox
- **TTS Support**: Varies by browser and language, automatic fallback included

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Design Inspiration**: BBC, CNN, Reuters, The Guardian
- **AI Technology**: Google Gemini, LangChain, LangGraph
- **News Data**: DuckDuckGo Search API
- **UI Framework**: Bootstrap team
- **Icons**: Font Awesome

---

**NewsFlash** - Bringing AI-powered news discovery to everyone! 🚀