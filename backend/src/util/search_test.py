


import os


import json


import asyncio


import aiohttp


import time


from typing import List, Dict, Any, Optional, Union


from urllib.parse import urlparse, quote_plus


from tenacity import retry, stop_after_attempt, wait_exponential


from dotenv import load_dotenv


from bs4 import BeautifulSoup




try:


    import wikipedia


    WIKIPEDIA_AVAILABLE = True


except ImportError:


    WIKIPEDIA_AVAILABLE = False



try:


    from serpapi import GoogleSearch


    SERPAPI_AVAILABLE = True


except ImportError:


    SERPAPI_AVAILABLE = False



try:


    from duckduckgo_search import DDGS


    DDGS_AVAILABLE = True


except ImportError:


    DDGS_AVAILABLE = False




load_dotenv()




SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")


SERPER_API_KEY = os.getenv("SERPER_API_KEY")


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")



from ..config import settings


from ..utils.logger import setup_logger



logger = setup_logger(__name__)



class SearchTool:


    """Base class for search tools"""


    


    def __init__(self):


        self.session = None


        


    async def _ensure_session(self):


        """Ensure an aiohttp session exists"""


        if self.session is None or self.session.closed:


            self.session = aiohttp.ClientSession()


            


    async def close(self):


        """Close the aiohttp session"""


        if self.session and not self.session.closed:


            await self.session.close()


            


    async def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:


        """Search implementation to be overridden by subclasses"""


        raise NotImplementedError("Subclasses must implement search()")



class DuckDuckGoSearchTool(SearchTool):


    """Tool for searching the web using DuckDuckGo"""


    


    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:


        """Perform a web search using DuckDuckGo"""


        await self._ensure_session()


        


        try:


            # Replace with actual DuckDuckGo API call or scraping logic


            # For now, return a mock response


            await asyncio.sleep(0.5)  # Simulate network delay


            


            results = []


            # Generate some mock results for testing


            for i in range(min(max_results, 5)):


                results.append({


                    "title": f"Result {i+1} for '{query}'",


                    "snippet": f"This is a snippet of information about {query} from the web.",


                    "url": f"https://example.com/result/{i+1}",


                    "source": "web:duckduckgo"


                })


                


            logger.info(f"Found {len(results)} DuckDuckGo results for '{query}'")


            return results


            


        except Exception as e:


            logger.error(f"DuckDuckGo search error: {str(e)}")


            return []



class WikipediaSearchTool(SearchTool):


    """Tool for searching Wikipedia"""


    


    async def search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:


        """Search Wikipedia for information"""


        try:


            # Use synchronous Wikipedia library in a thread pool


            import wikipedia


            


            # Create a function to run in the executor


            def _search_wikipedia():


                # Get search results


                search_results = wikipedia.search(query, results=max_results)


                results = []


                


                for title in search_results:


                    try:


                        # Get page summary


                        page = wikipedia.page(title, auto_suggest=False)


                        summary = page.summary


                        url = page.url


                        


                        results.append({


                            "title": title,


                            "snippet": summary[:200] + "..." if len(summary) > 200 else summary,


                            "content": summary,


                            "url": url,


                            "source": "wikipedia"


                        })


                    except Exception as e:


                        logger.warning(f"Error fetching Wikipedia page {title}: {str(e)}")


                        


                return results


            


            # Run the Wikipedia search in a thread pool


            loop = asyncio.get_event_loop()


            results = await loop.run_in_executor(None, _search_wikipedia)


            


            logger.info(f"Found {len(results)} Wikipedia results for '{query}'")


            return results


            


        except Exception as e:


            logger.error(f"Wikipedia search error: {str(e)}")


            return []



class SerpAPIImageSearch(SearchTool):


    """Tool for searching images using SerpAPI"""


    


    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:


        """Search for images related to the query"""


        await self._ensure_session()


        


        try:


            if not settings.SERPAPI_API_KEY:


                logger.warning("SERPAPI_API_KEY not set, returning mock image results")


                return self._mock_image_results(query, max_results)


                


            


            params = {


                "q": query,


                "engine": "google_images",


                "api_key": settings.SERPAPI_API_KEY,


                "num": max_results


            }


            


            # Make request to SerpAPI


            async with self.session.get("https://serpapi.com/search", params=params) as response:


                if response.status != 200:


                    logger.error(f"SerpAPI image search error: {response.status}")


                    return self._mock_image_results(query, max_results)


                    


                data = await response.json()


                


                # Extract image results


                results = []


                for image in data.get("images_results", [])[:max_results]:


                    results.append({


                        "title": image.get("title", ""),


                        "thumbnail": image.get("thumbnail", ""),


                        "image_url": image.get("original", ""),


                        "source_url": image.get("source", ""),


                        "source": "serpapi:images"


                    })


                    


                logger.info(f"Found {len(results)} image results for '{query}'")


                return results


                


        except Exception as e:


            logger.error(f"SerpAPI image search error: {str(e)}")


            return self._mock_image_results(query, max_results)


            


    def _mock_image_results(self, query: str, max_results: int) -> List[Dict[str, Any]]:


        """Generate mock image results for testing"""


        results = []


        for i in range(min(max_results, 5)):


            results.append({


                "title": f"Image {i+1} for '{query}'",


                "thumbnail": f"https://via.placeholder.com/150?text=Image+{i+1}",


                "image_url": f"https://via.placeholder.com/800x600?text=Image+{i+1}",


                "source_url": f"https://example.com/images/{i+1}",


                "source": "mock:images"


            })


            


        return results



class SerpAPIVideoSearch(SearchTool):


    """Tool for searching videos using SerpAPI"""


    


    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:


        """Search for videos related to the query"""


        await self._ensure_session()


        


        try:


            if not settings.SERPAPI_API_KEY:


                logger.warning("SERPAPI_API_KEY not set, returning mock video results")


                return self._mock_video_results(query, max_results)


                


            # Prepare SerpAPI request


            params = {


                "q": query + " video",


                "engine": "google_videos",


                "api_key": settings.SERPAPI_API_KEY,


                "num": max_results


            }


            


            # Make request to SerpAPI


            async with self.session.get("https://serpapi.com/search", params=params) as response:


                if response.status != 200:


                    logger.error(f"SerpAPI video search error: {response.status}")


                    return self._mock_video_results(query, max_results)


                    


                data = await response.json()


                


                # Extract video results


                results = []


                for video in data.get("video_results", [])[:max_results]:


                    results.append({


                        "title": video.get("title", ""),


                        "thumbnail": video.get("thumbnail", ""),


                        "video_url": video.get("link", ""),


                        "duration": video.get("duration", ""),


                        "platform": video.get("platform", ""),


                        "source": "serpapi:videos"


                    })


                    


                logger.info(f"Found {len(results)} video results for '{query}'")


                return results


                


        except Exception as e:


            logger.error(f"SerpAPI video search error: {str(e)}")


            return self._mock_video_results(query, max_results)


            


    def _mock_video_results(self, query: str, max_results: int) -> List[Dict[str, Any]]:


        """Generate mock video results for testing"""


        platforms = ["YouTube", "Vimeo", "Dailymotion"]


        results = []


        


        for i in range(min(max_results, 5)):


            platform = platforms[i % len(platforms)]


            results.append({


                "title": f"Video {i+1} about {query}",


                "thumbnail": f"https://via.placeholder.com/320x180?text=Video+{i+1}",


                "video_url": f"https://example.com/videos/{i+1}",


                "duration": f"{(i+1)*2}:{(i*10)%60:02d}",


                "platform": platform,


                "source": f"mock:{platform.lower()}"


            })


            


        return results



class SerperSearchTool(SearchTool):


    """Tool for searching the web using Serper.dev"""


    


    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:


        """Perform a web search using Serper.dev"""


        await self._ensure_session()


        


        try:


            if not settings.SERPER_API_KEY:


                logger.warning("SERPER_API_KEY not set, returning mock search results")


                return self._mock_serper_results(query, max_results)


                


            # Prepare Serper.dev request


            headers = {


                "X-API-KEY": settings.SERPER_API_KEY,


                "Content-Type": "application/json"


            }


            


            data = {


                "q": query,


                "num": max_results


            }


            


            # Make request to Serper.dev


            async with self.session.post("https://google.serper.dev/search", headers=headers, json=data) as response:


                if response.status != 200:


                    logger.error(f"Serper search error: {response.status}")


                    return self._mock_serper_results(query, max_results)


                    


                data = await response.json()


                


                # Extract organic search results


                results = []


               # Continue from where the last method cut off


                for item in data.get("organic", [])[:max_results]:


                    results.append({


                        "title": item.get("title", ""),


                        "snippet": item.get("snippet", ""),


                        "url": item.get("link", ""),


                        "source": "web:serper"


                    })



                logger.info(f"Found {len(results)} Serper results for '{query}'")


                return results



        except Exception as e:


            logger.error(f"Serper search error: {str(e)}")


            return self._mock_serper_results(query, max_results)



    def _mock_serper_results(self, query: str, max_results: int) -> List[Dict[str, Any]]:


        """Generate mock search results for Serper"""


        results = []


        for i in range(min(max_results, 5)):


            results.append({


                "title": f"Serper result {i+1} for '{query}'",


                "snippet": f"This is a snippet from a mock Serper result about {query}.",


                "url": f"https://example.com/serper/{i+1}",


                "source": "mock:serper"


            })


        return results
