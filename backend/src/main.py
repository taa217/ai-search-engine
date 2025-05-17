"""
Nexus AI Search Engine API
A state-of-the-art agentic search engine built with FastAPI and LangChain
"""
import os
import time
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union
from uuid import uuid4
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends, UploadFile, File, Form, Body, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the agentic search engine and config
from .agents.search_agent import SearchAgent, SearchQuery, SearchSession
from .config import settings
from .util.agentic_search_engine import AgenticSearchEngine
from .util.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Nexus AI Search Engine",
    description="State-of-the-art Agentic AI Search Engine API with multi-modal search capabilities",
    version="3.0.0"
)

# Configure CORS to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# We'll initialize search engine in startup event for proper async handling
search_engine = None

# Initialize search agent
search_agent = SearchAgent(model_provider=settings.LLM_PROVIDER, model_name=settings.LLM_MODEL)

# Initialize agentic search engine
agentic_search_engine = AgenticSearchEngine(
    model_name=settings.LLM_MODEL,
    model_provider=settings.LLM_PROVIDER,
    max_iterations=5,
    verbose=settings.DEBUG
)

# API Models
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    max_results: Optional[int] = Field(5, description="Maximum number of results")
    session_id: Optional[str] = Field(None, description="Session ID for continuity")
    modalities: Optional[List[str]] = Field(["text"], description="Modalities to search (text, images, videos)")
    use_enhancement: Optional[bool] = Field(True, description="Whether to enhance the query")

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    reasoning: List[Dict[str, Any]] = Field(..., description="Reasoning steps")
    sources: List[Dict[str, Any]] = Field(..., description="Source information")
    execution_time: float = Field(..., description="Search execution time in seconds")
    session_id: str = Field(..., description="Session ID for continuity")
    image_results: Optional[List[Dict[str, Any]]] = Field([], description="Image search results")
    video_results: Optional[List[Dict[str, Any]]] = Field([], description="Video search results")
    enhanced_query: Optional[str] = Field(None, description="Enhanced search query")
    related_searches: Optional[List[str]] = Field([], description="AI-generated related searches")
    has_images: Optional[bool] = Field(False, description="Whether image results are available")
    has_videos: Optional[bool] = Field(False, description="Whether video results are available")

class AgenticSearchRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    plan_id: Optional[str] = None
    max_iterations: Optional[int] = 5
    conversation_context: Optional[str] = None
    conversation_mode: Optional[bool] = False

class AgenticSearchResponse(BaseModel):
    plan_id: str
    original_query: str
    research_steps: List[Dict[str, Any]]
    synthesis: str
    status: str  # "initiated", "in_progress", "completed", "error"
    iterations_completed: int
    max_iterations: int
    conversation_context: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Startup tasks for the application"""
    global search_engine
    
    logger.info("Starting up Nexus AI Search Engine API")
    
    # Initialize the search engine
    search_engine = SearchAgent(
        model_provider=os.getenv("DEFAULT_MODEL_PROVIDER", "gemini").lower(),
        model_name=os.getenv("DEFAULT_MODEL_NAME", "gemini-1.5-flash"),
        verbose=settings.DEBUG
    ) 
    
    logger.info(f"Using model provider: {search_engine.model_provider}")
    logger.info(f"Default model: {search_engine.model_name}")
    
    required_packages = ["langchain", "langchain_openai"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.warning(f"Missing required packages: {', '.join(missing_packages)}")
        logger.warning("Some features may not work properly")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks for the application"""
    global search_engine
    
    logger.info("Shutting down Nexus AI Search Engine API")
    
    if search_engine:
        logger.info("Closing search engine resources...")
        await search_engine.close()
        logger.info("Search engine resources closed successfully")

@app.get("/")
async def root():
    """Root endpoint returning basic service information"""
    return {
        "status": "online",
        "service": "Nexus AI Agentic Search Engine API",
        "version": "3.0.0",
        "available_models": [
            {"provider": provider, "models": details["models"]} 
            for provider, details in search_engine.MODEL_PROVIDERS.items()
        ],
        "available_modalities": search_engine.SEARCH_MODALITIES
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "parallel_search": "enabled"}

@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest, req: Request):
    """
    Execute a search query using the agentic pipeline.
    """
    try:
        client_ip = req.client.host if req.client else "unknown"
        logger.info(f"Search request from {client_ip}: Query='{request.query}', Session='{request.session_id}'")

        # Generate or use provided session_id
        user_id = request.session_id or str(uuid4()) # Use consistent naming

        # Call the refactored execute_search method
        results = await search_engine.execute_search(
            query=request.query,
            session_id=user_id,
            max_results=request.max_results or 5,
            modalities=request.modalities,
            use_enhancement=request.use_enhancement
        )

        # Construct the response using data returned by execute_search
        # The SearchResponse model expects specific fields.
        response = SearchResponse(
            results=results.get("results", []), # This contains the agent's text answer
            reasoning=results.get("reasoning", []), # Reasoning steps from the search
            sources=results.get("sources", []),
            execution_time=results.get("execution_time", 0.0),
            session_id=results.get("session_id", user_id), # Get session_id from results
            image_results=results.get("image_results", []),
            video_results=results.get("video_results", []),
            enhanced_query=results.get("enhanced_query"),
            related_searches=results.get("related_searches", []),
            has_images=results.get("has_images", False),
            has_videos=results.get("has_videos", False)
        )

        logger.info(f"Successfully processed search for Session: {response.session_id}")
        return response

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions directly
        raise http_exc
    except Exception as e:
        logger.error(f"Unhandled error processing search query '{request.query}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get information about a search session"""
    if session_id not in search_engine.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = search_engine.sessions[session_id]
    
    # Convert to dict for JSON serialization
    return {
        "id": session.id,
        "queries": [q.dict() for q in session.queries],
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "query_count": len(session.queries)
    }

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a search session"""
    if session_id not in search_engine.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    del search_engine.sessions[session_id]
    return {"status": "success", "message": f"Session {session_id} deleted"}

@app.post("/search", response_model=SearchResponse)
async def search_post(request: SearchRequest):
    """
    Execute a search query and return results.
    
    - query: The search query
    - session_id: Optional session ID for continuity
    - modalities: List of modalities to search (text, images, videos)
    - use_enhancement: Whether to enhance the query
    """
    try:
        response = await search_agent.execute_search(
            query=request.query,
            session_id=request.session_id,
            max_results=10,
            modalities=request.modalities,
            use_enhancement=request.use_enhancement
        )
        
        return response
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.post("/agentic-search", response_model=AgenticSearchResponse)
async def agentic_search(request: AgenticSearchRequest):
    """
    Execute an agentic search that conducts multiple searches and synthesizes results.
    
    - query: The search query
    - session_id: Optional session ID for continuity
    - plan_id: Optional plan ID to continue an existing research plan
    - max_iterations: Maximum number of research iterations (default: 5)
    - conversation_context: Optional previous conversation context for follow-up questions
    - conversation_mode: Whether to use conversation mode for context-aware responses
    """
    try:
        # Override max_iterations if provided
        if request.max_iterations:
            agentic_search_engine.max_iterations = request.max_iterations
            
        # Process the query with context if in conversation mode
        processed_query = request.query
        if request.conversation_mode and request.conversation_context:
            # Log that we're using conversation context
            logger.info(f"Using conversation context for agentic search: Session={request.session_id}")
            
            # Process query with context
            processed_query = f"Previous context:\n{request.conversation_context}\n\nFollow-up question: {request.query}"
            
        # Execute the research process with the processed query
        research_response = await agentic_search_engine.execute_research(
            query=processed_query,
            plan_id=request.plan_id,
            session_id=request.session_id
        )
        
        # Ensure response has all required fields
        response = AgenticSearchResponse(
            plan_id=research_response["plan_id"],
            original_query=research_response["original_query"],
            research_steps=research_response["research_steps"],
            synthesis=research_response["synthesis"],
            status=research_response["status"],
            iterations_completed=research_response["iterations_completed"],
            max_iterations=research_response["max_iterations"],
            conversation_context=request.conversation_context if request.conversation_mode else None
        )
        
        return response
    except Exception as e:
        logger.error(f"Agentic search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agentic search error: {str(e)}")

@app.get("/research-plan/{plan_id}")
async def get_research_plan(plan_id: str):
    """
    Get the current status and results of a research plan.
    
    - plan_id: The ID of the research plan
    """
    try:
        plan = await agentic_search_engine.get_research_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail=f"Research plan {plan_id} not found")
        
        return plan
    except Exception as e:
        logger.error(f"Error retrieving research plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving research plan: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)
