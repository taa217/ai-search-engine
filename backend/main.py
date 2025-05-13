#!/usr/bin/env python
"""
Nexus AI Search Engine - Main Entry Point
Import and run the FastAPI application from src.main
"""
import os
import uvicorn
from dotenv import load_dotenv
import sys
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import importlib

# Load environment variables
load_dotenv()

# Add the parent directory to the sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.search_agent import SearchAgent

app = FastAPI(title="Nexus AI Search API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ai-search-engine-roan.vercel.app", "http://localhost:3000"],  # Allow frontend domain and local development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(),  # Log to console
        RotatingFileHandler(
            os.path.join(os.path.dirname(__file__), "logs", "api.log"),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
    ]
)

logger = logging.getLogger(__name__)

# Initialize search agent
search_agent = SearchAgent()

class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10
    use_web: Optional[bool] = True
    depth: Optional[int] = 4
    session_id: Optional[str] = None
    modalities: Optional[List[str]] = ["text"]
    use_enhancement: Optional[bool] = True
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    conversation_mode: Optional[bool] = True

@app.post("/api/search")
async def search(request: SearchRequest, background_tasks: BackgroundTasks, client_request: Request):
    client_ip = client_request.client.host
    logger.info(f"Search request from {client_ip}: Query='{request.query}', Session='{request.session_id}'")
    
    try:
        results = await search_agent.execute_search(
            query=request.query,
            session_id=request.session_id,
            max_results=request.max_results,
            modalities=request.modalities,
            use_enhancement=request.use_enhancement,
            model_provider=request.model_provider,
            model_name=request.model_name
        )
        
        logger.info(f"Successfully processed search for Session: {results['session_id']}")
        return results
    except Exception as e:
        logger.error(f"Error processing search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a search session and all its data"""
    logger.info(f"Deleting session: {session_id}")
    
    try:
        # Check if session exists
        if session_id in search_agent.sessions:
            # Remove session from the search agent
            del search_agent.sessions[session_id]
            return {"status": "success", "message": f"Session {session_id} deleted successfully"}
        else:
            logger.warning(f"Session not found: {session_id}")
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
            
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    await search_agent.close()

def main():
    """Main entry point for the application"""
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))
    
    # Start the server
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("DEBUG", "False").lower() == "true",
        log_level="info"
    )

if __name__ == "__main__":
    main() 
