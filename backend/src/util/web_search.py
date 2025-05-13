import json
from typing import List, Dict, Any, Optional
import httpx
from langchain_community.utilities import GoogleSerperAPIWrapper, SerpAPIWrapper
from ..config import settings
from .logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

class WebSearchTool:
    """Tool for performing web searches using various search APIs."""
    
    def __init__(self):
        self.search_provider = self._initialize_search_provider()
        logger.info(f"Web search tool initialized with provider: {self._get_provider_name()}")
    
    def _initialize_search_provider(self):
        """Initialize the appropriate search provider based on available API keys."""
        if settings.SERPER_API_KEY:
            return GoogleSerperAPIWrapper(
                serper_api_key=settings.SERPER_API_KEY,
                k=8  # Number of results
            )
        elif settings.SERP_API_KEY:
            return SerpAPIWrapper(
                serpapi_api_key=settings.SERP_API_KEY,
                k=8
            )
        elif settings.GOOGLE_API_KEY and settings.GOOGLE_CSE_ID:
            # Use custom Google CSE implementation with direct API access
            return GoogleCustomSearch(
                api_key=settings.GOOGLE_API_KEY,
                cse_id=settings.GOOGLE_CSE_ID
            )
        else:
            # Fallback to a simple HTTP client for search (less reliable but no API key needed)
            return FallbackSearch()
    
    def _get_provider_name(self) -> str:
        """Get the name of the current search provider."""
        if hasattr(self.search_provider, "__class__"):
            return self.search_provider.__class__.__name__
        return "Unknown"
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Perform a web search with the given query.
        
        Args:
            query: The search query string
            
        Returns:
            List of search results with title, url, and snippet
        """
        try:
            logger.info(f"Performing web search: {query}")
            
            # Handle different provider interfaces
            if isinstance(self.search_provider, (GoogleSerperAPIWrapper, SerpAPIWrapper)):
                raw_results = self.search_provider.results(query)
                
                # Parse results based on provider
                if isinstance(self.search_provider, GoogleSerperAPIWrapper):
                    return self._parse_serper_results(raw_results)
                else:
                    return self._parse_serpapi_results(raw_results)
            else:
                # Use the custom implementation's search method
                return self.search_provider.search(query)
                
        except Exception as e:
            logger.error(f"Error in web search: {str(e)}")
            return [{"title": "Error", "url": "", "snippet": f"Error performing search: {str(e)}"}]
    
    def _parse_serper_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse results from Google Serper API."""
        parsed_results = []
        
        # Extract organic results
        organic = results.get("organic", [])
        for result in organic:
            parsed_results.append({
                "title": result.get("title", ""),
                "url": result.get("link", ""),
                "snippet": result.get("snippet", "")
            })
            
        return parsed_results
    
    def _parse_serpapi_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse results from SerpAPI."""
        parsed_results = []
        
        # Extract organic results
        organic = results.get("organic_results", [])
        for result in organic:
            parsed_results.append({
                "title": result.get("title", ""),
                "url": result.get("link", ""),
                "snippet": result.get("snippet", "")
            })
            
        return parsed_results


class GoogleCustomSearch:
    """Custom implementation of Google Custom Search using the official API."""
    
    def __init__(self, api_key: str, cse_id: str):
        self.api_key = api_key
        self.cse_id = cse_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Perform a search using Google Custom Search API."""
        params = {
            "key": self.api_key,
            "cx": self.cse_id,
            "q": query,
            "num": 8
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("items", []):
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", "")
                    })
                
                return results
        except Exception as e:
            logger.error(f"Error in Google Custom Search: {str(e)}")
            return [{"title": "Error", "url": "", "snippet": f"Error in search: {str(e)}"}]


class FallbackSearch:
    """Fallback search implementation when no API keys are available."""
    
    def __init__(self):
        logger.warning("Using fallback search method. This is less reliable and may be rate-limited.")
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Perform a basic search using a public API.
        Note: This is a fallback and may be unreliable or rate-limited.
        """
        try:
            # Using a public search API without authentication
            url = f"https://api.duckduckgo.com/?q={query}&format=json"
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                data = response.json()
                
                results = []
                for result in data.get("RelatedTopics", [])[:8]:
                    if "Text" in result and "FirstURL" in result:
                        results.append({
                            "title": result.get("Text", "").split(" - ")[0],
                            "url": result.get("FirstURL", ""),
                            "snippet": result.get("Text", "")
                        })
                
                return results
        except Exception as e:
            logger.error(f"Error in fallback search: {str(e)}")
            return [{"title": "Search Unavailable", "url": "", "snippet": "Unable to perform search without API keys."}]
