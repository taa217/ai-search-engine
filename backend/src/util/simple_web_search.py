import json
import os
from typing import List, Dict, Any
import httpx
from ..utils.simple_logger import setup_logger
import asyncio
import aiohttp
import requests
import time
import random
from urllib.parse import urlparse, quote_plus
import wikipedia
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

# Import DuckDuckGo search
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

# Import SerpAPI if available
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger(__name__)

class WebSearchTool:
    """Enhanced web search tool that can use multiple search providers"""
    
    def __init__(self):
        self.serpapi_key = os.getenv("SERPAPI_API_KEY")
        self.google_cse_id = os.getenv("GOOGLE_CSE_ID")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
        # Determine which search provider to use
        if self.serpapi_key and SERPAPI_AVAILABLE:
            logger.info("Using SerpAPI for web search")
            self.search_provider = "serpapi"
        elif DDGS_AVAILABLE:
            logger.info("Using DuckDuckGo for web search")
            self.search_provider = "duckduckgo"
        else:
            logger.info("Using fallback search method")
            self.search_provider = "fallback"
        
        # Initialize session
        self.session = None
        
    async def initialize_session(self):
        """Initialize aiohttp session for async requests"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
        
    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search the web using the configured provider"""
        try:
            logger.info(f"Searching for: {query} using {self.search_provider}")
            
            if self.search_provider == "serpapi":
                return await self._search_with_serpapi(query, num_results)
            elif self.search_provider == "duckduckgo":
                return await self._search_with_duckduckgo(query, num_results)
            else:
                return await self._search_with_fallback(query, num_results)
                
        except Exception as e:
            logger.error(f"Error during web search: {str(e)}")
            # Return empty results in case of error
            return []
    
    async def _search_with_serpapi(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using SerpAPI Google Search"""
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.serpapi_key,
            "num": num_results,
            "gl": "us",
            "hl": "en"
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "error" in results:
            logger.error(f"SerpAPI error: {results['error']}")
            return []
            
        organic_results = results.get("organic_results", [])
        
        formatted_results = []
        for result in organic_results[:num_results]:
            item = {
                "title": result.get("title", ""),
                "url": result.get("link", ""),
                "snippet": result.get("snippet", ""),
                "source": "serpapi"
            }
            
            # Extract thumbnail if available
            if "thumbnail" in result:
                item["imageUrl"] = result["thumbnail"]
                
            formatted_results.append(item)
            
        return formatted_results
    
    async def _search_with_duckduckgo(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo"""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))
                
            formatted_results = []
            for result in results:
                item = {
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", ""),
                    "source": "duckduckgo"
                }
                
                # Try to fetch image from the page
                try:
                    url_domain = urlparse(result.get("href", "")).netloc
                    item["imageUrl"] = f"https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://{url_domain}&size=128"
                except:
                    pass
                    
                formatted_results.append(item)
                
            return formatted_results
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {str(e)}")
            return await self._search_with_fallback(query, num_results)
    
    async def _search_with_fallback(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Fallback search method using a free API"""
        await self.initialize_session()
        
        try:
            encoded_query = quote_plus(query)
            url = f"https://ddg-api.herokuapp.com/search?query={encoded_query}&limit={num_results}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    results = await response.json()
                    
                    formatted_results = []
                    for result in results:
                        item = {
                            "title": result.get("title", ""),
                            "url": result.get("link", ""),
                            "snippet": result.get("snippet", ""),
                            "source": "fallback"
                        }
                        
                        # Try to get favicon
                        try:
                            url_domain = urlparse(result.get("link", "")).netloc
                            item["imageUrl"] = f"https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://{url_domain}&size=128"
                        except:
                            pass
                            
                        formatted_results.append(item)
                        
                    return formatted_results
                else:
                    logger.error(f"Fallback search API error: {response.status}")
                    return self._generate_mock_results(query, num_results)
        except Exception as e:
            logger.error(f"Fallback search error: {str(e)}")
            return self._generate_mock_results(query, num_results)
    
    def _generate_mock_results(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Generate mock results as a last resort fallback"""
        logger.warning(f"Using mock results for query: {query}")
        
        # Sample domains
        domains = [
            "wikipedia.org", "nytimes.com", "github.com", 
            "medium.com", "stackoverflow.com", "bbc.com",
            "cnn.com", "theguardian.com", "reuters.com"
        ]
        
        results = []
        for i in range(min(num_results, 5)):
            domain = random.choice(domains)
            results.append({
                "title": f"Result {i+1} for {query}",
                "url": f"https://www.{domain}/search?q={quote_plus(query)}",
                "snippet": f"This is a mock result for {query}. This search result would normally contain relevant information about your query from {domain}.",
                "source": "mock",
                "imageUrl": f"https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://{domain}&size=128"
            })
            
        return results
        
    async def fetch_page_content(self, url: str) -> str:
        """Fetch and extract text content from a webpage"""
        await self.initialize_session()
        
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.extract()
                    
                    # Get text
                    text = soup.get_text()
                    
                    # Break into lines and remove leading/trailing whitespace
                    lines = (line.strip() for line in text.splitlines())
                    
                    # Break multi-headlines into a single line
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    
                    # Remove blank lines
                    text = '\n'.join(chunk for chunk in chunks if chunk)
                    
                    return text[:5000]  # Limit to first 5000 chars
                else:
                    logger.error(f"Failed to fetch page content: {response.status}")
                    return ""
        except Exception as e:
            logger.error(f"Error fetching page content: {str(e)}")
            return ""
            
    async def extract_images_from_url(self, url: str, max_images: int = 3) -> List[Dict[str, str]]:
        """Extract images from a webpage"""
        await self.initialize_session()
        
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    images = []
                    for img in soup.find_all('img', limit=max_images*3):
                        src = img.get('src', '')
                        alt = img.get('alt', '')
                        
                        # Skip small icons, spacers, etc.
                        if not src or 'icon' in src.lower() or 'logo' in src.lower():
                            continue
                            
                        # Make relative URLs absolute
                        if src.startswith('/'):
                            parsed_url = urlparse(url)
                            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                            src = base_url + src
                            
                        images.append({
                            "url": src,
                            "alt": alt,
                            "source_url": url
                        })
                        
                        if len(images) >= max_images:
                            break
                            
                    return images
                else:
                    logger.error(f"Failed to extract images: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error extracting images: {str(e)}")
            return []


class WikipediaSearch:
    """Enhanced Wikipedia search tool"""
    
    def __init__(self):
        wikipedia.set_lang("en")
        self.logger = setup_logger(__name__ + ".WikipediaSearch")
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def search(self, query: str, num_results: int = 2) -> List[Dict[str, Any]]:
        """Search Wikipedia for the given query"""
        try:
            self.logger.info(f"Searching Wikipedia for: {query}")
            
            # Run Wikipedia search in a separate thread to not block the event loop
            loop = asyncio.get_event_loop()
            search_results = await loop.run_in_executor(
                None, lambda: wikipedia.search(query, results=min(num_results * 2, 10))
            )
            
            results = []
            for title in search_results[:num_results]:
                try:
                    # Get page summary in a separate thread
                    page = await loop.run_in_executor(
                        None, lambda t=title: wikipedia.page(t, auto_suggest=False)
                    )
                    
                    summary = await loop.run_in_executor(
                        None, lambda p=page: p.summary
                    )
                    
                    image_urls = page.images
                    image_url = next((img for img in image_urls if any(ext in img.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']) 
                                     and not any(skip in img.lower() for skip in ['icon', 'logo', 'svg'])), None)
                    
                    result = {
                        "title": page.title,
                        "url": page.url,
                        "snippet": summary[:200] + "..." if len(summary) > 200 else summary,
                        "source": "wikipedia",
                        "isRelevant": True
                    }
                    
                    if image_url:
                        result["imageUrl"] = image_url
                        
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Error fetching Wikipedia page {title}: {str(e)}")
                    continue
                    
            return results
        except Exception as e:
            self.logger.error(f"Wikipedia search error: {str(e)}")
            return []

# The legacy SimpleWebSearch for backward compatibility
class SimpleWebSearch(WebSearchTool):
    pass 