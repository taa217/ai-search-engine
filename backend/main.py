"""
Nexus AI Search Engine - Main API
A clean, minimal search engine powered by Perplexity API
Compatible with the existing frontend interface
"""
import os
import time
import logging
from typing import Dict, List, Any, Optional
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from perplexity_service import PerplexitySearchService

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Nexus AI Search Engine",
    description="AI Search Engine powered by Perplexity API",
    version="4.0.0"
)

# Configure CORS - allow all origins for development
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Perplexity service
perplexity_service = PerplexitySearchService()

# Store sessions in memory (for conversation continuity)
sessions: Dict[str, List[Dict[str, Any]]] = {}


# --- API Models (matching frontend expectations) ---

class SearchResult(BaseModel):
    content: str
    type: str = "text"


class ReasoningStep(BaseModel):
    step: int
    thought: str


class Source(BaseModel):
    url: Optional[str] = None
    link: Optional[str] = None
    title: str
    snippet: Optional[str] = None
    source: Optional[str] = None


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    max_results: Optional[int] = Field(10, description="Maximum number of results")
    use_web: Optional[bool] = Field(True, description="Whether to use web search")
    depth: Optional[int] = Field(2, description="Search depth")
    modalities: Optional[List[str]] = Field(["text"], description="Search modalities")
    use_enhancement: Optional[bool] = Field(True, description="Whether to enhance query")
    model_provider: Optional[str] = Field(None, description="Model provider")
    model_name: Optional[str] = Field(None, description="Model name")
    conversation_mode: Optional[bool] = Field(True, description="Conversation mode")


class SearchResponse(BaseModel):
    """Response format matching frontend expectations"""
    results: List[SearchResult] = Field(..., description="Search results with content")
    reasoning: List[ReasoningStep] = Field(default=[], description="Reasoning steps")
    sources: List[Source] = Field(default=[], description="Source citations")
    execution_time: float = Field(..., description="Search execution time in seconds")
    session_id: str = Field(..., description="Session ID")
    image_results: Optional[List[Dict[str, Any]]] = Field(default=[], description="Image results")
    video_results: Optional[List[Dict[str, Any]]] = Field(default=[], description="Video results")
    enhanced_query: Optional[str] = Field(None, description="Enhanced query")
    has_images: Optional[bool] = Field(False, description="Has image results")
    has_videos: Optional[bool] = Field(False, description="Has video results")
    conversation_context: Optional[str] = Field(None, description="Conversation context")
    related_searches: Optional[List[str]] = Field(default=[], description="Related searches")


# --- API Endpoints ---

@app.get("/")
async def root():
    """Root endpoint returning basic service information"""
    return {
        "status": "online",
        "service": "Nexus AI Search Engine",
        "version": "4.0.0",
        "powered_by": "Perplexity API",
        "available_models": ["sonar", "sonar-pro", "sonar-reasoning-pro"]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    api_key_configured = bool(os.getenv("PERPLEXITY_API_KEY"))
    return {
        "status": "healthy" if api_key_configured else "unhealthy",
        "api_key_configured": api_key_configured
    }


@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest, req: Request):
    """
    Execute a search query using Perplexity API.
    Returns response in format compatible with existing frontend.
    """
    start_time = time.time()
    
    try:
        client_ip = req.client.host if req.client else "unknown"
        logger.info(f"Search request from {client_ip}: Query='{request.query}'")
        
        # Generate or use provided session_id
        session_id = request.session_id or str(uuid4())
        
        # Get conversation history for context
        conversation_history = sessions.get(session_id, [])
        
        # Determine model based on modalities or use default
        model = "sonar"
        if request.model_name:
            model = request.model_name
        
        # Execute search with Perplexity
        result = await perplexity_service.search(
            query=request.query,
            conversation_history=conversation_history,
            model=model
        )
        
        # Update session history
        if session_id not in sessions:
            sessions[session_id] = []
        
        sessions[session_id].append({
            "role": "user",
            "content": request.query
        })
        sessions[session_id].append({
            "role": "assistant", 
            "content": result["answer"]
        })
        
        # Keep only last 20 messages for context
        if len(sessions[session_id]) > 20:
            sessions[session_id] = sessions[session_id][-20:]
        
        execution_time = time.time() - start_time
        
        # Format results to match frontend expectations
        # The frontend expects results as an array with {content, type}
        results = [SearchResult(content=result["answer"], type="text")]
        
        # Format sources to match frontend expectations
        sources = []
        for src in result.get("sources", []):
            sources.append(Source(
                url=src.get("url", ""),
                link=src.get("url", ""),
                title=src.get("title", "Source"),
                snippet=src.get("snippet", ""),
                source="perplexity"
            ))
        
        # Create reasoning steps (Perplexity doesn't provide these, but frontend expects them)
        reasoning = [
            ReasoningStep(step=1, thought=f"Searching for: {request.query}"),
            ReasoningStep(step=2, thought=f"Found {len(sources)} relevant sources"),
            ReasoningStep(step=3, thought="Generated comprehensive answer with citations")
        ]
        
        response = SearchResponse(
            results=results,
            reasoning=reasoning,
            sources=sources,
            execution_time=execution_time,
            session_id=session_id,
            image_results=[],
            video_results=[],
            enhanced_query=request.query,
            has_images=False,
            has_videos=False,
            conversation_context=None,
            related_searches=result.get("related_searches", [])
        )
        
        logger.info(f"Search completed in {execution_time:.2f}s for session {session_id}")
        return response
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/agentic-search")
async def agentic_search(request: SearchRequest, req: Request):
    """
    Execute an agentic/deep search using Perplexity API.
    Uses sonar-pro for more comprehensive results.
    """
    start_time = time.time()
    
    try:
        client_ip = req.client.host if req.client else "unknown"
        logger.info(f"Agentic search request from {client_ip}: Query='{request.query}'")
        
        session_id = request.session_id or str(uuid4())
        conversation_history = sessions.get(session_id, [])
        
        # Use sonar-pro for deep research
        result = await perplexity_service.search(
            query=request.query,
            conversation_history=conversation_history,
            model="sonar-pro"
        )
        
        # Update session
        if session_id not in sessions:
            sessions[session_id] = []
        sessions[session_id].append({"role": "user", "content": request.query})
        sessions[session_id].append({"role": "assistant", "content": result["answer"]})
        
        execution_time = time.time() - start_time
        
        # Format sources
        sources = []
        for src in result.get("sources", []):
            sources.append({
                "url": src.get("url", ""),
                "link": src.get("url", ""),
                "title": src.get("title", "Source"),
                "snippet": src.get("snippet", ""),
                "source": "perplexity"
            })
        
        # Format response for agentic search
        return {
            "plan_id": str(uuid4()),
            "original_query": request.query,
            "research_steps": [
                {
                    "id": "step-1",
                    "query": request.query,
                    "reasoning": "Deep research with Perplexity sonar-pro",
                    "results_count": len(sources),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "execution_time": execution_time
                }
            ],
            "synthesis": result["answer"],
            "status": "completed",
            "iterations_completed": 1,
            "max_iterations": 1,
            "sources": sources,
            "related_searches": result.get("related_searches", [])
        }
        
    except Exception as e:
        logger.error(f"Agentic search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agentic search failed: {str(e)}")


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a search session"""
    if session_id in sessions:
        del sessions[session_id]
        return {"status": "success", "message": f"Session {session_id} deleted"}
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session conversation history"""
    if session_id in sessions:
        return {
            "session_id": session_id,
            "message_count": len(sessions[session_id]),
            "messages": sessions[session_id]
        }
    raise HTTPException(status_code=404, detail="Session not found")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=debug)
