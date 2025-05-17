# --- START OF FILE search_tools.py ---

"""Real search tools module using external APIs."""

import os
import json
import asyncio
import aiohttp
import time
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urlparse, quote_plus

# Import tenacity for retries
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from dotenv import load_dotenv

from bs4 import BeautifulSoup

# Conditional imports for search libraries
try:
    import wikipedia
    WIKIPEDIA_AVAILABLE = True
except ImportError:
    WIKIPEDIA_AVAILABLE = False
    wikipedia = None # Define as None if not available

try:
    # Note: SerpAPI Python library is synchronous, we'll use direct HTTP requests with aiohttp
    # We don't strictly need the library if using aiohttp, but check indicates intent/possibility
    # import serpapi
    SERPAPI_AVAILABLE = True # Assume available if configured, check key later
except ImportError:
    SERPAPI_AVAILABLE = False

try:
    from duckduckgo_search import DDGS, AsyncDDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    AsyncDDGS = None # Define as None if not available

load_dotenv()

# API Keys - It's better practice to load these within the tools or pass them,
# but following the original pattern for now. Using settings object is preferred.
# Assuming settings object is correctly configured elsewhere.
# from ..config import settings
# Mock settings object if not available for standalone execution
class MockSettings:
    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
    SERPER_API_KEY = os.getenv("SERPER_API_KEY")
    # GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") # Not used in this version
    # GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID") # Not used in this version

settings = MockSettings() # Replace with actual import: from ..config import settings

from ..util.logger import setup_logger # Assuming logger setup exists
# Mock logger if not available for standalone execution
import logging
def setup_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = setup_logger(__name__)


# --- Base SearchTool Class ---

class SearchTool:
    """Base class for search tools with async HTTP session management."""

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            # Consider adding connector with SSL context options if needed
            connector = aiohttp.TCPConnector(ssl=False) # Adjust SSL verification as needed
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Abstract search method to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement search()")

    # Apply retry decorator common settings here or individually
    RETRY_SETTINGS = {
        "stop": stop_after_attempt(3),
        "wait": wait_exponential(multiplier=1, min=4, max=10),
        "retry": retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError, ConnectionError)),
        "reraise": True # Reraise the exception if all retries fail
    }


# --- Concrete Search Tool Implementations ---

class DuckDuckGoSearchTool(SearchTool):
    """Tool for searching the web using DuckDuckGo (duckduckgo_search library)."""

    @retry(**SearchTool.RETRY_SETTINGS)
    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Perform a web search using the duckduckgo_search library."""
        if not DDGS_AVAILABLE:
            logger.error("DuckDuckGo Search library (duckduckgo_search) is not installed.")
            raise ImportError("duckduckgo_search library is required for DuckDuckGoSearchTool.")

        results = []
        try:
            # Set a timeout for DuckDuckGo search
            search_timeout = 8.0  # 8 seconds timeout
            
            # Use asyncio.wait_for to implement the timeout
            async with AsyncDDGS() as ddgs:
                try:
                    ddg_results = await asyncio.wait_for(
                        ddgs.text(query, max_results=max_results),
                        timeout=search_timeout
                    )
                    
                    if ddg_results:
                        for item in ddg_results:
                            results.append({
                                "title": item.get("title", ""),
                                "snippet": item.get("body", ""),
                                "url": item.get("href", ""),
                                "source": "web:duckduckgo"
                            })
                    logger.info(f"Found {len(results)} DuckDuckGo results for '{query}'")
                except asyncio.TimeoutError:
                    logger.warning(f"DuckDuckGo search timed out after {search_timeout}s for query '{query}'")
            
            return results

        except Exception as e:
            logger.error(f"DuckDuckGo search error for '{query}': {str(e)}")
            # Reraise after logging, or return empty list based on desired strictness
            # raise RuntimeError(f"DuckDuckGo search failed: {str(e)}") from e
            return [] # Returning empty list on failure


class WikipediaSearchTool(SearchTool):
    """Tool for searching Wikipedia."""

    async def search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Search Wikipedia for information using the wikipedia library."""
        if not WIKIPEDIA_AVAILABLE:
            logger.error("Wikipedia library is not installed.")
            raise ImportError("wikipedia library is required for WikipediaSearchTool.")

        try:
            # Use synchronous Wikipedia library in a thread pool executor
            loop = asyncio.get_event_loop()
            search_results = await loop.run_in_executor(
                None,  # Use default executor
                lambda: wikipedia.search(query, results=max_results)
            )

            results = []
            tasks = []

            # Define async helper to fetch page details
            async def fetch_page(title):
                try:
                    # Set a timeout for Wikipedia page fetch operations
                    page_fetch_timeout = 5.0  # 5 seconds timeout for each page fetch
                    
                    # Use asyncio.wait_for to implement the timeout
                    page = await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda: wikipedia.page(title, auto_suggest=False, preload=True)
                        ),
                        timeout=page_fetch_timeout
                    )
                    
                    summary = page.summary
                    url = page.url
                    return {
                        "title": title,
                        "snippet": summary[:250] + "..." if len(summary) > 250 else summary, # Slightly longer snippet
                        "content": summary, # Full summary as content
                        "url": url,
                        "source": "wikipedia"
                    }
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout fetching Wikipedia page '{title}' after {page_fetch_timeout}s")
                    return None
                except wikipedia.exceptions.PageError:
                    logger.warning(f"Wikipedia page '{title}' not found or disambiguation error.")
                    return None
                except wikipedia.exceptions.DisambiguationError as e:
                     logger.warning(f"Wikipedia disambiguation error for '{title}': {e.options[:3]}")
                     # Optionally, try searching for the first option e.g. fetch_page(e.options[0])
                     return None
                except Exception as e:
                    logger.warning(f"Error fetching Wikipedia page '{title}': {str(e)}")
                    return None

            # Create tasks to fetch pages concurrently
            for title in search_results:
                tasks.append(fetch_page(title))

            # Gather results from tasks
            page_results = await asyncio.gather(*tasks)
            results = [res for res in page_results if res is not None] # Filter out None results

            logger.info(f"Found {len(results)} Wikipedia results for '{query}'")
            return results

        except Exception as e:
            logger.error(f"Wikipedia search error for '{query}': {str(e)}")
            # raise RuntimeError(f"Wikipedia search failed: {str(e)}") from e
            return [] # Returning empty list on failure


class SerpAPIImageSearch(SearchTool):
    """Tool for searching images using SerpAPI."""

    @retry(**SearchTool.RETRY_SETTINGS)
    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        # Debug logging to verify this method is being called
        print(f"DEBUG - SerpAPIImageSearch.search called for query: '{query}'")
        logger.info(f"SerpAPIImageSearch.search called for query: '{query}' with max_results={max_results}")
        """Search for images related to the query using SerpAPI Google Images."""
        if not settings.SERPAPI_API_KEY:
            logger.error("SERPAPI_API_KEY is not set in environment or settings.")
            raise ValueError("SerpAPI API key is required for image search.")

        session = await self._get_session()
        params = {
            "q": query,
            "engine": "google_images",
            "ijn": "0",  # Page number, starts at 0
            "api_key": settings.SERPAPI_API_KEY,
            "num": max_results # SerpAPI uses 'num' for result count
        }

        try:
            logger.info(f"Performing SerpAPI image search for: '{query}'")
            async with session.get("https://serpapi.com/search", params=params) as response:
                response.raise_for_status() # Raise exception for 4xx/5xx status codes
                data = await response.json()

                results = []
                # Check if 'images_results' exists and is a list
                image_data = data.get("images_results")
                if not image_data or not isinstance(image_data, list):
                    logger.warning(f"No 'images_results' found in SerpAPI response for '{query}'. Response: {data}")
                    return []
                    
                # Debug the raw image data from SerpAPI
                logger.info(f"SerpAPI raw image data for '{query}': {image_data[:2]}")  # Only log first 2 to avoid overload

                for image in image_data[:max_results]:
                    if not isinstance(image, dict): continue # Skip malformed entries
                    # Format image data to match frontend expectations
                    source_domain = ""
                    source_url = image.get("link", image.get("source", ""))
                    try:
                        if source_url:
                            from urllib.parse import urlparse
                            parsed_url = urlparse(source_url)
                            source_domain = parsed_url.netloc.replace('www.', '')
                    except Exception:
                        pass
                        
                    # Get image URLs, ensure they're valid and start with http
                    original_url = image.get("original", "")
                    thumbnail_url = image.get("thumbnail", "")
                    
                    # Ensure URLs have proper scheme
                    if original_url and not original_url.startswith(('http://', 'https://')):
                        original_url = f"https://{original_url}"
                    if thumbnail_url and not thumbnail_url.startswith(('http://', 'https://')):
                        thumbnail_url = f"https://{thumbnail_url}"
                        
                    # Create the formatted image data
                    formatted_image = {
                        
                        "url": original_url or thumbnail_url, # Use original or fallback to thumbnail
                        "title": image.get("title", query),  # Use query as fallback title
                        "alt": image.get("title", query),    # Alt text for accessibility
                        
                        "source_url": source_url,             # URL to the source page
                        "source_name": source_domain or "Google Images", # Source website name
                        "width": image.get("original_width", 0),
                        "height": image.get("original_height", 0),
                        "thumbnail": thumbnail_url # Keep thumbnail for preview
                    }
                    
                    # Debug log the formatted image
                    logger.info(f"Formatted image result: URL='{formatted_image['url']}', thumbnail='{formatted_image['thumbnail']}'")
                    
                    results.append(formatted_image)

                logger.info(f"Found {len(results)} SerpAPI image results for '{query}'")
                return results

        except aiohttp.ClientResponseError as e:
            logger.error(f"SerpAPI image search HTTP error: {e.status} {e.message} for query '{query}'")
            raise RuntimeError(f"SerpAPI image search failed with status {e.status}") from e
        except Exception as e:
            logger.error(f"SerpAPI image search error for '{query}': {str(e)}")
            raise RuntimeError(f"SerpAPI image search failed: {str(e)}") from e


class SerpAPIVideoSearch(SearchTool):
    """Tool for searching videos using SerpAPI."""

    @retry(**SearchTool.RETRY_SETTINGS)
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for videos related to the query using SerpAPI Google Videos."""
        if not settings.SERPAPI_API_KEY:
            logger.error("SERPAPI_API_KEY is not set in environment or settings.")
            raise ValueError("SerpAPI API key is required for video search.")

        session = await self._get_session()
        params = {
            "q": query,
            "engine": "google_videos",
            "api_key": settings.SERPAPI_API_KEY,
            # Note: SerpAPI's Google Video endpoint might not have a 'num' parameter
            # It usually returns one page. We'll rely on slicing the result list.
        }

        try:
            logger.info(f"Performing SerpAPI video search for: '{query}'")
            async with session.get("https://serpapi.com/search", params=params) as response:
                response.raise_for_status()
                data = await response.json()

                results = []
                # Check if 'video_results' exists and is a list
                video_data = data.get("video_results")
                if not video_data or not isinstance(video_data, list):
                    logger.warning(f"No 'video_results' found in SerpAPI response for '{query}'. Response: {data}")
                    return []

                for video in video_data[:max_results]:
                     if not isinstance(video, dict): continue # Skip malformed entries
                     results.append({
                        "title": video.get("title", ""),
                        "thumbnail": video.get("thumbnail", ""),
                        "video_url": video.get("link", ""), # URL to the video page (e.g., YouTube)
                        "duration": video.get("duration", ""), # Often formatted like "PT1M35S" or "1:35"
                        "platform": video.get("source", ""), # E.g., "YouTube", "Vimeo"
                        "snippet": video.get("snippet", ""), # Sometimes available
                        "source": "serpapi:google_videos"
                    })

                logger.info(f"Found {len(results)} SerpAPI video results for '{query}'")
                return results

        except aiohttp.ClientResponseError as e:
            logger.error(f"SerpAPI video search HTTP error: {e.status} {e.message} for query '{query}'")
            raise RuntimeError(f"SerpAPI video search failed with status {e.status}") from e
        except Exception as e:
            logger.error(f"SerpAPI video search error for '{query}': {str(e)}")
            raise RuntimeError(f"SerpAPI video search failed: {str(e)}") from e


class SerperSearchTool(SearchTool):
    """Tool for searching the web using Serper.dev."""

    @retry(**SearchTool.RETRY_SETTINGS)
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Perform a web search using Serper.dev."""
        if not settings.SERPER_API_KEY:
            logger.error("SERPER_API_KEY is not set in environment or settings.")
            raise ValueError("Serper.dev API key is required for web search.")

        session = await self._get_session()
        headers = {
            "X-API-KEY": settings.SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        payload = json.dumps({
            "q": query,
            "num": max_results
        })

        try:
            logger.info(f"Performing Serper.dev search for: '{query}'")
            
            # Set explicit timeout for the HTTP request
            timeout = aiohttp.ClientTimeout(total=8.0)  # 8 seconds timeout
            
            async with session.post(
                "https://google.serper.dev/search", 
                headers=headers, 
                data=payload,
                timeout=timeout
            ) as response:
                # Check specifically for 403 Forbidden, often indicating key issues or quota exceeded
                if response.status == 403:
                     err_text = await response.text()
                     logger.error(f"Serper search failed with 403 Forbidden. Check API key/plan. Response: {err_text}")
                     raise RuntimeError(f"Serper API key invalid or quota exceeded (403 Forbidden). Response: {err_text}")
                response.raise_for_status() # Raise for other 4xx/5xx errors
                data = await response.json()

                results = []
                # Check if 'organic' results exist and is a list
                organic_data = data.get("organic")
                if not organic_data or not isinstance(organic_data, list):
                     logger.warning(f"No 'organic' results found in Serper response for '{query}'. Response: {data}")
                     return []

                for item in organic_data[:max_results]: # Ensure we don't exceed max_results
                    if not isinstance(item, dict): continue # Skip malformed entries
                    results.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "url": item.get("link", ""),
                        "position": item.get("position"), # Serper provides position
                        "source": "web:serper"
                    })

                logger.info(f"Found {len(results)} Serper results for '{query}'")
                return results

        except asyncio.TimeoutError:
            logger.error(f"Serper search timed out after 8.0s for query '{query}'")
            return []  # Return empty list on timeout
        except aiohttp.ClientResponseError as e:
            # Log specific details for ClientResponseError
            error_body = await e.response.text() if hasattr(e, 'response') else "No response body"
            logger.error(f"Serper search HTTP error: {e.status} {e.message}. Body: {error_body}. Query: '{query}'")
            raise RuntimeError(f"Serper search failed with status {e.status}. Check API key and Serper status. Details: {error_body}") from e
        except (aiohttp.ClientError, json.JSONDecodeError, Exception) as e:
            # Catch other potential errors (network, json parsing, etc.)
            logger.error(f"Serper search error for '{query}': {type(e).__name__} - {str(e)}")
            raise RuntimeError(f"Serper search failed: {str(e)}") from e


# Example usage (optional, for testing)
async def main():
    query = "latest AI advancements"

    # Instantiate tools
    serper_tool = SerperSearchTool()
    ddg_tool = DuckDuckGoSearchTool()
    wiki_tool = WikipediaSearchTool()
    img_tool = SerpAPIImageSearch()
    vid_tool = SerpAPIVideoSearch()

    tools = [serper_tool, ddg_tool, wiki_tool, img_tool, vid_tool]

    try:
        print(f"--- Running Serper Search for: '{query}' ---")
        serper_results = await serper_tool.search(query, max_results=3)
        print(json.dumps(serper_results, indent=2))
    except Exception as e:
        print(f"Serper search failed: {e}")

    try:
        print(f"\n--- Running DuckDuckGo Search for: '{query}' ---")
        ddg_results = await ddg_tool.search(query, max_results=3)
        print(json.dumps(ddg_results, indent=2))
    except Exception as e:
        print(f"DuckDuckGo search failed: {e}")

    try:
        print(f"\n--- Running Wikipedia Search for: '{query}' ---")
        wiki_results = await wiki_tool.search(query, max_results=2)
        print(json.dumps(wiki_results, indent=2))
    except Exception as e:
        print(f"Wikipedia search failed: {e}")

    try:
        print(f"\n--- Running SerpAPI Image Search for: '{query}' ---")
        img_results = await img_tool.search(query, max_results=4)
        print(json.dumps(img_results, indent=2))
    except Exception as e:
        print(f"SerpAPI Image search failed: {e}")

    try:
        print(f"\n--- Running SerpAPI Video Search for: '{query}' ---")
        vid_results = await vid_tool.search(query, max_results=3)
        print(json.dumps(vid_results, indent=2))
    except Exception as e:
        print(f"SerpAPI Video search failed: {e}")

    # Important: Close sessions when done
    print("\n--- Closing sessions ---")
    await asyncio.gather(*(tool.close() for tool in tools))

# if __name__ == "__main__":
#     # Setup environment variables (SERPER_API_KEY, SERPAPI_API_KEY) in a .env file
#     # or export them before running.
#     load_dotenv()
#     # Replace MockSettings with your actual settings import if applicable
#     # from your_project.config import settings # Example
#     settings = MockSettings() # Using mock settings for standalone run

#     # Add basic logging setup if running standalone
#     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#     asyncio.run(main())

# --- END OF FILE search_tools.py ---