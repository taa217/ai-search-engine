import os
import logging
import time
import uvicorn
import asyncio
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import settings
from .utils.logger import setup_logger
from .agents.search_agent_fixed import SearchAgent

# Setup logger
logger = setup_logger(__name__)

# Initialize the app
app = FastAPI(
    title="Nexus AI Search API",
    description="API for searching the web with AI augmented results",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the search agent
search_agent = None

# Define request/response models
class SearchRequest(BaseModel):
    query: str = Field(..., description="The search query to execute")
    session_id: Optional[str] = Field(None, description="Session ID for continuity")
    max_results: int = Field(10, description="Maximum number of results to return")
    modalities: List[str] = Field(["text"], description="Modalities to search (text, images, videos)")
    enhance_query: bool = Field(True, description="Whether to enhance the query")

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    reasoning_steps: List[Dict[str, Any]] = Field(..., description="Reasoning steps")
    sources: List[Dict[str, Any]] = Field(..., description="Sources of information")
    session_id: str = Field(..., description="Session ID for continuity")
    execution_time: float = Field(..., description="Search execution time in seconds")
    enhanced_query: Optional[str] = Field(None, description="Enhanced query if query enhancement was used")
    image_results: List[Dict[str, Any]] = Field([], description="Image search results if requested")
    video_results: List[Dict[str, Any]] = Field([], description="Video search results if requested")

@app.on_event("startup")
async def startup_event():
    """Initialize components during startup"""
    global search_agent
    logger.info("Initializing search agent...")
    search_agent = SearchAgent(
        model_provider="openai",
        model_name=settings.LLM_MODEL,
        verbose=settings.DEBUG
    )
    logger.info("API initialized and ready")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources during shutdown"""
    global search_agent
    if search_agent:
        logger.info("Closing search agent...")
        await search_agent.close()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request and response details"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} completed in {process_time:.4f}s")
    
    return response

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Nexus AI Search API"}

@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Execute a search query with AI reasoning"""
    global search_agent
    
    if not search_agent:
        raise HTTPException(status_code=503, detail="Search agent not initialized")
    
    try:
        logger.info(f"Processing search request: {request.query}")
        
        # Execute search
        response = await search_agent.execute_search(
            query=request.query,
            session_id=request.session_id,
            max_results=request.max_results,
            modalities=request.modalities,
            use_enhancement=request.enhance_query
        )
        
        logger.info(f"Search completed in {response.get('execution_time', 0):.2f}s")
        return response
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing search: {str(e)}")

@app.get("/api/modalities")
async def get_modalities():
    """Get available search modalities"""
    global search_agent
    
    if not search_agent:
        raise HTTPException(status_code=503, detail="Search agent not initialized")
        
    return {"modalities": search_agent.SEARCH_MODALITIES}

@app.get("/api/models")
async def get_models():
    """Get available models"""
    global search_agent
    
    if not search_agent:
        raise HTTPException(status_code=503, detail="Search agent not initialized")
        
    return {"models": search_agent.MODEL_PROVIDERS}

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    ) 