"""
Advanced Search Module
Implements real AI search capabilities using OpenAI, Gemini, and other AI models with web search
"""
import os
import time
import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Literal
from dotenv import load_dotenv

 
load_dotenv()

# API keys f
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# Default model to use
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini").lower()

# Sso, i want ths to be kinda a memory cache
search_cache = {}

#yhea, this are the models we gonna b using, at least for now , xoxo
ModelType = Literal["openai", "gemini", "claude"]

async def get_aiohttp_session():
    """Get or create an aiohttp session"""
    if not hasattr(get_aiohttp_session, "session"):
        get_aiohttp_session.session = aiohttp.ClientSession()
    return get_aiohttp_session.session

async def close_aiohttp_session():
    """Close the aiohttp session if it exists"""
    if hasattr(get_aiohttp_session, "session"):
        await get_aiohttp_session.session.close()
        get_aiohttp_session.session = None

async def search_web(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search the web using DuckDuckGo
    """
    try:
        session = await get_aiohttp_session()
        
        # so we gonna use , duckduckgo api to do the searches, at least for now
        api_url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "no_redirect": 1,
            "skip_disambig": 1
        }
        
        async with session.get(api_url, params=params) as response:
            if response.status != 200:
                print(f"DuckDuckGo API returned status {response.status}")
                return []
            
            data = await response.json(content_type=None)
            
            results = []
            
            # Add the main "AbstractText" result if it exists
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", "DuckDuckGo Result"),
                    "link": data.get("AbstractURL", ""),
                    "snippet": data.get("AbstractText", ""),
                    "source": "duckduckgo"
                })
            
            # so, ting is, this will add kinda the related topics, yhea.....
            for topic in data.get("RelatedTopics", []):
                if "Text" in topic and "FirstURL" in topic:
                    results.append({
                        "title": topic.get("Text", "").split(" - ")[0] if " - " in topic.get("Text", "") else topic.get("Text", ""),
                        "link": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", ""),
                        "source": "duckduckgo"
                    })
            
            return results[:max_results]
            
    except Exception as e:
        print(f"Error in web search: {str(e)}")
        return []

async def search_wikipedia(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """
    Search Wikipedia for information
    """
    try:
        session = await get_aiohttp_session()
        
        # so, yhea, this will first find the first matching pages
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": max_results,
            "srwhat": "text"
        }
        
        async with session.get(search_url, params=search_params) as response:
            if response.status != 200:
                print(f"Wikipedia API returned status {response.status}")
                return []
            
            data = await response.json()
            
            search_results = data.get("query", {}).get("search", [])
            page_titles = [result["title"] for result in search_results]
        
        # so, here we gonna have to get the details for each page, yheaaa...
        results = []
        for title in page_titles:
            page_params = {
                "action": "query",
                "format": "json",
                "titles": title,
                "prop": "extracts|info",
                "exintro": 1,
                "explaintext": 1,
                "inprop": "url"
            }
            
            async with session.get(search_url, params=page_params) as response:
                if response.status != 200:
                    print(f"Wikipedia API returned status {response.status}")
                    continue
                
                data = await response.json()
                
                # so, yhea, this will extract page data
                pages = data.get("query", {}).get("pages", {})
                if not pages:
                    continue
                
                # so , here we will get the first and umm, kinda (the only oage)
                page_id = next(iter(pages))
                page_data = pages[page_id]
                
                # mmmm, here we will skip the pages that dont exist, u know homie
                if "missing" in page_data:
                    continue
                
                results.append({
                    "title": page_data.get("title", ""),
                    "link": page_data.get("fullurl", f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"),
                    "snippet": page_data.get("extract", "")[:500] + "...",
                    "source": "wikipedia"
                })
        
        return results
            
    except Exception as e:
        print(f"Error in Wikipedia search: {str(e)}")
        return []

async def search_serper(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search the web using Serper.dev API (Google Search API)
    """
    try:
        serper_api_key = os.getenv("SERPER_API_KEY")
        if not serper_api_key:
            print("Serper API key not found, skipping Serper search")
            return []
            
        session = await get_aiohttp_session()
        
        # Use the Serper API
        api_url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": serper_api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query,
            "gl": "us",
            "hl": "en",
            "num": max_results
        }
        
        async with session.post(api_url, headers=headers, json=payload) as response:
            if response.status != 200:
                print(f"Serper API returned status {response.status}")
                return []
            
            data = await response.json()
            
            results = []
            
            # Process organic results
            for item in data.get("organic", [])[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "google"
                })
            
            return results
            
    except Exception as e:
        print(f"Error in Serper search: {str(e)}")
        return []

def get_system_prompt() -> str:
    """Get the system prompt for AI synthesis"""
    return """
    You are an advanced AI research assistant. Your task is to:
    1. Analyze the search query and understand the underlying intent
    2. Examine search results from multiple sources
    3. Synthesize a comprehensive, detailed, accurate answer
    4. Provide proper attribution to sources
    5. Maintain factual accuracy and avoid fabricating information

    6. cite your sources
    
    Format your response as a JSON object with these keys:
    - answer: The synthesized answer to the query
    - confidence: Your confidence score (0-1) in the answer
    - reasoning: Your step-by-step reasoning process as a list of strings
    """

def format_sources_as_context(sources: List[Dict[str, Any]]) -> str:
    """Format sources as context for the AI in a structured way"""
    if not sources:
        return "No search results found."
    
    context = ""
    for i, source in enumerate(sources, 1):
        title = source.get("title", "Untitled")
        snippet = source.get("snippet", "")
        url = source.get("link", "")
        source_type = source.get("source", "web")
        
        context += f"[SOURCE {i}]\n"
        context += f"Title: {title}\n"
        context += f"URL: {url}\n"
        context += f"Type: {source_type}\n"
        context += f"Content: {snippet}\n\n"
    
    return context

async def synthesize_with_openai(query: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Use OpenAI to synthesize search results into a coherent response
    """
    try:
        if not OPENAI_API_KEY:
            return {
                "answer": "OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable.",
                "confidence": 0,
                "reasoning": ["OpenAI API key not available"]
            }
        
        session = await get_aiohttp_session()
        
        # so , yhea, we gonna have to format sources as context
        context = format_sources_as_context(sources)
        
        # yhea, this gonna be our system prompt fo our ai, u know, that init promp.. you know 
        system_prompt = """
        You are an advanced AI research assistant. Your task is to:
        1. Analyze the search query and understand the underlying intent
        2. Examine search results from multiple sources
        3. Synthesize a comprehensive, accurate answer
        4. Provide proper attribution to sources
        5. Maintain factual accuracy and avoid fabricating information
        
        Important: Provide your answer in a clean, well-formatted text that directly addresses the user's query.
        Do NOT output JSON format in your response. Just write the answer as a human-friendly paragraph.
        """
        
        # so, yhea, this will prepare messages for openai,  or... (for SCAM alt hahahaha (am a fan, btw))
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {query}\n\nSearch Results:\n{context}"}
        ]
        
        # haaa c'mon, this is straight, its  an api call for openai (scam altman)
        api_url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            "messages": messages,
            "temperature": 0.3
        }
        
        async with session.post(api_url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"OpenAI API error: {response.status} - {error_text}")
            
            result = await response.json()
            response_text = result["choices"][0]["message"]["content"]
            
            # pretty obvios , isn't it? will return in a kinda formatted structure
            return {
                "answer": response_text,
                "confidence": 0.9,
                "reasoning": ["Analyzed search results and synthesized an answer to the user query"]
            }
            
    except Exception as e:
        print(f"Error in OpenAI synthesis: {str(e)}")
        return {
            "answer": f"Error synthesizing results: {str(e)}",
            "confidence": 0,
            "reasoning": [f"Error: {str(e)}"]
        }

async def synthesize_with_gemini(query: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Use Google's Gemini model to synthesize search results
    """
    try:
        if not GEMINI_API_KEY:
            return {
                "answer": "Gemini API key not configured. Please set the GEMINI_API_KEY environment variable.",
                "confidence": 0,
                "reasoning": ["Gemini API key not available"]
            }
        
        session = await get_aiohttp_session()
        
        # Format sources as context
        context = format_sources_as_context(sources)
        
        # Construct the prompt for Gemini with citation requirements
        prompt = f"""
        You are an advanced AI research assistant synthesizing information from search results.

        Please provide a comprehensive, accurate answer to the query below.
        
        IMPORTANT INSTRUCTIONS:
        2. Organize your answer into structure you see is the best for the case
        3. Be informative but conversational in tone
        4. DO NOT include phrases like "According to the search results" or "Based on the provided sources"
        5. DO NOT introduce yourself or explain your process
        6. You can decide if the query requires a detailed answer or not. you can give in detail or not (you decide whats the best)
        
        
        QUERY: {query}
        
        SOURCES:
        {context}
        """
        
        # API call to Gemini
        api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-exp-03-25:generateContent"
        params = {
            "key": GEMINI_API_KEY
        }
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "topP": 0.8,
                "topK": 40
            }
        }
        
        async with session.post(api_url, params=params, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Gemini API error: {response.status} - {error_text}")
            
            result = await response.json()
            
            # Extract text from response
            try:
                response_text = result["candidates"][0]["content"]["parts"][0]["text"]
                
                # We're not expecting JSON anymore, just return a formatted structure
                return {
                    "answer": response_text,
                    "confidence": 0.9,
                    "reasoning": ["Analyzed search results and synthesized an answer to the user query"]
                }
            except (KeyError, IndexError) as e:
                raise Exception(f"Error parsing Gemini response: {str(e)}")
            
    except Exception as e:
        print(f"Error in Gemini synthesis: {str(e)}")
        return {
            "answer": f"Error synthesizing results with Gemini: {str(e)}",
            "confidence": 0,
            "reasoning": [f"Error: {str(e)}"]
        }

async def synthesize_with_claude(query: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Use Anthropic's Claude model to synthesize search results
    """
    try:
        if not CLAUDE_API_KEY:
            return {
                "answer": "Claude API key not configured. Please set the CLAUDE_API_KEY environment variable.",
                "confidence": 0,
                "reasoning": ["Claude API key not available"]
            }
        
        session = await get_aiohttp_session()
        
        # Format sources as context
        context = format_sources_as_context(sources)
        
        # Prepare the messages for Claude
        system_prompt = """
        You are an advanced AI research assistant. Your task is to:
        1. Analyze the search query and understand the underlying intent
        2. Examine search results from multiple sources
        3. Synthesize a comprehensive, accurate answer
        4. Provide proper attribution to sources
        5. Maintain factual accuracy and avoid fabricating information
        
        Important: Provide your answer in a clean, well-formatted text that directly addresses the user's query.
        Do NOT output JSON format in your response. Just write the answer as a human-friendly paragraph.
        """
        
        user_prompt = f"Query: {query}\n\nSearch Results:\n{context}"
        
        # API call to Claude (Anthropic)
        api_url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": os.getenv("CLAUDE_MODEL", "claude-2"),
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        async with session.post(api_url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Claude API error: {response.status} - {error_text}")
            
            result = await response.json()
            response_text = result.get("content", [{"text": "No response"}])[0].get("text", "No response")
            
            # Return a formatted structure
            return {
                "answer": response_text,
                "confidence": 0.9,
                "reasoning": ["Analyzed search results and synthesized an answer to the user query"]
            }
            
    except Exception as e:
        print(f"Error in Claude synthesis: {str(e)}")
        return {
            "answer": f"Error synthesizing results with Claude: {str(e)}",
            "confidence": 0,
            "reasoning": [f"Error: {str(e)}"]
        }

async def synthesize_with_ai(query: str, sources: List[Dict[str, Any]], model_type: ModelType = None) -> Dict[str, Any]:
    """
    Synthesize search results using the specified AI model
    
    Args:
        query: The search query
        sources: The search results to synthesize
        model_type: Type of model to use (openai, gemini, claude)
        
    Returns:
        Synthesized results dictionary
    """
    # If no model specified, use the default
    if model_type is None:
        model_type = DEFAULT_MODEL
    
    # Choose the appropriate synthesis function based on model_type
    if model_type == "openai":
        return await synthesize_with_openai(query, sources)
    elif model_type == "gemini":
        return await synthesize_with_gemini(query, sources)
    elif model_type == "claude":
        return await synthesize_with_claude(query, sources)
    else:
        # Fallback to OpenAI if model_type is not recognized
        print(f"Unknown model type: {model_type}. Falling back to default.")
        if DEFAULT_MODEL == "gemini":
            return await synthesize_with_gemini(query, sources)
        elif DEFAULT_MODEL == "claude":
            return await synthesize_with_claude(query, sources)
        else:
            return await synthesize_with_openai(query, sources)

async def perform_advanced_search(
    query: str, 
    max_results: int = 10,
    model_type: ModelType = None
) -> Dict[str, Any]:
    """
    Perform an advanced search with AI synthesis
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        model_type: Type of model to use for synthesis (openai, gemini, claude)
        
    Returns:
        Search results with AI synthesis
    """
    try:
        # If no model specified, use the default
        if model_type is None:
            model_type = DEFAULT_MODEL
        
        # Check cache first
        cache_key = f"{query}:{max_results}:{model_type}"
        if cache_key in search_cache:
            print(f"Cache hit for query: {query}")
            return search_cache[cache_key]
        
        start_time = time.time()
        
        # Get results from multiple sources in parallel
        serper_results_task = search_serper(query, max_results=max_results)
        duckduckgo_results_task = search_web(query, max_results=max_results)
        wiki_results_task = search_wikipedia(query, max_results=max_results // 2)
        
        serper_results, duckduckgo_results, wiki_results = await asyncio.gather(
            serper_results_task, 
            duckduckgo_results_task, 
            wiki_results_task
        )
        
        # Combine results from different sources, prioritizing Serper results
        all_sources = []
        
        # First add Serper (Google) results
        all_sources.extend(serper_results)
        
        # Then add DuckDuckGo and Wikipedia, but avoid duplicates
        seen_urls = set(source["link"] for source in all_sources)
        
        for result_set in [duckduckgo_results, wiki_results]:
            for source in result_set:
                if source["link"] not in seen_urls:
                    seen_urls.add(source["link"])
                    all_sources.append(source)
        
        # Limit to max_results
        all_sources = all_sources[:max_results]
        
        # If we found sources, synthesize them with AI
        if all_sources:
            synthesis = await synthesize_with_ai(query, all_sources, model_type)
            
            # Format final response
            response = {
                "results": [{
                    "content": synthesis.get("answer", "No results found"),
                    "type": "text"
                }],
                "reasoning": [],
                "sources": all_sources,
                "execution_time": time.time() - start_time,
                "model_used": model_type
            }
            
            # Format reasoning steps
            reasoning_raw = synthesis.get("reasoning", ["Performed search and analysis"])
            if isinstance(reasoning_raw, str):
                reasoning_raw = [reasoning_raw]
            
            for i, step in enumerate(reasoning_raw, 1):
                response["reasoning"].append({
                    "step": i,
                    "thought": step
                })
            
            # Cache the result
            search_cache[cache_key] = response
            
            return response
        else:
            # No results found
            return {
                "results": [{
                    "content": f"No results found for query: '{query}'",
                    "type": "text"
                }],
                "reasoning": [{
                    "step": 1,
                    "thought": f"Searched for information about '{query}' but found no relevant results"
                }],
                "sources": [],
                "execution_time": time.time() - start_time,
                "model_used": model_type
            }
            
    except Exception as e:
        print(f"Error in advanced search: {str(e)}")
        return {
            "results": [{
                "content": f"An error occurred while searching: {str(e)}",
                "type": "text"
            }],
            "reasoning": [{
                "step": 1,
                "thought": f"Error during search: {str(e)}"
            }],
            "sources": [],
            "execution_time": time.time() - start_time,
            "model_used": model_type
        } 