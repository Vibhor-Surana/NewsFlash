import logging
import requests
from typing import Optional, Dict
import trafilatura
from bs4 import BeautifulSoup
from newspaper import Article
import re

logger = logging.getLogger(__name__)

class ArticleExtractor:
    def __init__(self):
        logger.info("ArticleExtractor initialized successfully with newspaper3k")

    def extract_full_article(self, url: str) -> Optional[str]:
        """Extract the full article content from a URL using newspaper3k"""
        try:
            logger.info(f"Extracting full article from: {url}")
            
            # First try with newspaper3k - excellent for article extraction
            try:
                article = Article(url)
                article.download()
                article.parse()
                
                logger.info(f"Newspaper3k raw text length: {len(article.text) if article.text else 0}")
                
                if article.text and len(article.text.strip()) > 100:
                    formatted_text = self._format_newspaper_content(article.text)
                    logger.info(f"Successfully extracted article using newspaper3k: {len(formatted_text)} characters (original: {len(article.text)})")
                    return formatted_text
                else:
                    logger.warning(f"Newspaper3k extracted text too short or empty: {len(article.text) if article.text else 0} characters")
                    
            except Exception as e:
                logger.warning(f"Newspaper3k extraction failed: {e}, trying trafilatura fallback")
            
            # Fallback to trafilatura
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                text = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
                logger.info(f"Trafilatura raw text length: {len(text) if text else 0}")
                
                if text and len(text.strip()) > 100:
                    formatted_text = self._format_newspaper_content(text)
                    logger.info(f"Successfully extracted article using trafilatura: {len(formatted_text)} characters (original: {len(text)})")
                    return formatted_text
                else:
                    logger.warning(f"Trafilatura extracted text too short or empty: {len(text) if text else 0} characters")
            else:
                logger.warning("Trafilatura failed to download content")
            
            # Final fallback to BeautifulSoup
            logger.warning("Both newspaper3k and trafilatura failed, trying BeautifulSoup fallback")
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
                element.decompose()
            
            # Try to find the main content area
            content_selectors = [
                'article', '[role="main"]', '.article-content', 
                '.post-content', '.entry-content', '.content', 'main'
            ]
            
            article_content = None
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    article_content = elements[0]
                    break
            
            if not article_content:
                article_content = soup.find('body')
            
            if article_content:
                text = article_content.get_text(separator='\n', strip=True)
                formatted_text = self._format_newspaper_content(text)
                
                if len(formatted_text.strip()) > 100:
                    logger.info(f"Successfully extracted article using BeautifulSoup: {len(formatted_text)} characters")
                    return formatted_text
            
            logger.warning(f"Could not extract meaningful content from {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting article from {url}: {e}")
            return None

    def _format_newspaper_content(self, text: str) -> str:
        """Format article content using newspaper3k-style formatting (NO API calls)"""
        try:
            # Clean up the text
            text = text.strip()
            original_length = len(text)
            
            # Remove excessive whitespace and normalize line breaks
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple line breaks to double
            text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single space
            
            # Split into paragraphs
            paragraphs = text.split('\n\n')
            formatted_paragraphs = []
            filtered_count = 0
            
            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                
                # Skip very short lines (likely navigation/ads)
                if len(paragraph) < 20:
                    filtered_count += 1
                    continue
                    
                # Skip lines that look like navigation or ads
                if self._is_likely_noise(paragraph):
                    filtered_count += 1
                    logger.debug(f"Filtered noise paragraph: {paragraph[:50]}...")
                    continue
                
                # Clean up the paragraph
                paragraph = re.sub(r'\s+', ' ', paragraph)  # Normalize whitespace
                paragraph = paragraph.strip()
                
                # Only keep substantial paragraphs
                if len(paragraph) > 30:
                    formatted_paragraphs.append(paragraph)
                else:
                    filtered_count += 1
            
            # Join paragraphs with proper spacing
            formatted_text = '\n\n'.join(formatted_paragraphs)
            
            logger.info(f"Formatting stats - Original: {original_length} chars, Filtered {filtered_count} paragraphs, Final: {len(formatted_text)} chars")
            
            # Limit to reasonable length for display
            if len(formatted_text) > 25000:
                formatted_text = formatted_text[:25000] + "\n\n[Article truncated for display]"
                logger.info("Article truncated due to length limit (25000 chars)")
            
            return formatted_text
            
        except Exception as e:
            logger.error(f"Error formatting article text: {e}")
            return text

    def _is_likely_noise(self, line: str) -> bool:
        """Check if a line is likely to be noise (ads, navigation, etc.)"""
        noise_patterns = [
            'subscribe', 'newsletter', 'advertisement', 'click here', 'read more',
            'sign up', 'follow us', 'share this', 'cookie', 'privacy policy',
            'terms of service', 'related articles', 'trending now', 'most popular',
            'you may also like', 'recommended for you', 'advertisement', 'sponsored',
            'continue reading', 'view comments', 'leave a comment', 'social media',
            'facebook', 'twitter', 'instagram', 'linkedin', 'download app',
            'get notifications', 'breaking news alert', 'newsletter signup'
        ]
        
        line_lower = line.lower()
        
        # Check for noise patterns
        if any(pattern in line_lower for pattern in noise_patterns):
            return True
            
        # Check for very short lines (likely navigation)
        if len(line.strip()) < 20:
            return True
            
        # Check for lines that are mostly punctuation or numbers
        if len(re.sub(r'[^a-zA-Z]', '', line)) < len(line) * 0.5:
            return True
            
        return False

    def get_readable_article(self, url: str, title: str = "") -> Dict[str, str]:
        """Get a readable version of the article with newspaper3k formatting (NO API calls)"""
        try:
            content = self.extract_full_article(url)
            
            if not content:
                return {
                    "content": "Sorry, I couldn't extract the full article content from this source. Please try opening the original source page.",
                    "formatted": False
                }
            
            # Content is already well-formatted by newspaper3k or our formatting function
            return {
                "content": content,
                "formatted": True  # Always true since newspaper3k provides good formatting
            }
                
        except Exception as e:
            logger.error(f"Error getting readable article: {e}")
            return {
                "content": "An error occurred while extracting the article content.",
                "formatted": False
            }

    def get_article_metadata(self, url: str) -> Dict[str, str]:
        """Extract article metadata using newspaper3k (NO API calls)"""
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            return {
                "title": article.title or "No title available",
                "authors": ", ".join(article.authors) if article.authors else "Unknown author",
                "publish_date": str(article.publish_date) if article.publish_date else "Unknown date",
                "summary": article.summary[:500] if article.summary else "No summary available",
                "keywords": ", ".join(article.keywords[:10]) if article.keywords else "No keywords",
                "top_image": article.top_image or "",
                "text_length": len(article.text) if article.text else 0
            }
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {url}: {e}")
            return {
                "title": "Error extracting title",
                "authors": "Unknown",
                "publish_date": "Unknown",
                "summary": "Could not extract summary",
                "keywords": "None",
                "top_image": "",
                "text_length": 0
            }


