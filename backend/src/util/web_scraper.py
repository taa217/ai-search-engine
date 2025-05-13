import re
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import asyncio
from .logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

class WebScraperTool:
    """Tool for scraping and extracting content from web pages."""
    
    def __init__(self):
        # User agent to mimic a browser
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        # Settings for timeouts and retry logic
        self.timeout = 10  # seconds
        self.max_retries = 2
    
    async def scrape(self, url: str) -> Dict[str, Any]:
        """
        Scrape content from a URL.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dictionary with extracted content and metadata
        """
        logger.info(f"Scraping content from: {url}")
        try:
            # Validate URL
            if not self._is_valid_url(url):
                return {"error": "Invalid URL format", "url": url, "content": ""}
            
            # Fetch content
            html = await self._fetch_with_retry(url)
            if not html:
                return {"error": "Failed to retrieve page", "url": url, "content": ""}
            
            # Extract content
            soup = BeautifulSoup(html, 'html.parser')
            
            # Get title
            title = self._extract_title(soup)
            
            # Extract main content
            main_content = self._extract_main_content(soup)
            
            # Get metadata
            metadata = self._extract_metadata(soup)
            
            return {
                "url": url,
                "title": title,
                "content": main_content,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {"error": str(e), "url": url, "content": ""}
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except Exception:
            return False
    
    async def _fetch_with_retry(self, url: str) -> Optional[str]:
        """Fetch URL content with retry logic."""
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, headers=self.headers, follow_redirects=True)
                    response.raise_for_status()
                    return response.text
            except httpx.TimeoutException:
                logger.warning(f"Timeout fetching {url}, attempt {attempt+1}/{self.max_retries+1}")
                if attempt < self.max_retries:
                    await asyncio.sleep(1)  # Wait before retrying
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching {url}: {e}")
                return None
            except Exception as e:
                logger.error(f"Error fetching {url}: {str(e)}")
                return None
        
        return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the title from a webpage."""
        if soup.title:
            return soup.title.string.strip() if soup.title.string else ""
        
        # Try to find h1 if title tag is missing
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()
        
        return "No title found"
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract the main content from a webpage.
        Uses heuristics to find the main content area.
        """
        # Remove script, style, nav, and other non-content elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Try to find main content container
        main_candidates = []
        
        # Look for semantic HTML5 elements first
        semantic_elements = soup.find_all(['article', 'main', 'section'])
        main_candidates.extend(semantic_elements)
        
        # Look for common content div classes/ids
        content_selectors = [
            '#content', '.content', '#main', '.main', '.post', '.article',
            '.entry', '.post-content', '.article-content', '.entry-content'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                main_candidates.append(element)
        
        # Choose the candidate with the most text
        if main_candidates:
            main_candidates.sort(key=lambda x: len(x.get_text()), reverse=True)
            main_text = main_candidates[0].get_text(separator=' ', strip=True)
        else:
            # Fallback to body content if no good candidates
            main_text = soup.body.get_text(separator=' ', strip=True) if soup.body else ""
        
        # Clean up text
        main_text = self._clean_text(main_text)
        
        # Limit text length to avoid very large responses
        if len(main_text) > 10000:
            main_text = main_text[:10000] + "... (content truncated)"
        
        return main_text
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove any remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract metadata from the webpage."""
        metadata = {}
        
        # Extract meta tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            # Description
            if tag.get('name') == 'description' or tag.get('property') == 'og:description':
                metadata['description'] = tag.get('content', '')
            
            # Keywords
            if tag.get('name') == 'keywords':
                metadata['keywords'] = tag.get('content', '')
            
            # Author
            if tag.get('name') == 'author':
                metadata['author'] = tag.get('content', '')
            
            # OpenGraph data
            if tag.get('property') and tag.get('property').startswith('og:'):
                prop = tag.get('property')[3:]  # Remove 'og:' prefix
                metadata[f'og_{prop}'] = tag.get('content', '')
        
        return metadata
