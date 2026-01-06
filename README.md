# NewsFlash - AI-Powered News Assistant 📰

A modern, responsive news website that combines AI conversation with real-time news search and text-to-speech functionality.

## ✨ Features

### 🤖 AI-Powered Chat Interface
- **Intelligent Conversation**: Natural language interaction to collect news topics
- **Smart Topic Collection**: AI understands and organizes your interests
- **Conversational Flow**: Guided experience from topic selection to news discovery

### 📰 Real-Time News Search
- **Multi-Topic Search**: Search multiple news topics simultaneously
- **AI-Generated Summaries**: Concise, intelligent summaries of articles
- **Sentiment Analysis**: Visual indicators showing emotional tone (positive, negative, neutral)
- **Source Attribution**: Clear source and date information
- **Load More**: Infinite scroll for additional articles

### 🌍 Multi-Language Support
- **Language Selection**: Choose from English, Hindi, or Marathi for summaries
- **Localized Content**: AI-generated summaries in your preferred language
- **Language Persistence**: Your language preference is remembered during the session
- **Fallback Support**: Automatic fallback to English if target language fails

### 🎧 Multi-Language Text-to-Speech
- **Article Reading**: Listen to article summaries and full content
- **Language-Aware Audio**: TTS in English, Hindi, or Marathi
- **High-Quality Audio**: Clear, natural-sounding speech synthesis
- **Playback Controls**: Start, stop, and manage audio playback

### 🎨 Professional Design
- **News Site Inspired**: Color scheme based on BBC, CNN, Reuters
- **High Contrast**: Excellent readability with professional colors
- **Responsive Layout**: Works perfectly on desktop, tablet, and mobile
- **Accessibility**: WCAG compliant with keyboard navigation support

## 🚀 Technology Stack

### Backend
- **Flask**: Python web framework
- **LangGraph**: AI conversation management
- **Google Gemini**: AI language model for summaries
- **DuckDuckGo Search**: Real-time news search
- **SQLAlchemy**: Database management
- **gTTS**: Text-to-speech generation

### Frontend
- **Bootstrap 5**: Responsive UI framework
- **Vanilla JavaScript**: Modern ES6+ features
- **Font Awesome**: Professional icons
- **Inter Font**: Clean, readable typography

### AI & Data
- **LangSmith**: AI conversation tracing
- **Trafilatura**: Article content extraction
- **BeautifulSoup**: HTML parsing fallback

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Setup
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd newsflash
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Copy the example file and add your API keys:
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` and replace the placeholder values:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key
   LANGSMITH_API_KEY=your_actual_langsmith_api_key
   LANGSMITH_PROJECT=news-website
   
   # Optional: Configure language and sentiment settings
   DEFAULT_LANGUAGE=en
   SENTIMENT_ANALYSIS_ENABLED=true
   LANGUAGE_FALLBACK_ENABLED=true
   ```
   
   **Get your API keys:**
   - Gemini API: https://makersuite.google.com/app/apikey
   - LangSmith API: https://smith.langchain.com/

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   Navigate to `http://localhost:5000`

## 📱 Usage

### Getting Started
1. **Start a Conversation**: Type a news topic in the chat (e.g., "technology", "sports")
2. **Add More Topics**: Continue adding topics or say "no" to search
3. **Browse Results**: View AI-summarized articles organized by topic
4. **Read Full Articles**: Click "Read Full Article" for complete content
5. **Listen**: Use the "Listen" button for text-to-speech playback

### Chat Commands
- **Topic names**: "technology", "politics", "sports", etc.
- **Stop adding**: "no", "done", "search", "stop"
- **Reset**: Use the "Reset Chat" button to start over

### Language & Sentiment Features

#### Multi-Language Support
- **Language Selection**: Use the language dropdown in the header to select your preferred language
- **Supported Languages**: 
  - English (en) - Default
  - Hindi (हिंदी) - hi
  - Marathi (मराठी) - mr
- **Language Persistence**: Your selection is remembered for the current session
- **Automatic Fallback**: If AI fails in your selected language, it falls back to English

#### Sentiment Analysis
- **Visual Indicators**: Each article shows a sentiment badge
  - 🟢 **Positive**: Green badge for optimistic/good news
  - 🔴 **Negative**: Red badge for concerning/problematic content
  - ⚪ **Neutral**: Gray badge for factual reporting
- **Hover Information**: Hover over sentiment badges for explanations
- **Fallback Behavior**: Defaults to neutral if sentiment analysis fails

#### Text-to-Speech Languages
- **Language Matching**: TTS automatically uses your selected language
- **Voice Quality**: High-quality voices for all supported languages
- **Fallback Support**: Falls back to English TTS if target language unavailable

## 🎯 Key Features Explained

### AI Conversation Management
- Uses LangGraph for sophisticated conversation flow
- Maintains context across multiple interactions
- Intelligent topic extraction and validation

### News Search & Summarization
- Real-time search using DuckDuckGo News API
- AI-powered article summarization with Gemini
- Fallback summaries for rate limiting scenarios

### Professional UI/UX
- **Color Scheme**: Inspired by major news websites
  - Primary Blue (#1e40af) - BBC-inspired
  - News Red (#dc2626) - CNN-inspired
  - Success Green (#059669) - Reuters-inspired
- **Typography**: Inter font for maximum readability
- **Layout**: 25/75 split for optimal content consumption

### Accessibility Features
- High contrast color ratios
- Keyboard navigation support
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