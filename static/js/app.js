// News Assistant JavaScript Application

class NewsAssistant {
    constructor() {
        this.currentTopics = [];
        this.isSearching = false;
        this.currentAudio = null;
        this.currentFullArticle = null;
        this.themeKey = 'newsflash-theme';
        this.compactKey = 'newsflash-compact';
        this.currentLanguage = 'en';
        this.supportedLanguages = {};
        
        this.initializeEventListeners();
        this.initializeApp();
    }
    
    initializeEventListeners() {
        // Chat input handling
        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        
        document.getElementById('send-btn').addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Search and reset buttons
        document.getElementById('search-btn').addEventListener('click', () => {
            this.searchNews();
        });
        
        document.getElementById('reset-btn').addEventListener('click', () => {
            this.resetConversation();
        });
        
        // Article modal TTS button
        document.getElementById('tts-article-btn').addEventListener('click', () => {
            this.playFullArticleTTS();
        });
        
        // Audio ended event
        document.getElementById('tts-audio').addEventListener('ended', () => {
            this.stopAllTTS();
        });

        // Theme toggle
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // Compact layout toggle
        const compactToggle = document.getElementById('compact-toggle');
        if (compactToggle) {
            compactToggle.addEventListener('click', () => this.toggleCompact());
        }
    }
    
    initializeApp() {
        console.log('News Assistant initialized');
        this.initializeConnectionMonitoring();
        this.restorePreferences();
        this.initializeLanguageSelector();
        
        // Check if service worker is supported for offline functionality
        if ('serviceWorker' in navigator) {
            console.log('Service Worker supported');
        }
    }

    restorePreferences() {
        try {
            const storedTheme = localStorage.getItem(this.themeKey);
            if (storedTheme === 'dark') {
                document.body.classList.add('theme-dark');
                document.body.classList.remove('theme-light');
                const btn = document.getElementById('theme-toggle');
                if (btn) {
                    btn.setAttribute('aria-pressed', 'true');
                    btn.innerHTML = '<i class="fas fa-sun"></i>';
                }
            }
            const storedCompact = localStorage.getItem(this.compactKey);
            if (storedCompact === 'true') {
                document.body.classList.add('compact');
                const cbtn = document.getElementById('compact-toggle');
                if (cbtn) cbtn.setAttribute('aria-pressed', 'true');
            }
        } catch (e) {
            console.warn('Preference restore failed', e);
        }
    }

    toggleTheme() {
        const isDark = document.body.classList.toggle('theme-dark');
        document.body.classList.toggle('theme-light', !isDark);
        const btn = document.getElementById('theme-toggle');
        if (btn) {
            btn.setAttribute('aria-pressed', String(isDark));
            btn.innerHTML = isDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
        }
        try { localStorage.setItem(this.themeKey, isDark ? 'dark' : 'light'); } catch {}
    }

    toggleCompact() {
        const compact = document.body.classList.toggle('compact');
        const btn = document.getElementById('compact-toggle');
        if (btn) btn.setAttribute('aria-pressed', String(compact));
        try { localStorage.setItem(this.compactKey, String(compact)); } catch {}
    }
    
    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Add user message to chat
        this.addMessageToChat(message, 'user');
        
        // Clear input
        input.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            const response = await this.fetchWithRetry('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Remove typing indicator
            this.removeTypingIndicator();
            
            // Add bot response
            this.addMessageToChat(data.response, 'bot');
            
            // Update topics display
            this.updateTopicsDisplay(data.topics);
            
            // Show search button if ready
            console.log('Chat response data:', data);
            if (data.should_search) {
                console.log('should_search is true, triggering autoSearchNews');
                document.getElementById('search-btn').style.display = 'inline-block';
                this.autoSearchNews();
            } else {
                console.log('should_search is false, not triggering search');
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.removeTypingIndicator();
            this.addMessageToChat('Sorry, I encountered an error. Please try again.', 'bot');
        }
    }
    
    addMessageToChat(message, sender) {
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (sender === 'bot') {
            contentDiv.innerHTML = `<i class="fas fa-sparkles me-2"></i>${message}`;
        } else {
            contentDiv.innerHTML = `<i class="fas fa-user me-2"></i>${message}`;
        }
        
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom with smooth animation
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }
    
    showTypingIndicator() {
        const chatMessages = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot-message typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-content">
                <i class="fas fa-brain me-2"></i>
                <span class="typing-dots">
                    <span>.</span><span>.</span><span>.</span>
                </span>
                <span class="ms-2">Thinking...</span>
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }
    
    removeTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    updateTopicsDisplay(topics) {
        this.currentTopics = topics;
        const topicsDisplay = document.getElementById('topics-display');
        const topicsList = document.getElementById('topics-list');
        
        if (topics.length > 0) {
            topicsDisplay.style.display = 'block';
            topicsList.innerHTML = topics.map((topic, index) => 
                `<span class="badge" style="animation-delay: ${index * 0.1}s">${topic}</span>`
            ).join('');
        } else {
            topicsDisplay.style.display = 'none';
        }
    }
    
    async autoSearchNews() {
        // Automatically search for news after a brief delay
        console.log('autoSearchNews called, currentTopics:', this.currentTopics);
        setTimeout(() => {
            console.log('setTimeout callback executing, currentTopics:', this.currentTopics);
            this.searchNews();
        }, 1000);
    }
    
    async searchNews() {
        if (this.isSearching || this.currentTopics.length === 0) {
            console.log('Search blocked:', { isSearching: this.isSearching, topicsLength: this.currentTopics.length });
            return;
        }
        
        this.isSearching = true;
        this.showLoadingSpinner();
        this.updateNewsStatus('Searching for news articles...');
        
        console.log('Starting news search for topics:', this.currentTopics);
        
        try {
            const response = await fetch('/search_news', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    language: this.currentLanguage
                })
            });
            
            const data = await response.json();
            console.log('Search response:', data);
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            if (data.success) {
                console.log('Displaying results:', data.results);
                this.displayNewsResults(data.results);
                this.updateNewsStatus(`Found news for ${Object.keys(data.results).length} topics`);
            }
            
        } catch (error) {
            console.error('Error searching news:', error);
            this.showError('An error occurred while searching for news. Please try again.');
        } finally {
            this.isSearching = false;
            this.hideLoadingSpinner();
        }
    }
    
    displayNewsResults(results) {
        const welcomeMessage = document.getElementById('welcome-message');
        const newsResults = document.getElementById('news-results');
        
        // Hide welcome message and show results
        welcomeMessage.style.display = 'none';
        newsResults.style.display = 'block';
        newsResults.innerHTML = '';
        
        // Display news for each topic
        Object.keys(results).forEach(topic => {
            const articles = results[topic];
            const topicSection = this.createTopicSection(topic, articles);
            newsResults.appendChild(topicSection);
        });
    }
    
    createTopicSection(topic, articles) {
        const section = document.createElement('div');
        section.className = 'news-topic-section';
        
        const header = document.createElement('h3');
        header.className = 'topic-header';
        header.innerHTML = `<i class="fas fa-newspaper me-2"></i>${topic.toUpperCase()}`;
        
        const articlesContainer = document.createElement('div');
        articlesContainer.className = 'p-3';
        
        // Add articles
        console.log(`Creating section for topic: ${topic}, articles:`, articles);
        if (articles && articles.length > 0) {
            articles.forEach((article) => {
                const articleElement = this.createArticleElement(article);
                articlesContainer.appendChild(articleElement);
            });
        } else {
            console.log(`No articles found for topic: ${topic}`);
            const noArticlesDiv = document.createElement('div');
            noArticlesDiv.className = 'alert alert-info';
            noArticlesDiv.innerHTML = '<i class="fas fa-info-circle me-2"></i>No articles found for this topic.';
            articlesContainer.appendChild(noArticlesDiv);
        }
        
        // Add load more button
        const loadMoreBtn = document.createElement('button');
        loadMoreBtn.className = 'btn load-more-btn';
        loadMoreBtn.innerHTML = '<i class="fas fa-plus me-1"></i>Load more on this topic';
        loadMoreBtn.onclick = () => this.loadMoreArticles(topic, articlesContainer, loadMoreBtn);
        
        articlesContainer.appendChild(loadMoreBtn);
        
        section.appendChild(header);
        section.appendChild(articlesContainer);
        
        return section;
    }
    
    createSentimentIndicator(sentiment) {
        const sentimentData = this.getSentimentData(sentiment);
        
        return `
            <div class="sentiment-indicator ${sentimentData.class}" title="${sentimentData.tooltip}">
                <i class="sentiment-icon ${sentimentData.icon}"></i>
                <span class="sentiment-text">${sentimentData.text}</span>
                <div class="sentiment-tooltip">${sentimentData.tooltip}</div>
            </div>
        `;
    }
    
    getSentimentData(sentiment) {
        const sentimentMap = {
            'positive': {
                class: 'positive',
                icon: 'fas fa-smile',
                text: 'Positive',
                tooltip: 'This article has a positive sentiment'
            },
            'negative': {
                class: 'negative',
                icon: 'fas fa-frown',
                text: 'Negative',
                tooltip: 'This article has a negative sentiment'
            },
            'neutral': {
                class: 'neutral',
                icon: 'fas fa-meh',
                text: 'Neutral',
                tooltip: 'This article has a neutral sentiment'
            }
        };
        
        return sentimentMap[sentiment] || sentimentMap['neutral'];
    }
    
    createArticleElement(article) {
        const articleDiv = document.createElement('div');
        articleDiv.className = 'news-article card mb-3';
        
        const formattedDate = this.formatDate(article.date);
        const sentimentIndicator = this.createSentimentIndicator(article.sentiment || 'neutral');
        
        articleDiv.innerHTML = `
            <div class="card-header">
                <div class="article-header">
                    <div class="article-title-section">
                        <h5 class="card-title mb-1">${article.title}</h5>
                        <small class="text-muted">
                            <i class="fas fa-globe me-1"></i>${article.source || 'Unknown Source'}
                            ${formattedDate ? `<i class="fas fa-clock ms-2 me-1"></i>${formattedDate}` : ''}
                        </small>
                    </div>
                    <div class="article-meta-section">
                        ${sentimentIndicator}
                    </div>
                </div>
            </div>
            <div class="card-body">
                <div class="article-summary">
                    ${article.summary || article.body || 'No summary available.'}
                </div>
            </div>
            <div class="card-footer article-actions p-0">
                <div class="btn-group w-100" role="group">
                    <button type="button" class="btn btn-outline-primary" onclick="window.open('${article.url}', '_blank')">
                        <i class="fas fa-external-link-alt me-1"></i>
                        Open Source
                    </button>
                    <button type="button" class="btn btn-outline-info" onclick="newsApp.showFullArticle('${article.url}', '${article.title.replace(/'/g, "\\'")}')">
                        <i class="fas fa-book-open me-1"></i>
                        Read Full Article
                    </button>
                    <button type="button" class="btn btn-outline-success tts-btn" onclick="newsApp.playTTS('${this.escapeHtml(article.summary || article.body)}', this)">
                        <i class="fas fa-volume-up me-1"></i>
                        Listen
                    </button>
                </div>
            </div>
        `;
        
        return articleDiv;
    }
    
    async loadMoreArticles(topic, container, button) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Loading...';
        
        try {
            const response = await fetch(`/load_more/${encodeURIComponent(topic)}`);
            const data = await response.json();
            
            if (data.success && data.articles.length > 0) {
                // Insert new articles before the load more button
                data.articles.forEach(article => {
                    const articleElement = this.createArticleElement(article);
                    container.insertBefore(articleElement, button);
                });
                
                button.innerHTML = '<i class="fas fa-plus me-1"></i>Load more on this topic';
                button.disabled = false;
            } else {
                button.innerHTML = '<i class="fas fa-check me-1"></i>No more articles';
                button.disabled = true;
            }
            
        } catch (error) {
            console.error('Error loading more articles:', error);
            button.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>Error loading';
            button.disabled = false;
        }
    }
    
    async showFullArticle(url, title) {
        const modal = new bootstrap.Modal(document.getElementById('articleModal'));
        const modalTitle = document.getElementById('articleModalLabel');
        const articleContent = document.getElementById('article-content');
        
        // Set title and show modal
        modalTitle.textContent = title;
        articleContent.innerHTML = `
            <div class="text-center p-3">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading article...</span>
                </div>
                <p class="mt-2">Extracting full article content...</p>
            </div>
        `;
        
        modal.show();
        
        try {
            const response = await fetch('/full_article', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url, title: title })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentFullArticle = data.content;
                articleContent.innerHTML = `
                    <div class="full-article-content">
                        ${data.content.replace(/\n/g, '<br>')}
                    </div>
                `;
            } else {
                throw new Error(data.error || 'Failed to load article');
            }
            
        } catch (error) {
            console.error('Error loading full article:', error);
            articleContent.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Failed to load the full article. Please try opening the source page instead.
                </div>
            `;
        }
    }
    
    async playTTS(text, button) {
        // If audio is already playing, stop it
        if (this.currentAudio && !this.currentAudio.paused) {
            this.stopAllTTS();
            return;
        }
        
        // Stop any currently playing audio
        this.stopAllTTS();
        
        if (!text) return;
        
        // Update button state
        button.classList.add('playing');
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Generating...';
        
        try {
            const response = await fetch('/tts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    text: text,
                    language: this.currentLanguage 
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const audio = document.getElementById('tts-audio');
                
                // Clear any existing event listeners and reset audio
                audio.pause();
                audio.currentTime = 0;
                audio.src = '';
                
                // Set new source
                audio.src = data.audio_url;
                
                // Set up event listeners with proper cleanup
                const endedHandler = () => {
                    console.log('Audio playback ended');
                    this.stopAllTTS();
                };
                
                const errorHandler = (e) => {
                    console.error('Audio error:', e);
                    this.stopAllTTS();
                    // Don't show error message for normal audio completion
                };
                
                const canPlayHandler = () => {
                    button.innerHTML = '<i class="fas fa-stop me-1"></i>Stop';
                    audio.play().then(() => {
                        this.currentAudio = audio;
                    }).catch((e) => {
                        console.error('Play error:', e);
                        this.stopAllTTS();
                    });
                };
                
                // Add event listeners
                audio.addEventListener('ended', endedHandler, { once: true });
                audio.addEventListener('error', errorHandler, { once: true });
                audio.addEventListener('canplay', canPlayHandler, { once: true });
                
                // Load the audio
                audio.load();
                
            } else {
                throw new Error(data.error || 'Failed to generate audio');
            }
            
        } catch (error) {
            console.error('Error generating TTS:', error);
            this.stopAllTTS();
            // Only show error for actual failures, not normal completion
            if (!error.message.includes('aborted')) {
                console.warn('TTS generation failed:', error.message);
            }
        }
    }
    
    async playFullArticleTTS() {
        if (!this.currentFullArticle) return;
        
        const button = document.getElementById('tts-article-btn');
        await this.playTTS(this.currentFullArticle, button);
    }
    
    stopAllTTS() {
        console.log('Stopping all TTS');
        
        // Stop current audio
        if (this.currentAudio) {
            try {
                this.currentAudio.pause();
                this.currentAudio.currentTime = 0;
                this.currentAudio.src = '';
            } catch (e) {
                console.log('Audio cleanup error (normal):', e.message);
            }
            this.currentAudio = null;
        }
        
        // Also stop the main audio element
        const mainAudio = document.getElementById('tts-audio');
        if (mainAudio) {
            try {
                mainAudio.pause();
                mainAudio.currentTime = 0;
                mainAudio.src = '';
                // Remove all event listeners
                mainAudio.removeEventListener('ended', this.stopAllTTS);
                mainAudio.removeEventListener('error', this.stopAllTTS);
            } catch (e) {
                console.log('Main audio cleanup error (normal):', e.message);
            }
        }
        
        // Reset all TTS buttons
        document.querySelectorAll('.tts-btn').forEach(btn => {
            btn.classList.remove('playing');
            btn.innerHTML = '<i class="fas fa-volume-up me-1"></i>Listen';
        });
        
        // Reset article TTS button
        const articleBtn = document.getElementById('tts-article-btn');
        if (articleBtn) {
            articleBtn.classList.remove('playing');
            articleBtn.innerHTML = '<i class="fas fa-volume-up me-1"></i>Read Article';
        }
    }
    
    async resetConversation() {
        try {
            await fetch('/reset_conversation', { method: 'POST' });
            
            // Reset UI
            document.getElementById('chat-messages').innerHTML = `
                <div class="message bot-message">
                    <div class="message-content">
                        <i class="fas fa-sparkles me-2"></i>
                        Hello! I'm your AI news assistant. What topics would you like to explore today?
                    </div>
                </div>
            `;
            
            document.getElementById('topics-display').style.display = 'none';
            document.getElementById('search-btn').style.display = 'none';
            document.getElementById('news-results').style.display = 'none';
            document.getElementById('welcome-message').style.display = 'block';
            
            this.currentTopics = [];
            this.stopAllTTS();
            
            // Hide status container on reset
            const statusContainer = document.getElementById('news-status-container');
            if (statusContainer) {
                statusContainer.style.display = 'none';
            }
            
        } catch (error) {
            console.error('Error resetting conversation:', error);
        }
    }
    
    showLoadingSpinner() {
        document.getElementById('loading-spinner').style.display = 'block';
        document.getElementById('welcome-message').style.display = 'none';
        document.getElementById('news-results').style.display = 'none';
    }
    
    hideLoadingSpinner() {
        document.getElementById('loading-spinner').style.display = 'none';
    }
    
    updateNewsStatus(message) {
        const statusElement = document.getElementById('news-status');
        const statusContainer = document.getElementById('news-status-container');
        
        if (statusElement && statusContainer) {
            statusElement.textContent = message;
            statusContainer.style.display = 'block';
        } else {
            console.warn('News status elements not found');
        }
    }
    
    showError(message) {
        const newsResults = document.getElementById('news-results');
        newsResults.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
        `;
        newsResults.style.display = 'block';
        document.getElementById('welcome-message').style.display = 'none';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML.replace(/'/g, "\\'").replace(/"/g, '\\"');
    }
    
    formatDate(dateString) {
        if (!dateString) return '';
        
        try {
            const date = new Date(dateString);
            
            // Check if date is valid
            if (isNaN(date.getTime())) {
                return dateString; // Return original if can't parse
            }
            
            const now = new Date();
            const diffMs = now - date;
            const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
            const diffDays = Math.floor(diffHours / 24);
            
            // Show relative time for recent articles
            if (diffHours < 1) {
                const diffMinutes = Math.floor(diffMs / (1000 * 60));
                return diffMinutes <= 1 ? 'Just now' : `${diffMinutes} minutes ago`;
            } else if (diffHours < 24) {
                return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
            } else if (diffDays < 7) {
                return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
            } else {
                // Show formatted date for older articles
                return date.toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }
        } catch (error) {
            console.warn('Error formatting date:', dateString, error);
            return dateString; // Return original if error
        }
    }
    
    // Network error handling
    async fetchWithRetry(url, options, maxRetries = 3) {
        for (let i = 0; i < maxRetries; i++) {
            try {
                const response = await fetch(url, options);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response;
            } catch (error) {
                if (i === maxRetries - 1) throw error;
                
                // Wait before retry (exponential backoff)
                await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
                console.warn(`Retry ${i + 1}/${maxRetries} for ${url}`);
            }
        }
    }
    
    // Connection status monitoring
    initializeConnectionMonitoring() {
        window.addEventListener('online', () => {
            this.showConnectionStatus('Connected', 'success');
        });
        
        window.addEventListener('offline', () => {
            this.showConnectionStatus('Offline - Check your connection', 'error');
        });
    }
    
    showConnectionStatus(message, type) {
        const statusDiv = document.createElement('div');
        statusDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} position-fixed top-0 start-50 translate-middle-x mt-3`;
        statusDiv.style.zIndex = '9999';
        statusDiv.innerHTML = `<i class="fas fa-${type === 'success' ? 'check' : 'exclamation-triangle'} me-2"></i>${message}`;
        
        document.body.appendChild(statusDiv);
        
        setTimeout(() => {
            statusDiv.remove();
        }, 3000);
    }
    
    // Language Management Methods
    async initializeLanguageSelector() {
        try {
            // Load supported languages from server
            await this.loadSupportedLanguages();
            
            // Populate language dropdown
            this.populateLanguageDropdown();
            
            // Set up event listeners for language selection
            this.setupLanguageEventListeners();
            
            console.log('Language selector initialized');
        } catch (error) {
            console.error('Error initializing language selector:', error);
        }
    }
    
    async loadSupportedLanguages() {
        try {
            const response = await this.fetchWithRetry('/get-languages');
            const data = await response.json();
            
            if (data.success) {
                this.supportedLanguages = data.languages;
                this.currentLanguage = data.current_language || 'en';
                
                // Update button text with current language
                this.updateLanguageButtonText();
            } else {
                throw new Error('Failed to load supported languages');
            }
        } catch (error) {
            console.error('Error loading supported languages:', error);
            // Fallback to default languages
            this.supportedLanguages = {
                'en': { name: 'English', native: 'English' },
                'hi': { name: 'Hindi', native: 'हिंदी' },
                'mr': { name: 'Marathi', native: 'मराठी' }
            };
            this.currentLanguage = 'en';
        }
    }
    
    populateLanguageDropdown() {
        const languageMenu = document.querySelector('.language-menu');
        if (!languageMenu) return;
        
        // Clear existing items (keep header and divider)
        const existingItems = languageMenu.querySelectorAll('.language-item');
        existingItems.forEach(item => item.remove());
        
        // Add language options
        Object.entries(this.supportedLanguages).forEach(([code, lang]) => {
            const listItem = document.createElement('li');
            listItem.className = 'language-item';
            
            const button = document.createElement('button');
            button.className = `dropdown-item ${code === this.currentLanguage ? 'active' : ''}`;
            button.type = 'button';
            button.dataset.language = code;
            
            // Add flag emoji based on language
            const flagEmoji = this.getLanguageFlag(code);
            
            button.innerHTML = `
                <span class="language-flag">${flagEmoji}</span>
                <div class="language-names">
                    <span class="language-name">${lang.name}</span>
                    <span class="language-native">${lang.native}</span>
                </div>
            `;
            
            listItem.appendChild(button);
            languageMenu.appendChild(listItem);
        });
    }
    
    getLanguageFlag(languageCode) {
        const flags = {
            'en': '🇺🇸',
            'hi': '🇮🇳',
            'mr': '🇮🇳'
        };
        return flags[languageCode] || '🌐';
    }
    
    setupLanguageEventListeners() {
        // Add click event listeners to language options
        document.addEventListener('click', (e) => {
            if (e.target.closest('.dropdown-item[data-language]')) {
                const button = e.target.closest('.dropdown-item[data-language]');
                const languageCode = button.dataset.language;
                this.changeLanguage(languageCode);
            }
        });
    }
    
    async changeLanguage(languageCode) {
        if (languageCode === this.currentLanguage) {
            return; // No change needed
        }
        
        const languageBtn = document.getElementById('languageDropdown');
        const originalText = languageBtn.querySelector('.language-text').textContent;
        
        try {
            // Show loading state
            languageBtn.classList.add('loading');
            languageBtn.querySelector('.language-text').textContent = 'Changing';
            
            // Send request to server
            const response = await this.fetchWithRetry('/set-language', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ language: languageCode })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update current language
                this.currentLanguage = languageCode;
                
                // Update UI with animation
                this.updateLanguageButtonText();
                this.updateLanguageDropdownSelection();
                
                // Add success animation to button
                languageBtn.classList.add('success');
                setTimeout(() => languageBtn.classList.remove('success'), 600);
                
                // Show success feedback
                this.showLanguageChangeSuccess(data.message);
                
                // Close dropdown
                const dropdown = bootstrap.Dropdown.getInstance(languageBtn);
                if (dropdown) dropdown.hide();
                
                console.log(`Language changed to: ${languageCode}`);
            } else {
                throw new Error(data.error || 'Failed to change language');
            }
            
        } catch (error) {
            console.error('Error changing language:', error);
            
            // Restore original text
            languageBtn.querySelector('.language-text').textContent = originalText;
            
            // Show error message
            this.showLanguageChangeError('Failed to change language. Please try again.');
            
        } finally {
            // Remove loading state
            languageBtn.classList.remove('loading');
        }
    }
    
    updateLanguageButtonText() {
        const languageBtn = document.getElementById('languageDropdown');
        const languageText = languageBtn.querySelector('.language-text');
        
        if (this.supportedLanguages[this.currentLanguage]) {
            languageText.textContent = this.supportedLanguages[this.currentLanguage].name;
        }
    }
    
    updateLanguageDropdownSelection() {
        // Update active state in dropdown
        document.querySelectorAll('.dropdown-item[data-language]').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.language === this.currentLanguage) {
                item.classList.add('active');
            }
        });
    }
    
    showLanguageChangeSuccess(message) {
        this.showLanguageToast(message, 'success', 'check');
    }
    
    showLanguageChangeError(message) {
        this.showLanguageToast(message, 'danger', 'exclamation-triangle');
    }
    
    showLanguageToast(message, type, icon) {
        // Remove any existing language toasts
        document.querySelectorAll('.language-toast').forEach(toast => toast.remove());
        
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} language-toast`;
        toast.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-${icon} me-2"></i>
                <span>${message}</span>
                <button type="button" class="btn-close ms-auto" aria-label="Close"></button>
            </div>
        `;
        
        // Add close functionality
        toast.querySelector('.btn-close').addEventListener('click', () => {
            toast.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => toast.remove(), 300);
        });
        
        document.body.appendChild(toast);
        
        // Auto-remove after delay
        const delay = type === 'danger' ? 4000 : 3000;
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.animation = 'slideOutRight 0.3s ease-in';
                setTimeout(() => toast.remove(), 300);
            }
        }, delay);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.newsApp = new NewsAssistant();
});

// Add some CSS for typing indicator animation
const style = document.createElement('style');
style.textContent = `
    .typing-dots span {
        animation: typing 1.4s infinite ease-in-out;
        opacity: 0;
    }
    
    .typing-dots span:nth-child(1) {
        animation-delay: 0.2s;
    }
    
    .typing-dots span:nth-child(2) {
        animation-delay: 0.4s;
    }
    
    .typing-dots span:nth-child(3) {
        animation-delay: 0.6s;
    }
    
    @keyframes typing {
        0%, 60%, 100% {
            opacity: 0;
        }
        30% {
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);
