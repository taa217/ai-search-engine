"""
Agent pipeline for orchestrating agentic search using LangChain and multiple tools.
Handles query rewriting, tool selection, and result aggregation.
"""
import uuid
import asyncio
from typing import Any, Dict, List, Optional

from .model_manager import get_llm
from .session_manager import SessionManager
from ..util.search_tools import (
    DuckDuckGoSearchTool, WikipediaSearchTool, SerpAPIImageSearch, SerpAPIVideoSearch, SerperSearchTool
)
from ..util.parallel_search import ParallelSearchExecutor, SearchPriority
from ..util.logger import setup_logger

logger = setup_logger(__name__)

class AgentPipeline:
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        
        # Initialize search tools
        self.web_search = SerperSearchTool()
        self.duck_search = DuckDuckGoSearchTool()
        self.wikipedia_search = WikipediaSearchTool()
        self.image_search = SerpAPIImageSearch()
        self.video_search = SerpAPIVideoSearch()
        
        # Initialize parallel search executor with prioritized tools
        self.search_executor = ParallelSearchExecutor()
        
        # Register search tools with priorities and timeouts
        self._register_search_tools()
        
    def _register_search_tools(self):
        """Register all search tools with appropriate priorities"""
        # Serper is typically fastest and most reliable for web search
        self.search_executor.register_tool(
            tool=self.web_search,
            priority=SearchPriority.HIGH,
            timeout=5.0,  # 5 second timeout
            max_results=8,
            weight=1.0
        )
        
        # DuckDuckGo as medium priority alternative
        self.search_executor.register_tool(
            tool=self.duck_search,
            priority=SearchPriority.MEDIUM,
            timeout=6.0,
            max_results=8,
            weight=0.8
        )
        
        # Wikipedia for factual information, high priority for knowledge queries
        self.search_executor.register_tool(
            tool=self.wikipedia_search,
            priority=SearchPriority.MEDIUM,
            timeout=7.0,
            max_results=3,
            weight=0.9
        )
        
        # Image and video search are lower priority and only used when needed
        self.search_executor.register_tool(
            tool=self.image_search,
            priority=SearchPriority.LOW,
            timeout=8.0,
            max_results=5,
            weight=0.7
        )
        
        self.search_executor.register_tool(
            tool=self.video_search,
            priority=SearchPriority.LOW,
            timeout=8.0,
            max_results=3,
            weight=0.6
        )

    async def run(self, user_id: str, query: str, model: str = "gemini", max_results: int = 5) -> Dict[str, Any]:
        """
        Run the agent pipeline for the given query and user session.
        
        Args:
            user_id: User identifier
            query: Search query string
            model: LLM model to use for query enhancement
            max_results: Maximum results to return per category
            
        Returns:
            Dictionary containing search results, images, videos, etc.
        """
        session = self.session_manager.get_session(user_id)
        llm = get_llm(model)
        
        # Step 1: Use LLM to rewrite/expand query and determine modality needs
        agent_prompt = self._build_agent_prompt(query, session)
        agent_response = llm(agent_prompt)
        
        # Extract information from LLM response
        queries = agent_response.get("queries", [query])
        needs_images = agent_response.get("needs_images", False)
        needs_videos = agent_response.get("needs_videos", False)
        
        # Step 2: Execute prioritized parallel search for each query
        all_search_results = []
        
        # Execute searches for all queries in parallel
        search_tasks = [
            self.search_executor.execute_prioritized_search(q) 
            for q in queries
        ]
        
        search_responses = await asyncio.gather(*search_tasks)
        
        # Collect all web results
        web_results = []
        successful_sources = set()
        
        for response in search_responses:
            web_results.extend(response["results"])
            successful_sources.update(response["sources"])
            
            # Add search stats to logging for monitoring
            for tool_name, stats in response["stats"].get("tool_stats", {}).items():
                logger.info(f"Tool {tool_name} stats: {stats}")
        
        # Step 3: Get images and videos if needed
        images, videos = [], []
        
        if needs_images:
            # Images already collected in parallel search if image tool was used
            for response in search_responses:
                for result in response["results"]:
                    if "thumbnail" in result or "image_url" in result:
                        image_result = {
                            "url": result.get("url") or result.get("image_url", ""),
                            "title": result.get("title", ""),
                            "thumbnail": result.get("thumbnail", "")
                        }
                        if image_result not in images:  # Avoid duplicates
                            images.append(image_result)
        
        if needs_videos:
            # Videos already collected in parallel search if video tool was used
            for response in search_responses:
                for result in response["results"]:
                    if "video_url" in result or "duration" in result:
                        video_result = {
                            "url": result.get("video_url") or result.get("url", ""),
                            "title": result.get("title", ""),
                            "thumbnail": result.get("thumbnail", ""),
                            "duration": result.get("duration", "")
                        }
                        if video_result not in videos:  # Avoid duplicates
                            videos.append(video_result)
        
        # Step 4: Aggregate results and return
        response = {
            "queries": queries,
            "web_results": web_results[:max_results*2],  # Limit to avoid overwhelming
            "images": images[:max_results],
            "videos": videos[:max_results],
            "sources": list(successful_sources),
            "session_id": session["id"],
        }
        
        # Update session with new search results
        self.session_manager.update_session(user_id, query, response)
        
        return response

    def _build_agent_prompt(self, query: str, session: Dict[str, Any]) -> str:
        """
        Build a prompt for the LLM agent to analyze query intent.
        
        Args:
            query: User's search query
            session: User's session data with history
            
        Returns:
            Prompt string for the LLM
        """
        history = session.get("history", [])
        
        prompt = (
            f"User asked: '{query}'.\n"
            f"Previous context: {history}\n\n"
            "Analyze this search query and help me plan the search strategy:\n"
            "1. Should the query be rewritten or expanded for better results?\n"
            "2. Should it be split into multiple queries to get comprehensive results?\n"
            "3. Determine if this query would benefit from images or videos.\n\n"
            "Respond as a JSON object: {\"queries\": [...], \"needs_images\": bool, \"needs_videos\": bool}"
        )
        
        return prompt
        
    async def close(self):
        """Close all search tool sessions and executors."""
        await self.search_executor.close()
