"""
Agentic Search Engine Implementation
This module implements an advanced agentic search engine that can:
1. Optimize/enhance search queries
2. Execute sequential searches with context
3. Search for multiple modalities (text, images, videos)
4. Maintain conversation context
5. Use multiple language models (OpenAI, Gemini, Claude)
"""

import os
import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
from pydantic import BaseModel, Field

# LangChain imports
from langchain.agents import Tool, AgentExecutor
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.tools import BaseTool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import Document
from langchain.schema.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
from langchain.callbacks.manager import CallbackManager
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic

# Import our utilities and tools
from ..util.search_tools import (
    DuckDuckGoSearchTool,
    WikipediaSearchTool, 
    SerpAPIImageSearch,
    SerpAPIVideoSearch,
    SerperSearchTool
)
from ..util.logger import setup_logger

# Configure logger
logger = setup_logger(__name__)

# Available model providers
MODEL_PROVIDERS = {
    "openai": {
        "default": "gpt-4o",
        "models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
    },
    "google": {
        "default": "gemini-2.5-flash-preview-04-17",
        "models": ["gemini-2.0-flash-lite", "gemini-2.5-flash-preview-04-17"]
    },
    "anthropic": {
        "default": "claude-3-opus",
        "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
    }
}

# Available search modalities
SEARCH_MODALITIES = ["text", "images", "videos", "news"]

class SearchQuery(BaseModel):
    """Model for a search query with metadata"""
    query: str
    modalities: List[str] = Field(default=["text"])
    depth: int = Field(default=2)
    max_results: int = Field(default=10)
    enhancement_enabled: bool = Field(default=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SearchResult(BaseModel):
    """Model for search results by modality"""
    modality: str
    data: List[Dict[str, Any]]
    
class SearchSession(BaseModel):
    """Model for a search session with context"""
    id: str
    queries: List[SearchQuery] = Field(default_factory=list)
    results: Dict[str, List[SearchResult]] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    
class LangChainSearchTool(BaseTool):
    """LangChain wrapper for our custom search tools"""
    
    name: str
    description: str
    search_tool: Any
    
    def _run(self, query: str) -> str:
        """Synchronous run method required by LangChain"""
        raise NotImplementedError("This tool only supports async execution")
        
    async def _arun(self, query: str, max_results: int = 5) -> str:
        """Asynchronous run method for LangChain"""
        results = await self.search_tool.search(query, max_results)
        return json.dumps(results, ensure_ascii=False)

class AgenticSearchEngine:
    """
    Advanced agentic search engine with multi-modal search capabilities
    and context-aware query enhancement
    """
    
    def __init__(
        self,
        model_provider: str = "google",
        model_name: Optional[str] = None,
        temperature: float = 0.2,
        verbose: bool = True
    ):
        """
        Initialize the agentic search engine
        
        Args:
            model_provider: Which LLM provider to use ("openai", "google", "anthropic")
            model_name: Specific model name (if None, uses provider default)
            temperature: Creativity parameter for LLM (0.0 - 1.0)
            verbose: Whether to log detailed information
        """
        self.model_provider = model_provider.lower()
        self.model_name = model_name or MODEL_PROVIDERS[self.model_provider]["default"]
        self.temperature = temperature
        self.verbose = verbose
        
        self.sessions = {}  # Store active search sessions
        
        # Initialize search tools
        self.search_tools = {
            "text": {
                "web": SerperSearchTool(),
                "duckduckgo": DuckDuckGoSearchTool(),
                "wikipedia": WikipediaSearchTool()
            },
            "images": {
                "google_images": SerpAPIImageSearch()
            },
            "videos": {
                "google_videos": SerpAPIVideoSearch()
            }
        }
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Initialize agents
        self.query_enhancement_agent = self._create_query_enhancement_agent()
        self.search_planning_agent = self._create_search_planning_agent()
        
        logger.info(f"Initialized AgenticSearchEngine with {self.model_provider}/{self.model_name}")

    def _initialize_llm(self):
        """Initialize the appropriate LLM based on provider"""
        if self.model_provider == "openai":
            return ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        elif self.model_provider == "google":
            return ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=self.temperature,
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
        elif self.model_provider == "anthropic":
            return ChatAnthropic(
                model=self.model_name,
                temperature=self.temperature,
                anthropic_api_key=os.getenv("CLAUDE_API_KEY")
            )
        else:
            logger.warning(f"Unknown model provider {self.model_provider}, falling back to OpenAI")
            return ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=self.temperature
            )
    
    def _create_query_enhancement_agent(self) -> AgentExecutor:
        """Create an agent for query enhancement/optimization"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a search query enhancement AI. Your goal is to:
1. Analyze user queries and determine if they can be improved
2. Break down complex questions into optimal search queries
3. Determine what media types (text, images, videos) would be most helpful 
4. Return enhanced search queries in a structured format

Keep queries concise, specific, and focused on retrieving the most relevant information.
Always respond in JSON format with these fields:
- enhanced_query: The improved main query string
- sub_queries: A list of more specific queries if the main query is complex
- modalities: List of relevant media types for this query (text, images, videos)
- reasoning: Your explanation for how you improved the query
"""),
            ("human", "{input}"),
        ])
        
        # Use OpenAIFunctionsAgent only for OpenAI, otherwise use AgentExecutor directly
        if self.model_provider == "openai":
            agent = OpenAIFunctionsAgent(llm=self.llm, prompt=prompt, tools=[])
            return AgentExecutor(
                agent=agent,
                tools=[],
                verbose=self.verbose,
                handle_parsing_errors=True,
            )
        else:
            # For Gemini and others, use AgentExecutor directly
            return AgentExecutor(
                llm=self.llm,
                prompt=prompt,
                tools=[],
                verbose=self.verbose,
                handle_parsing_errors=True,
            )

    def _create_search_planning_agent(self) -> AgentExecutor:
        """Create an agent for search planning and execution"""
        
        # Create LangChain tools from our search tools
        tools = []
        
        # Web search tool
        web_search_tool = LangChainSearchTool(
            name="web_search",
            description="Search the web for general information. Use this for finding specific answers to questions.",
            search_tool=self.search_tools["text"]["web"]
        )
        tools.append(web_search_tool)
        
        # Wikipedia search tool
        wiki_search_tool = LangChainSearchTool(
            name="wikipedia_search",
            description="Search Wikipedia for factual, encyclopedic information. Best for definitions, historical facts, and general knowledge.",
            search_tool=self.search_tools["text"]["wikipedia"]
        )
        tools.append(wiki_search_tool)
        
        # Image search tool
        image_search_tool = LangChainSearchTool(
            name="image_search",
            description="Search for images related to a topic. Returns a list of image URLs and metadata.",
            search_tool=self.search_tools["images"]["google_images"]
        )
        tools.append(image_search_tool)
        
        # Video search tool
        video_search_tool = LangChainSearchTool(
            name="video_search",
            description="Search for videos related to a topic. Returns a list of video results with thumbnails and links.",
            search_tool=self.search_tools["videos"]["google_videos"]
        )
        tools.append(video_search_tool)
        
        # Create agent prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a search planning AI that executes search strategies across multiple sources.

Follow these steps for any search request:
1. Analyze the query and context from previous searches
2. Determine which search tools to use (web, wikipedia, images, videos)
3. Execute searches in parallel when possible
4. Identify the most relevant results
5. For image and video searches, decide if they are necessary based on the query content

When someone asks about a person, place, or visual topic, consider searching for images.
When someone asks about a process or demonstration, consider searching for videos.
Always prioritize giving accurate, comprehensive answers.

Return your final response with organized results from all sources, properly cited.
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        # Use OpenAIFunctionsAgent only for OpenAI, otherwise use AgentExecutor directly
        if self.model_provider == "openai":
            agent = OpenAIFunctionsAgent(
                llm=self.llm,
                tools=tools,
                prompt=prompt
            )
            return AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=self.verbose,
                return_intermediate_steps=True,
                memory=ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True
                )
            )
        else:
            return AgentExecutor(
                llm=self.llm,
                prompt=prompt,
                tools=tools,
                verbose=self.verbose,
                return_intermediate_steps=True,
                memory=ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True
                )
            )

    async def enhance_query(self, query: str) -> Dict[str, Any]:
        """
        Enhance the user's query for optimal search
        
        Args:
            query: Original user query
            
        Returns:
            Dictionary with enhanced query and metadata
        """
        try:
            response = await self.query_enhancement_agent.ainvoke({"input": query})
            
            # Parse JSON response (with fallback handling)
            try:
                if isinstance(response, dict) and "output" in response:
                    result = json.loads(response["output"])
                else:
                    result = json.loads(response)
            except json.JSONDecodeError:
                # Fallback to regex extraction if JSON parsing fails
                import re
                text = response["output"] if isinstance(response, dict) else response
                # Extract JSON from markdown blocks or plain text
                json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # Simple fallback
                    result = {
                        "enhanced_query": query,
                        "sub_queries": [],
                        "modalities": ["text"],
                        "reasoning": "Direct query passthrough due to parsing error."
                    }
            
            # Ensure all required fields exist
            result.setdefault("enhanced_query", query)
            result.setdefault("sub_queries", [])
            result.setdefault("modalities", ["text"])
            result.setdefault("reasoning", "")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in query enhancement: {str(e)}")
            # Return default with original query on error
            return {
                "enhanced_query": query,
                "sub_queries": [],
                "modalities": ["text"],
                "reasoning": f"Error in enhancement: {str(e)}"
            }
    
    async def execute_search(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_results: int = 10,
        modalities: List[str] = None,
        use_enhancement: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a full agentic search with the given query
        
        Args:
            query: The user's search query
            session_id: Optional session ID for context continuity
            max_results: Maximum number of results per source
            modalities: List of modalities to search (text, images, videos)
            use_enhancement: Whether to use query enhancement
            
        Returns:
            Dictionary with search results, reasoning, and metadata
        """
        start_time = time.time()
        
        try:
            # Initialize or retrieve session
            session = await self._get_or_create_session(session_id)
            
            # Default modalities to text only if not specified
            if modalities is None:
                modalities = ["text"]
            
            # 1. Enhance query if enabled
            enhanced_data = {}
            if use_enhancement:
                enhanced_data = await self.enhance_query(query)
                enhanced_query = enhanced_data.get("enhanced_query", query)
                detected_modalities = enhanced_data.get("modalities", ["text"])
                
                # Merge user-requested modalities with detected ones
                modalities = list(set(modalities + detected_modalities))
            else:
                enhanced_query = query
            
            # 2. Create search query object
            search_query = SearchQuery(
                query=query,
                modalities=modalities,
                depth=max(1, min(3, len(enhanced_data.get("sub_queries", [])) + 1)),
                max_results=max_results,
                enhancement_enabled=use_enhancement,
                metadata={
                    "enhanced_query": enhanced_query,
                    "sub_queries": enhanced_data.get("sub_queries", []),
                    "reasoning": enhanced_data.get("reasoning", "")
                }
            )
            
            # 3. Add query to session
            session.queries.append(search_query)
            session.updated_at = time.time()
            
            # 4. Execute search with agent
            agent_input = f"Search query: {enhanced_query}"
            if search_query.metadata.get("sub_queries"):
                agent_input += "\nRelated queries to consider: " + ", ".join(search_query.metadata["sub_queries"])
                
            agent_response = await self.search_planning_agent.ainvoke({"input": agent_input})
            
            # 5. Process results by modality
            results = {
                "text": [],
                "images": [],
                "videos": []
            }
            
            # Extract results from intermediate steps
            sources = []
            reasoning_steps = []
            
            for step in agent_response.get("intermediate_steps", []):
                tool = step[0].tool
                tool_input = step[0].tool_input
                observation = step[1]
                
                reasoning_steps.append({
                    "step": len(reasoning_steps) + 1,
                    "thought": f"Used {tool} to search for '{tool_input}'"
                })
                
                # Parse observation as JSON
                try:
                    parsed_results = json.loads(observation)
                    
                    # Categorize results by tool
                    if tool == "web_search" or tool == "wikipedia_search":
                        results["text"].extend(parsed_results)
                        sources.extend(parsed_results)
                    elif tool == "image_search":
                        results["images"].extend(parsed_results)
                        # Add image sources in a compatible format
                        for img in parsed_results:
                            sources.append({
                                "title": img.get("title", "Image result"),
                                "link": img.get("source_url", ""),
                                "imageUrl": img.get("url", ""),
                                "snippet": img.get("alt", ""),
                                "source": "image_search"
                            })
                    elif tool == "video_search":
                        results["videos"].extend(parsed_results)
                        # Add video sources in a compatible format
                        for vid in parsed_results:
                            sources.append({
                                "title": vid.get("title", "Video result"),
                                "link": vid.get("link", ""),
                                "imageUrl": vid.get("thumbnail", ""),
                                "snippet": vid.get("description", ""),
                                "source": "video_search"
                            })
                except:
                    # If parsing fails, skip this result
                    logger.warning(f"Failed to parse observation as JSON: {observation[:100]}...")
            
            # 6. Store results in session
            for modality, data in results.items():
                if data:  # Only store non-empty results
                    if query not in session.results:
                        session.results[query] = []
                    
                    session.results[query].append(
                        SearchResult(modality=modality, data=data)
                    )
            
            # 7. Format final response
            answer = agent_response.get("output", "No result generated.")
            
            # Format final response
            execution_time = time.time() - start_time
            response = {
                "query": query,
                "results": [{
                    "content": answer,
                    "type": "text"
                }],
                "reasoning": reasoning_steps,
                "sources": sources,
                "execution_time": execution_time,
                "session_id": session.id,
                "has_images": bool(results["images"]),
                "has_videos": bool(results["videos"]),
                "image_results": results["images"],
                "video_results": results["videos"],
                "enhanced_query": enhanced_query
            }
            
            logger.info(f"Search completed in {execution_time:.2f}s: {query}")
            return response
            
        except Exception as e:
            logger.error(f"Error in execute_search: {str(e)}")
            execution_time = time.time() - start_time
            
            # Return error response
            return {
                "query": query,
                "results": [{
                    "content": f"An error occurred while searching: {str(e)}",
                    "type": "error"
                }],
                "reasoning": [{
                    "step": 1,
                    "thought": f"Error during search: {str(e)}"
                }],
                "sources": [],
                "execution_time": execution_time,
                "session_id": session_id or "error-session",
                "has_images": False,
                "has_videos": False,
                "image_results": [],
                "video_results": [],
                "enhanced_query": query
            }
    
    async def _get_or_create_session(self, session_id: Optional[str] = None) -> SearchSession:
        """Get an existing session or create a new one"""
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
        
        # Create new session with UUID
        import uuid
        new_id = session_id or str(uuid.uuid4())
        session = SearchSession(id=new_id)
        self.sessions[new_id] = session
        
        return session
        
    async def close(self):
        """Close all resources"""
        for modality in self.search_tools.values():
            for tool in modality.values():
                if hasattr(tool, 'close'):
                    await tool.close()

# Main function for testing
async def test_agentic_search():
    """Test the agentic search engine"""
    try:
        search_engine = AgenticSearchEngine(
            model_provider="openai",
            model_name="gpt-3.5-turbo",
            verbose=True
        )
        
        # Test search
        result = await search_engine.execute_search(
            query="Who is Elon Musk and what's the latest news about SpaceX?",
            modalities=["text", "images"],
            max_results=3
        )
        
        print(json.dumps(result, indent=2))
        
    finally:
        await search_engine.close()

if __name__ == "__main__":
    asyncio.run(test_agentic_search()) 