import os
import time
import json
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional, Set
import re

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.schema import Document
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools.retriever import create_retriever_tool
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore

# Import search tools for web, image, and video search
from ..util.search_tools import (
    DuckDuckGoSearchTool,
    WikipediaSearchTool,
    SerpAPIImageSearch,
    SerpAPIVideoSearch,
    SerperSearchTool
)

try:
    from langchain_community.vectorstores import Weaviate
    import weaviate
except ImportError:
    pass

try:
    from langchain_community.vectorstores import Qdrant
    import qdrant_client
except ImportError:
    pass

try:
    from langchain_community.vectorstores import FAISS
except ImportError:
    pass

# Import search tools for web, image, and video search
from .agent_pipeline import AgentPipeline
from .session_manager import SessionManager


from ..config import settings
from ..util.logger import setup_logger

logger = setup_logger(__name__)

class SearchQuery:
    """Represents a search query with its results and metadata"""
    
    def __init__(self, query: str, _query: Optional[str] = None):
        self.id = str(uuid.uuid4())
        self.query = query
        self.enhanced_query = _query
        self.timestamp = datetime.now()
        self.results = []
        self.reasoning = []
        self.sources = []
        self.execution_time = 0
        self.image_results = []
        self.video_results = []
    
    def dict(self):
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "query": self.query,
            "enhanced_query": self.enhanced_query,
            "timestamp": self.timestamp.isoformat(),
            "results_count": len(self.results),
            "sources_count": len(self.sources),
            "has_images": len(self.image_results) > 0,
            "has_videos": len(self.video_results) > 0
        }

class SearchSession:
    """Manages a search session with multiple queries"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.id = session_id or str(uuid.uuid4())
        self.queries: List[SearchQuery] = []
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.conversation_context: Dict[str, Any] = {}  # Store context like entities, topics, etc.
    
    def add_query(self, query: SearchQuery):
        """Add a query to the session"""
        self.queries.append(query)
        self.updated_at = datetime.now()
    
    def get_context(self, max_queries: int = 5) -> List[Dict[str, Any]]:
        """Get context from previous queries for continuity"""
        return [
            {
                "query": q.query,
                "results": q.results,
                "timestamp": q.timestamp.isoformat()
            }
            for q in self.queries[-max_queries:]
        ]
    
    def get_conversation_history(self, max_entries: int = 5) -> str:
        """Get formatted conversation history for context inclusion"""
        if not self.queries:
            return ""
            
        history = []
        for i, q in enumerate(self.queries[-max_entries:]):
            history.append(f"User: {q.query}")
            if q.results and len(q.results) > 0:
                # Get first result content
                result = q.results[0].get("content", "No answer provided")
                # Truncate if too long
                if len(result) > 500:
                    result = result[:500] + "..."
                history.append(f"Assistant: {result}")
        
        return "\n".join(history)

from .agent_pipeline import AgentPipeline
from .session_manager import SessionManager

class SearchAgent:
    """
    Agentic search engine using AgentPipeline and SessionManager only.
    """
    def __init__(self, model_provider: str = "gemini", model_name: Optional[str] = None, verbose: bool = False):
        self.model_provider = model_provider.lower()
        self.model_name = model_name
        self.verbose = verbose
        self.session_manager = SessionManager()
        self.agent_pipeline = AgentPipeline(self.session_manager)

    async def execute_pipeline_search(
        self,
        user_id: str,
        query: str,
        model: str = None,
        max_results: int = 20
    ) -> dict:
        """Run the agent pipeline for the given query and user/session."""
        logger.info(f"Executing search for user_id: {user_id}")
        model = model or self.model_provider
        try:
            return await self.agent_pipeline.run(user_id, query, model=model, max_results=max_results)
        except Exception as e:
            logger.error(f"Error executing search: {str(e)}")
            return {
                "queries": [query],
                "web_results": [],
                "images": [],
                "videos": [],
                "error": str(e)
            }
            
    async def close(self):
        """Close all resources when done."""
        await self.agent_pipeline.close()
        
    async def __aenter__(self):
        """Enable async context manager pattern."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources on exit."""
        await self.close()

    # Define available model providers
    MODEL_PROVIDERS = {
        "openai": {
            "models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            "default": "gpt-4o"
        },
        "google": {
            "models": ["gemini-2.5-flash-preview-04-17", "gemini-1.5-flash"],
            "default": "gemini-2.5-flash-preview-04-17"
        },
        "anthropic": {
            "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "default": "claude-3-opus"
        }
    }
    
    # Define available search modalities
    SEARCH_MODALITIES = ["text", "images", "videos"]
    
    def __init__(self, model_provider: str = "openai", model_name: Optional[str] = None, verbose: bool = False):
        """Initialize the Search Agent with necessary components"""
        logger.info("Initializing Search Agent")
        
        self.model_provider = model_provider.lower()
        self.model_name = model_name
        self.verbose = verbose
        
        # Initialize LLM based on provider
        self.llm = self._initialize_llm()
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY
        )
        
        # Initialize vector store
        self.vector_store = self._initialize_vector_store()
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Initialize agent
        self.agent_executor = self._initialize_agent()
        
        # Initialize sessions
        self.sessions = {}
        
        # Initialize search tools
        self.web_search = SerperSearchTool()
        self.wiki_search = WikipediaSearchTool()
        self.image_search = SerpAPIImageSearch()
        self.video_search = SerpAPIVideoSearch()
        self.serper_search = SerperSearchTool()
        # Note: actual tool selection happens in _initialize_tools based on API key.
    
    def _initialize_llm(self):
        """Initialize LLM based on provider and model name"""
        if self.model_provider == "openai":
            model = self.model_name or self.MODEL_PROVIDERS["openai"]["default"]
            return ChatOpenAI(
                model=model,
                temperature=settings.TEMPERATURE,
                api_key=settings.OPENAI_API_KEY,
                streaming=True,
                callback_manager=CallbackManager([StreamingStdOutCallbackHandler()])
            )
        elif self.model_provider in ("google", "gemini"):
            # Gemini (Google) integration
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
            except ImportError:
                raise ImportError("Install 'langchain-google-genai' for Google Gemini support")
            model_choice = self.model_name or self.MODEL_PROVIDERS["google"]["default"]
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=settings.TEMPERATURE,
                google_api_key=settings.GOOGLE_API_KEY
            )
        elif self.model_provider == "anthropic":
            # Claude (Anthropic) integration
            try:
                from langchain.chat_models import ChatAnthropic
            except ImportError:
                raise ImportError("Install 'anthropic' or 'langchain[anthropic]' for Claude support")
            model_choice = self.model_name or self.MODEL_PROVIDERS["anthropic"]["default"]
            return ChatAnthropic(
                model=model_choice,
                temperature=settings.TEMPERATURE,
                api_key=settings.CLAUDE_API_KEY
            )
        else:
            # Default to OpenAI
            return ChatOpenAI(
                model=settings.LLM_MODEL,
                temperature=settings.TEMPERATURE,
                api_key=settings.OPENAI_API_KEY,
                streaming=True,
                callback_manager=CallbackManager([StreamingStdOutCallbackHandler()])
            )
        
    def _initialize_vector_store(self):
        """Initialize the appropriate vector store based on configuration"""
        vector_db = settings.VECTOR_DB.lower()
        
        if vector_db == "pinecone":
            # Use Pinecone v3+ SDK and langchain_pinecone integration
            pc = Pinecone(
                api_key=settings.PINECONE_API_KEY,
                environment=settings.PINECONE_ENVIRONMENT
            )
            # TODO: Set the correct cloud and region for your Pinecone project!
            if settings.PINECONE_INDEX not in [i.name for i in pc.list_indexes()]:
                pc.create_index(
                    name=settings.PINECONE_INDEX,
                    dimension=1536,  # Make sure this matches your embedding model
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',      # <-- CHANGE THIS if your Pinecone project uses a different cloud
                        region='us-west-2' # <-- CHANGE THIS to your Pinecone region
                    )
                )
            index = pc.Index(settings.PINECONE_INDEX)
            return PineconeVectorStore(
                index=index,
                embedding=self.embeddings
            )

        elif vector_db == "weaviate" and "Weaviate" in globals():
            # Initialize Weaviate
            client = weaviate.Client(
                url=settings.WEAVIATE_URL,
                auth_client_secret=weaviate.AuthApiKey(api_key=settings.WEAVIATE_API_KEY)
            )
            
            return Weaviate(
                client=client,
                index_name=settings.WEAVIATE_INDEX,
                text_key="content",
                embedding=self.embeddings
            )
            
        elif vector_db == "qdrant" and "Qdrant" in globals():
            # Initialize Qdrant
            client = qdrant_client.QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY
            )
            
            return Qdrant(
                client=client,
                collection_name=settings.QDRANT_COLLECTION,
                embedding=self.embeddings
            )
            
        elif "FAISS" in globals():
            # Fallback to FAISS as in-memory vector store
            logger.info(f"Vector DB {vector_db} not available, falling back to FAISS")
            
            # Create a small sample collection
            texts = ["AI search engines", "Vector databases", "Large language models", "Semantic search"]
            metadatas = [{"source": "sample"} for _ in texts]
            
            return FAISS.from_texts(
                texts=texts,
                embedding=self.embeddings,
                metadatas=metadatas
            )
        else:
            logger.warning("No vector store initialized - some functions may be limited")
            return None
    
    def _initialize_tools(self) -> List[Tool]:
        """Initialize search and utility tools"""
        tools = []

        # Helper function to run async search in sync context
        def sync_search(search_func):
            def wrapper(query):
                # Remove quotes to improve search results
                cleaned_query = query.replace('"', '').strip()
                
                try:
                    # Get the current event loop or create a new one
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        # No event loop in thread, create one
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    if loop.is_running():
                        # Execute in thread-safe way
                        from concurrent.futures import ThreadPoolExecutor
                        with ThreadPoolExecutor() as pool:
                            future = pool.submit(lambda: asyncio.new_event_loop().run_until_complete(search_func(cleaned_query)))
                            return future.result()
                    else:
                        return loop.run_until_complete(search_func(cleaned_query))
                except Exception as e:
                    logger.error(f"Search error in wrapper: {str(e)}")
                    # Return empty list on error rather than crashing
                    return []
            return wrapper

        # Web search tool: Prefer Serper.dev if API key is set, else DuckDuckGo
        if hasattr(settings, "SERPER_API_KEY") and settings.SERPER_API_KEY:
            logger.info("Using Serper.dev as the main web search tool.")
            tools.append(
                Tool(
                    name="web_search",
                    func=sync_search(lambda q: self.serper_search.search(q.replace('"', ''))),
                    description="Primary: Uses Serper.dev to search the web for up-to-date information. Input should be a search query."
                )
            )
        else:
            logger.info("SERPER_API_KEY not set. Falling back to DuckDuckGo for web search.")
            tools.append(
                Tool(
                    name="web_search",
                    func=sync_search(lambda q: self.web_search.search(q.replace('"', ''))),
                    description="Fallback: Uses DuckDuckGo to search the web for up-to-date information. Input should be a search query."
                )
            )

        # Wikipedia search tool
        tools.append(
            Tool(
                name="wikipedia",
                func=sync_search(lambda q: self.wiki_search.search(q.replace('"', ''))),
                description="Useful for searching Wikipedia for well-known facts, historical events, or general knowledge. Input should be a search query."
            )
        )

        # Add vector store tool if available
        if self.vector_store:
            retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )
            retriever_tool = create_retriever_tool(
                retriever,
                "knowledge_base",
                "Useful for retrieving specific information from the knowledge base. Input should be a search query."
            )
            tools.append(retriever_tool)

        return tools
    
    def _initialize_agent(self) -> AgentExecutor:
        """Initialize the LangChain agent with tools"""
        # Define the agent prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are an advanced LLM that talks with people in a conversational manner and also an AI search assistant (YOU ARE CALLED NEXUS, SO IF YOU NEED TO SPECIFY YOUR CREATION YOU SAY YOU ARE NEXUS AN AI SEARCH ENGINE FOUNDED BY CLYDE TADIWA. YOU CAN JUST SAY OTHER TYPICAL THINGS JUST AROUND BEING CREATED BY NEXUS. LIKE WHAT A TYPICAL LLM WOULD ) that provides comprehensive and accurate answers. 
             
            IMPORTANT: First determine if the user's message is:
            1. A conversational statement or greeting (like "thanks", "hello", "how are you", who created you...,  etc.)
            2. An actual information query requiring search
             
            For conversational messages, respond naturally WITHOUT using any search tools or looking up information.
            
            When given a query, first check the provided search results. BUT YOU DO NOT NEED TO CHECK THE RESULTS IF THE MESSAGE IS CONVERSATIONAL If the search results 
            contain sufficient information to answer the query, use that information primarily. 
            Only use the available TOOLS when you need additional information not present in the 
            initial search results.
            YOUR REPLY SHOULD NOT BE SOMETHING LIKE "BASED ON SEARCH RESULTS...", But just the answer, in detail though. 
             
           
            
            For conversational messages, respond naturally WITHOUT using any search tools or looking up information.
            
            When citing sources, provide specific attribution including the title and URL if available.
            
            If neither the search results nor the tools provide an answer, you may use your existing 
            knowledge but clearly indicate this to the user.
            
            Avoid repeating yourself and present information in a clear, organized manner, and in as much detail.
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create an agent with tools
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        
        # Create an agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=self.verbose,
            max_iterations=settings.MAX_ITERATIONS,
            early_stopping_method="generate"
        )
        
        return agent_executor
        
    async def _enhance_query(self, query: str, session: Optional[SearchSession] = None) -> str:
        """Enhance the original query to get better search results, considering conversation context"""
        if not settings.USE_QUERY_ENHANCEMENT:
            return query
            
        try:
            # Use conversation history as context if available
            conversation_context = ""
            if session and session.queries:
                conversation_context = f"""
                Previous conversation:
                {session.get_conversation_history(max_entries=3)}
                """
            
            # For very short queries that might be failing, use a different enhancement approach
            if len(query.split()) <= 3 and any(term in query.lower() for term in ['latest', 'news', 'recent']):
                # This is likely a 'latest news' type query that's failing, use a more straightforward enhancement
                person_name = query.lower().replace('latest', '').replace('news', '').replace('recent', '').strip()
                enhanced_query = f"{person_name} recent news announcements activities 2025"
                logger.info(f"Special handling for news query. Enhanced: {enhanced_query}")
                return enhanced_query
                
            # Prepare the enhancement prompt with conversation context if available
            enhancement_prompt = f"""
            {conversation_context}
            
            Please enhance this search query to get more accurate and comprehensive results. BUT DO NOT INCLUDE ANY TERMS THAT MIGHT GET OFF SUBJECT:
            
            Original query: {query}
            
           
            
            ONLY ENHANCE THE QUERY IF NECESSARY. IF NOT NECESSARY JUST RETURN THE ORIGINAL QUERY TEXT WITH NO EXPLANATION.
            DO NOT ASSUME WHAT THE USER MEANS.
            DO NOT include quotation marks in your enhanced query.
            Return ONLY the enhanced query text with no explanation.
            """
            
            response = await self.llm.ainvoke(enhancement_prompt)
            enhanced_query = response.content.strip()
            
            # Remove quotes that might restrict search results
            enhanced_query = enhanced_query.replace('"', '')
            
            if enhanced_query:
                logger.info(f"Enhanced query: {enhanced_query}")
                return enhanced_query
            else:
                return query
                
        except Exception as e:
            logger.error(f"Error enhancing query: {str(e)}")
            return query
    
    async def search(
        self, 
        query: str, 
        max_results: int = None, 
        use_web: bool = True, 
        depth: int = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], float]:
        """
        Execute a search query and return the results
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            use_web: Whether to use web search tools
            depth: Depth of search (1-3) for more comprehensive results
        
        Returns:
            Tuple of (results, reasoning_steps, sources, execution_time)
        """
        start_time = time.time()
        
        # Normalize parameters
        max_results = max_results or settings.MAX_RESULTS
        depth = depth or settings.SEARCH_DEPTH
        
        # First run web search to gather sources
        sources = []
        search_context = ""
        
        if use_web:
            try:
                logger.info(f"Gathering web search results for query: {query}")
                
                # Try multiple search strategies if needed
                search_queries = [
                    query,  # Try original query first
                    query.replace('"', '')  # Try without quotes
                ]
                
                # For specific types of queries (like "latest news"), also try simplified versions
                if any(term in query.lower() for term in ['latest', 'news', 'recent']):
                    # Extract name part (assuming format like "Person Name latest")
                    name_part = query.lower()
                    for term in ['latest', 'news', 'recent']:
                        name_part = name_part.replace(term, '')
                    name_part = name_part.strip()
                    
                    # Add simplified queries
                    search_queries.extend([
                        f"{name_part} recent news",
                        f"{name_part} 2025 news",
                        f"{name_part} latest activities"
                    ])
                
                # Try different search services and queries until we get results
                for search_query in search_queries:
                    # Use Serper.dev as the primary search tool if available
                    if hasattr(settings, "SERPER_API_KEY") and settings.SERPER_API_KEY:
                        serper_results = await self.serper_search.search(search_query, max_results=max_results)
                        if serper_results:
                            sources.extend(serper_results)
                            logger.info(f"Found {len(serper_results)} Serper results with query: {search_query}")
                    
                    # Only continue to other search sources if we haven't found anything
                    if not sources and settings.USE_WIKIPEDIA:
                        wiki_results = await self.wiki_search.search(search_query, max_results=max(3, max_results // 2))
                        if wiki_results:
                            sources.extend(wiki_results)
                            logger.info(f"Found {len(wiki_results)} Wikipedia results with query: {search_query}")
                    
                    # Only continue to other search sources if we haven't found anything
                    if not sources and settings.USE_DUCKDUCKGO:
                        web_results = await self.web_search.search(search_query, max_results=max_results)
                        if web_results:
                            sources.extend(web_results)
                            logger.info(f"Found {len(web_results)} DuckDuckGo results with query: {search_query}")
                    
                    # If we found results with this query, stop trying other queries
                    if sources:
                        break
                        
                # If we still have no results, use a fallback
                if not sources:
                    # Create a minimal fallback result to inform the user
                    fallback_time = datetime.now().strftime("%Y-%m-%d")
                    sources = [{
                        'title': 'Search Results Not Available',
                        'snippet': f"Unable to retrieve search results for '{query}'. Consider trying a different search term or checking back later.",
                        'url': 'https://example.com',
                        'source': 'fallback_message'
                    }]
            except Exception as e:
                logger.error(f"Error during web search: {str(e)}")
                # Provide fallback sources on error
                sources = [{
                    'title': 'Search Error',
                    'snippet': f"An error occurred while searching: {str(e)}. You can try reformulating your query.",
                    'url': 'https://example.com',
                    'source': 'error_message'
                }]
            
            # Format search results to include in LLM context
            if sources:
                search_context = "Here are search results from the web that might help answer the query:\n\n"
                for idx, source in enumerate(sources[:max_results]):
                    search_context += f"[{idx+1}] {source.get('title', 'Untitled')}\n"
                    search_context += f"URL: {source.get('url', 'No URL')}\n"
                    search_context += f"Snippet: {source.get('snippet', 'No content')}\n\n"
                    # Add full content if available
                    if source.get('content'):
                        search_context += f"Content: {source.get('content')[:500]}...\n\n"
        
        # Prepare input with search context
        agent_input = query
        if search_context:
            agent_input = f"{query}\n\n{search_context}\n\nPlease provide a comprehensive answer based on these search results. Only use search tools if you need additional information not found in these results."
        else:
            # If we have no search context, make it clear to the LLM
            agent_input = f"{query}\n\nNo search results were found for this query. Please answer based on your general knowledge, but be clear about the limitations of your information."
        
        # Now execute search with the prepared context
        try:
            response = await self.agent_executor.ainvoke({
                "input": agent_input,
                "chat_history": []
            })
            
            output = response.get("output", "")
            
            # Extract reasoning steps (intermediate_steps contains tool inputs and outputs)
            reasoning_steps = []
            for idx, step in enumerate(response.get("intermediate_steps", [])):
                action = step[0]
                tool_input = action.tool_input if hasattr(action, "tool_input") else ""
                reasoning_steps.append({
                    "step": idx + 1,
                    "thought": f"Using {action.tool} to find information about '{tool_input}'"
                })
            
            # Process results
            results = [{
                "content": output,
                "type": "text"
            }]
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            return results, reasoning_steps, sources, execution_time
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            
            # Provide a fallback response
            results = [{
                "content": f"I encountered an error while searching for '{query}'. Please try again or rephrase your query.",
                "type": "error"
            }]
            
            reasoning_steps = [{
                "step": 1,
                "thought": f"Encountered an error: {str(e)}"
            }]
            
            execution_time = time.time() - start_time
            
            return results, reasoning_steps, [], execution_time
    
    async def search_images(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for images related to the query"""
        try:
            return await self.image_search.search(query, max_results=max_results)
        except Exception as e:
            logger.error(f"Image search error: {str(e)}")
            return []
    
    async def search_videos(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for videos related to the query"""
        try:
            return await self.video_search.search(query, max_results=max_results)
        except Exception as e:
            logger.error(f"Video search error: {str(e)}")
            return []
    
    async def execute_search(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_results: int = 10,
        modalities: List[str] = ["text"],
        use_enhancement: bool = True,
        model_provider: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a search across specified modalities and return combined results
        
        Args:
            query: The search query
            session_id: Session ID for continuity
            max_results: Maximum results per modality
            modalities: List of modalities to search (text, images, videos)
            use_enhancement: Whether to enhance the query
            model_provider: Override the model provider
            model_name: Override the model name
            
        Returns:
            Dictionary with search results for all modalities
        """
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
                
            # Create session if not exists
            if session_id not in self.sessions:
                self.sessions[session_id] = SearchSession(session_id)
                
            session = self.sessions[session_id]
            
            # Create search query object
            search_query = SearchQuery(query=query)
            
            # Enhance query if enabled, using session context
            enhanced_query = query
            if use_enhancement:
                enhanced_query = await self._enhance_query(query, session)
                search_query.enhanced_query = enhanced_query
                
            # Set query to use for search
            query_to_use = enhanced_query if use_enhancement else query
            
            # Execute text search
            results, reasoning_steps, sources, execution_time = await self.search(
                query=query_to_use,
                max_results=max_results
            )
            
            # Generate related searches
            related_searches = await self.generate_related_searches(query, results, sources)
            
            # Store results in query object
            search_query.results = results
            search_query.reasoning = reasoning_steps
            search_query.sources = sources
            search_query.execution_time = execution_time
            
            # Execute image search if requested
            image_results = []
            if "images" in modalities:
                image_results = await self.search_images(query_to_use, max_results=max_results)
                search_query.image_results = image_results
                
            # Execute video search if requested
            video_results = []
            if "videos" in modalities:
                video_results = await self.search_videos(query_to_use, max_results=max_results)
                search_query.video_results = video_results
                
            # Add query to session
            session.add_query(search_query)
            
            # Update session's conversation context with entities from this query
            # This is a simple approach; you might want a more sophisticated entity extraction
            if results and len(results) > 0:
                # Extract potential entities from the search query and results
                # This is where you'd implement more advanced entity recognition
                pass
            
            # Prepare response
            response = {
                "results": results,
                "reasoning_steps": reasoning_steps,
                "sources": sources,
                "execution_time": execution_time,
                "session_id": session_id,
                "enhanced_query": enhanced_query if use_enhancement else None,
                "image_results": image_results,
                "video_results": video_results,
                "has_images": len(image_results) > 0,
                "has_videos": len(video_results) > 0,
                "related_searches": related_searches
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Execute search error: {str(e)}")
            return {
                "results": [{
                    "content": f"I encountered an error while processing your search for '{query}'. Please try again or rephrase your query.",
                    "type": "error"
                }],
                "reasoning_steps": [{
                    "step": 1,
                    "thought": f"Encountered an error: {str(e)}"
                }],
                "sources": [],
                "execution_time": 0.0,
                "session_id": session_id or str(uuid.uuid4()),
                "enhanced_query": None,
                "image_results": [],
                "video_results": [],
                "has_images": False,
                "has_videos": False,
                "related_searches": []
            }
    
    async def generate_related_searches(self, query: str, results: List[Dict[str, Any]], sources: List[Dict[str, Any]], max_suggestions: int = 5) -> List[str]:
        """
        Generate related search suggestions based on the original query and search results.
        
        Args:
            query: The original search query
            results: Search results from the main query
            sources: Sources used in the search
            max_suggestions: Maximum number of suggestions to generate
            
        Returns:
            List of related search queries
        """
        try:
            # Extract key information from results and sources
            key_topics = []
            
            # Get content from results
            result_content = ""
            if results and len(results) > 0:
                result_content = results[0].get("content", "")
                if len(result_content) > 800:
                    result_content = result_content[:800]
            
            # Get titles and snippets from sources
            source_info = []
            if sources and len(sources) > 0:
                for source in sources[:3]:
                    title = source.get("title", "")
                    snippet = source.get("snippet", "")
                    if title or snippet:
                        source_info.append(f"{title}: {snippet}")
            
            # Create a very focused prompt that forces specific related searches
            prompt = f"""
            Based on the user's search query: "{query}" and the following information:
            {result_content}
            
            Generate {max_suggestions} SPECIFIC related search queries that users might be interested in.
            These should be diverse, relevant, specific, and cover different aspects of the topic.
            
            DO NOT use generic templates like "{query} tutorial" or "{query} latest". Each query must be unique and specific to the topic.
            
            IMPORTANT: Format your response as a JSON array of strings containing ONLY the related search queries. 
            No explanations or additional text.
            
            For example:
            ["specific related query 1", "specific related query 2", "specific related query 3"]
            """
            
            # Call LLM with the focused prompt
            logger.info(f"Generating related searches for query: '{query}'")
            response = await self.llm.ainvoke(prompt)
            result_text = response.content.strip()
            logger.info(f"Raw LLM response for related searches: {result_text[:200]}...")
            
            # First attempt: Try to parse the entire response as JSON
            try:
                # Clean the response - sometimes there are markdown code blocks
                clean_text = result_text
                if "```json" in result_text:
                    clean_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    clean_text = result_text.split("```")[1].split("```")[0].strip()
                
                # Check if the entire result is a valid JSON array
                related_queries = json.loads(clean_text)
                
                if isinstance(related_queries, list) and all(isinstance(q, str) for q in related_queries):
                    logger.info(f"Successfully parsed complete JSON with {len(related_queries)} related searches")
                    
                    # Validate quality - ensure they're not just templates
                    template_patterns = [f"{query} tutorial", f"{query} guide", f"{query} latest", f"best {query}"]
                    template_count = 0
                    for rq in related_queries:
                        if any(pattern.lower() in rq.lower() for pattern in template_patterns):
                            template_count += 1
                    
                    # If more than half look like templates, reject
                    if template_count <= len(related_queries) / 2:
                        # We have good queries
                        return related_queries[:max_suggestions]
                    else:
                        logger.warning(f"Rejected related searches - {template_count} of {len(related_queries)} appear to be templates")
            except Exception as e:
                logger.warning(f"JSON parsing failed: {str(e)}")
            
            # Second attempt: Try to extract queries line by line with improved pattern matching
            logger.info("Attempting line-by-line extraction of related searches")
            fallback_queries = []
            
            # Try to find quoted strings
            quote_pattern = r'"([^"]+)"'
            quoted_matches = re.findall(quote_pattern, result_text)
            if quoted_matches and len(quoted_matches) >= 2:  # At least a couple of matches suggests a pattern
                logger.info(f"Found {len(quoted_matches)} quoted strings that might be related searches")
                fallback_queries = quoted_matches[:max_suggestions]
            else:
                # No quoted strings found, try line-by-line
                lines = result_text.split("\n")
                for line in lines:
                    # Skip empty lines and lines that look like JSON syntax or explanations
                    line = line.strip()
                    if not line or line in ['[', ']', '{', '}', ','] or line.startswith('//') or line.startswith('#'):
                        continue
                        
                    # Look for patterns like: "1. query", "- query", "• query", "query"
                    # Remove common prefixes
                    for prefix in ['"', "'", "- ", "• ", "* "]:
                        if line.startswith(prefix):
                            line = line[len(prefix):]
                            
                    # Remove numbering like "1. ", "2. "
                    line = re.sub(r'^\d+[\.\)]\s*', '', line)
                    
                    # Remove quotes and trailing commas
                    line = line.strip('"\'').rstrip(',')
                    
                    if line and len(line) > 3 and not line.lower().startswith(("here", "these", "example")):
                        fallback_queries.append(line)
                        if len(fallback_queries) >= max_suggestions:
                            break
            
            if fallback_queries:
                logger.info(f"Extracted {len(fallback_queries)} related searches using line-by-line method")
                return fallback_queries[:max_suggestions]
            
            # If we still don't have results, try a completely different approach
            # Generate specific questions about the topic
            logger.info("Trying question-based approach for related searches")
            try:
                questions_prompt = f"""
                What are {max_suggestions} specific questions people might have about "{query}"?
                Each question should explore a different aspect of the topic.
                
                Format your response as a list with one question per line.
                DO NOT use numbers or bullet points.
                """
                
                questions_response = await self.llm.ainvoke(questions_prompt)
                questions_text = questions_response.content.strip()
                
                # Extract questions
                questions = []
                for line in questions_text.split("\n"):
                    line = line.strip()
                    if not line or line.startswith(("-", "*", "•", "#")):
                        continue
                    
                    # Clean up the line
                    line = re.sub(r'^\d+[\.\)]\s*', '', line)  # Remove numbering
                    line = line.rstrip("?")  # Remove question mark
                    
                    if len(line) > 5:
                        questions.append(line)
                
                if questions and len(questions) >= 2:
                    logger.info(f"Generated {len(questions)} question-based related searches")
                    return questions[:max_suggestions]
            except Exception as e:
                logger.warning(f"Question-based related search generation failed: {str(e)}")
            
            # If all other methods fail, generate topic-based searches
            logger.warning(f"Could not extract structured related searches, generating topic-based alternatives")
            try:
                # Find related topics first
                topics_prompt = f"""
                List {max_suggestions} specific topics or aspects directly related to "{query}".
                Each topic should be a short phrase (2-5 words) that could be searched for more information.
                
                Format your response as a list with one topic per line.
                DO NOT use any bullet points or numbers.
                """
                
                topics_response = await self.llm.ainvoke(topics_prompt)
                topics_text = topics_response.content.strip()
                
                # Extract topics
                topics = []
                for line in topics_text.split("\n"):
                    line = line.strip()
                    if not line or line.startswith(("-", "*", "•", "#")):
                        continue
                    
                    # Clean up
                    line = re.sub(r'^\d+[\.\)]\s*', '', line)  # Remove numbering
                    line = line.strip('"\'')  # Remove quotes
                    
                    if len(line) > 3 and len(line.split()) <= 5:
                        topics.append(line)
                
                if topics and len(topics) >= 2:
                    logger.info(f"Generated {len(topics)} topic-based related searches")
                    return topics[:max_suggestions]
            except Exception as e:
                logger.warning(f"Topic-based search generation failed: {str(e)}")
                
            # Absolute last resort - generate high-quality template queries
            # These should be more varied than before
            emergency_fallbacks = [
                f"experts on {query}",
                f"{query} analysis",
                f"{query} key findings",
                f"{query} latest developments",
                f"{query} practical applications",
                f"{query} future outlook",
                f"{query} benefits",
                f"{query} impact assessment",
                f"{query} key metrics",
                f"innovations in {query}"
            ]
            
            # Use a different subset based on query hash for variety
            variation = sum(ord(c) for c in query) % 5
            final_searches = emergency_fallbacks[variation:variation+max_suggestions]
            if len(final_searches) < max_suggestions:
                final_searches += emergency_fallbacks[:max_suggestions-len(final_searches)]
                
            logger.info(f"Using {len(final_searches)} emergency fallback searches")
            return final_searches
            
        except Exception as e:
            logger.error(f"Error generating related searches: {str(e)}")
            # Final emergency fallback with varied alternatives
            varied_fallbacks = [
                f"experts on {query}",
                f"{query} analysis",
                f"{query} research papers", 
                f"{query} controversies",
                f"{query} statistical data",
                f"{query} current trends",
                f"{query} policy implications",
                f"{query} historical context",
                f"{query} global perspective",
                f"future of {query}"
            ]
            
            # Vary based on query hash
            hash_value = sum(ord(c) for c in query) % 5
            selected = varied_fallbacks[hash_value:hash_value+max_suggestions]
            if len(selected) < max_suggestions:
                selected += varied_fallbacks[:max_suggestions-len(selected)]
            
            logger.info(f"Using {len(selected)} exception fallback searches")
            return selected