"""
Vercel Serverless Function Entry Point
This file serves as the main entry point for Vercel Python serverless functions
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from uuid import uuid4
import os
import time
import logging
import httpx
import json

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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store sessions in memory
sessions: Dict[str, List[Dict[str, Any]]] = {}


# --- Perplexity Service (inline to avoid import issues) ---

class PerplexitySearchService:
    BASE_URL = "https://api.perplexity.ai"
    
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.default_model = os.getenv("PERPLEXITY_MODEL", "sonar")
    
    async def search(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY is not configured")
        
        model_to_use = model or self.default_model
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful AI search assistant called Nexus. "
                    "Provide comprehensive, accurate answers based on current web information. "
                    "Always cite your sources with numbered references like [1], [2], etc. "
                    "Be conversational but informative."
                )
            }
        ]
        
        if conversation_history:
            messages.extend(conversation_history[-10:])
        
        messages.append({"role": "user", "content": query})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_to_use,
            "messages": messages,
            "temperature": 0.2,
            "return_citations": True,
            "return_related_questions": True
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            answer = ""
            if data.get("choices") and len(data["choices"]) > 0:
                answer = data["choices"][0].get("message", {}).get("content", "")
            
            sources = []
            for i, citation in enumerate(data.get("citations", [])):
                if isinstance(citation, str):
                    sources.append({"index": i + 1, "url": citation, "title": f"Source {i + 1}"})
                elif isinstance(citation, dict):
                    sources.append({
                        "index": i + 1,
                        "url": citation.get("url", ""),
                        "title": citation.get("title", f"Source {i + 1}"),
                        "snippet": citation.get("snippet", "")
                    })
            
            return {
                "answer": answer,
                "sources": sources,
                "model_used": model_to_use,
                "related_searches": data.get("related_questions", [])
            }
    
    async def search_stream(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ):
        """Streaming search that yields content chunks progressively"""
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY is not configured")
        
        model_to_use = model or self.default_model
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful AI search assistant called Nexus. "
                    "Provide comprehensive, accurate answers based on current web information. "
                    "Always cite your sources with numbered references like [1], [2], etc. "
                    "Be conversational but informative."
                )
            }
        ]
        
        if conversation_history:
            messages.extend(conversation_history[-10:])
        
        messages.append({"role": "user", "content": query})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        
        payload = {
            "model": model_to_use,
            "messages": messages,
            "temperature": 0.2,
            "return_citations": True,
            "return_related_questions": True,
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                
                full_content = ""
                sources = []
                related_searches = []
                
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    
                    if line.startswith("data: "):
                        data_str = line[6:]
                        
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            
                            # Extract content - handle both delta (OpenAI style) and message (cumulative)
                            if data.get("choices") and len(data["choices"]) > 0:
                                choice = data["choices"][0]
                                
                                # Try delta first (standard streaming format)
                                delta = choice.get("delta", {})
                                new_content = delta.get("content", "")
                                
                                # If no delta content, check for message (cumulative format)
                                if not new_content:
                                    message = choice.get("message", {})
                                    cumulative_content = message.get("content", "")
                                    # Only yield the new portion
                                    if cumulative_content and len(cumulative_content) > len(full_content):
                                        new_content = cumulative_content[len(full_content):]
                                
                                if new_content:
                                    full_content += new_content
                                    yield {"type": "content", "text": new_content}
                            
                            if "citations" in data:
                                citations = data.get("citations", [])
                                for i, citation in enumerate(citations):
                                    if isinstance(citation, str):
                                        sources.append({"index": i + 1, "url": citation, "title": f"Source {i + 1}"})
                                    elif isinstance(citation, dict):
                                        sources.append({
                                            "index": i + 1,
                                            "url": citation.get("url", ""),
                                            "title": citation.get("title", f"Source {i + 1}"),
                                            "snippet": citation.get("snippet", "")
                                        })
                            
                            if "related_questions" in data:
                                related_searches = data.get("related_questions", [])
                                
                        except json.JSONDecodeError:
                            continue
                
                yield {
                    "type": "done",
                    "sources": sources,
                    "related_searches": related_searches,
                    "full_content": full_content,
                    "model_used": model_to_use
                }


perplexity_service = PerplexitySearchService()


# --- API Models ---

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
    session_id: Optional[str] = Field(None, description="Session ID")
    max_results: Optional[int] = Field(10)
    model_name: Optional[str] = Field(None)

class SearchResponse(BaseModel):
    results: List[SearchResult]
    reasoning: List[ReasoningStep] = []
    sources: List[Source] = []
    execution_time: float
    session_id: str
    image_results: Optional[List[Dict[str, Any]]] = []
    video_results: Optional[List[Dict[str, Any]]] = []
    enhanced_query: Optional[str] = None
    has_images: Optional[bool] = False
    has_videos: Optional[bool] = False
    related_searches: Optional[List[str]] = []


# --- API Endpoints ---

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Nexus AI Search Engine",
        "version": "4.0.0",
        "powered_by": "Perplexity API"
    }

@app.get("/health")
async def health_check():
    api_key_configured = bool(os.getenv("PERPLEXITY_API_KEY"))
    return {"status": "healthy" if api_key_configured else "unhealthy", "api_key_configured": api_key_configured}


@app.post("/api/search/stream")
async def search_stream(request: SearchRequest):
    """Streaming search endpoint using Server-Sent Events"""
    try:
        session_id = request.session_id or str(uuid4())
        conversation_history = sessions.get(session_id, [])
        model = request.model_name or "sonar"
        
        async def generate_stream():
            start_time = time.time()
            full_content = ""
            sources = []
            related_searches = []
            
            try:
                async for chunk in perplexity_service.search_stream(
                    query=request.query,
                    conversation_history=conversation_history,
                    model=model
                ):
                    if chunk["type"] == "content":
                        full_content += chunk["text"]
                        yield f"data: {json.dumps({'type': 'content', 'text': chunk['text']})}\n\n"
                    
                    elif chunk["type"] == "done":
                        sources = chunk.get("sources", [])
                        related_searches = chunk.get("related_searches", [])
                        
                        if session_id not in sessions:
                            sessions[session_id] = []
                        sessions[session_id].append({"role": "user", "content": request.query})
                        sessions[session_id].append({"role": "assistant", "content": full_content})
                        
                        if len(sessions[session_id]) > 20:
                            sessions[session_id] = sessions[session_id][-20:]
                        
                        execution_time = time.time() - start_time
                        
                        formatted_sources = [
                            {
                                "url": src.get("url", ""),
                                "link": src.get("url", ""),
                                "title": src.get("title", "Source"),
                                "snippet": src.get("snippet", ""),
                                "source": "perplexity"
                            }
                            for src in sources
                        ]
                        
                        final_data = {
                            "type": "done",
                            "session_id": session_id,
                            "execution_time": execution_time,
                            "sources": formatted_sources,
                            "related_searches": related_searches
                        }
                        yield f"data: {json.dumps(final_data)}\n\n"
                        
            except Exception as e:
                logger.error(f"Streaming error: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"Stream setup error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stream setup failed: {str(e)}")

@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    start_time = time.time()
    
    try:
        session_id = request.session_id or str(uuid4())
        conversation_history = sessions.get(session_id, [])
        model = request.model_name or "sonar"
        
        result = await perplexity_service.search(
            query=request.query,
            conversation_history=conversation_history,
            model=model
        )
        
        if session_id not in sessions:
            sessions[session_id] = []
        sessions[session_id].append({"role": "user", "content": request.query})
        sessions[session_id].append({"role": "assistant", "content": result["answer"]})
        
        if len(sessions[session_id]) > 20:
            sessions[session_id] = sessions[session_id][-20:]
        
        execution_time = time.time() - start_time
        
        sources = [
            Source(
                url=src.get("url", ""),
                link=src.get("url", ""),
                title=src.get("title", "Source"),
                snippet=src.get("snippet", ""),
                source="perplexity"
            )
            for src in result.get("sources", [])
        ]
        
        return SearchResponse(
            results=[SearchResult(content=result["answer"], type="text")],
            reasoning=[
                ReasoningStep(step=1, thought=f"Searching for: {request.query}"),
                ReasoningStep(step=2, thought=f"Found {len(sources)} sources"),
                ReasoningStep(step=3, thought="Generated answer with citations")
            ],
            sources=sources,
            execution_time=execution_time,
            session_id=session_id,
            related_searches=result.get("related_searches", [])
        )
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
        return {"status": "success", "message": f"Session {session_id} deleted"}
    raise HTTPException(status_code=404, detail="Session not found")
