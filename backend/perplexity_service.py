"""
Perplexity Search Service
Handles all interactions with the Perplexity API
"""
import os
import httpx
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class PerplexitySearchService:
    """
    Service for interacting with Perplexity API.
    Uses the Chat Completions endpoint with Sonar models for grounded search.
    """
    
    BASE_URL = "https://api.perplexity.ai"
    
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.default_model = os.getenv("PERPLEXITY_MODEL", "sonar")
        
        if not self.api_key:
            logger.warning("PERPLEXITY_API_KEY not set. API calls will fail.")
    
    async def search(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a search using Perplexity's Sonar API.
        
        Args:
            query: The search query
            conversation_history: Previous messages for context
            model: Perplexity model to use (sonar, sonar-pro, sonar-reasoning-pro)
            
        Returns:
            Dictionary containing:
            - answer: The AI-generated response
            - sources: List of source citations
            - model_used: The model that was used
            - related_searches: Suggested follow-up queries
        """
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY is not configured")
        
        model_to_use = model or self.default_model
        
        # Build messages array
        messages = []
        
        # Add system message for search context
        messages.append({
            "role": "system",
            "content": (
                "You are a helpful AI search assistant called Nexus. "
                "Provide comprehensive, accurate answers based on current web information. "
                "Always cite your sources with numbered references like [1], [2], etc. "
                "Be conversational but informative. "
                "If asked follow-up questions, use the conversation context appropriately."
            )
        })
        
        # Add conversation history for context
        if conversation_history:
            # Only include the last few messages to stay within context limits
            recent_history = conversation_history[-10:]
            messages.extend(recent_history)
        
        # Add the current query
        messages.append({
            "role": "user",
            "content": query
        })
        
        # Make API request
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
            try:
                logger.info(f"Calling Perplexity API with model: {model_to_use}")
                
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Extract the answer
                answer = ""
                if data.get("choices") and len(data["choices"]) > 0:
                    answer = data["choices"][0].get("message", {}).get("content", "")
                
                # Extract sources/citations
                sources = []
                citations = data.get("citations", [])
                
                for i, citation in enumerate(citations):
                    if isinstance(citation, str):
                        # Simple URL citation
                        sources.append({
                            "index": i + 1,
                            "url": citation,
                            "title": f"Source {i + 1}"
                        })
                    elif isinstance(citation, dict):
                        # Detailed citation object
                        sources.append({
                            "index": i + 1,
                            "url": citation.get("url", ""),
                            "title": citation.get("title", f"Source {i + 1}"),
                            "snippet": citation.get("snippet", ""),
                            "date": citation.get("date", "")
                        })
                
                # Extract related questions if available
                related_searches = data.get("related_questions", [])
                
                # Also check search_results for additional source info
                search_results = data.get("search_results", [])
                if search_results and not sources:
                    for i, result in enumerate(search_results):
                        sources.append({
                            "index": i + 1,
                            "url": result.get("url", ""),
                            "title": result.get("title", f"Source {i + 1}"),
                            "snippet": result.get("snippet", ""),
                            "date": result.get("date", "")
                        })
                
                logger.info(f"Perplexity search successful. Sources: {len(sources)}")
                
                return {
                    "answer": answer,
                    "sources": sources,
                    "model_used": model_to_use,
                    "related_searches": related_searches,
                    "usage": data.get("usage", {})
                }
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Perplexity API HTTP error: {e.response.status_code} - {e.response.text}")
                raise ValueError(f"Perplexity API error: {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"Perplexity API request error: {str(e)}")
                raise ValueError(f"Failed to connect to Perplexity API: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error calling Perplexity API: {str(e)}")
                raise


class PerplexityRawSearchService:
    """
    Service for raw web search using Perplexity Search API.
    Returns ranked search results without AI synthesis.
    """
    
    BASE_URL = "https://api.perplexity.ai"
    
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        
        if not self.api_key:
            logger.warning("PERPLEXITY_API_KEY not set. API calls will fail.")
    
    async def search(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Execute a raw web search using Perplexity Search API.
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, url, snippet, date
        """
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY is not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "max_results": max_results
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/search",
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                results = []
                for result in data.get("results", []):
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": result.get("snippet", ""),
                        "date": result.get("date", "")
                    })
                
                return results
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Perplexity Search API error: {e.response.status_code}")
                raise ValueError(f"Perplexity Search API error: {e.response.status_code}")
            except Exception as e:
                logger.error(f"Error calling Perplexity Search API: {str(e)}")
                raise
