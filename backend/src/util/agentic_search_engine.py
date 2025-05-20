"""
Advanced Agentic Search Engine

This module implements a highly autonomous search agent that can:
1. Conduct multiple searches iteratively
2. Reason about the results and determine next steps
3. Synthesize information from multiple sources
4. Generate a comprehensive report

It follows a researcher-like approach, continuously refining its understanding
of the topic through multiple search iterations.
"""

import asyncio
import time
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
import logging
import os
import re

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.schema import AIMessage, HumanMessage, SystemMessage

from ..util.search_tools import SearchTool, SerperSearchTool, DuckDuckGoSearchTool, WikipediaSearchTool
from ..util.parallel_search import ParallelSearchExecutor, SearchPriority
from ..util.logger import setup_logger

logger = setup_logger(__name__)

class ResearchStep:
    """Represents a single step in the research process"""
    
    def __init__(self, query: str, reasoning: str):
        self.id = str(uuid.uuid4())
        self.query = query
        self.reasoning = reasoning
        self.results = []
        self.sources = []  # Add sources field to store references
        self.timestamp = datetime.now()
        self.execution_time = 0
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "query": self.query,
            "reasoning": self.reasoning,
            "results_count": len(self.results),
            "sources_count": len(self.sources),  # Add source count
            "timestamp": self.timestamp.isoformat(),
            "execution_time": self.execution_time
        }

class ResearchPlan:
    """Represents the overall research plan with steps and synthesis"""
    
    def __init__(self, original_query: str):
        self.id = str(uuid.uuid4())
        self.original_query = original_query
        self.steps: List[ResearchStep] = []
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.synthesis = ""
        self.final_answer = ""
        self.status = "initiated"  # initiated, in_progress, completed
        
    def add_step(self, step: ResearchStep):
        """Add a research step"""
        self.steps.append(step)
        self.updated_at = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "original_query": self.original_query,
            "steps": [step.to_dict() for step in self.steps],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "synthesis": self.synthesis,
            "final_answer": self.final_answer,
            "status": self.status,
            "sources": self.get_all_sources()  # Include all sources
        }
        
    def get_all_sources(self) -> List[Dict[str, Any]]:
        """Get all unique sources from all steps"""
        all_sources = []
        seen_urls = set()
        
        for step in self.steps:
            for source in step.sources:
                source_url = source.get("url", "")
                if source_url and source_url not in seen_urls:
                    seen_urls.add(source_url)
                    all_sources.append(source)
        
        return all_sources

class AgenticSearchEngine:
    """
    Advanced agentic search engine that conducts iterative research like a human researcher.
    """
    
    def __init__(self, 
                model_name: str = "gemini-2.5-flash-preview-04-17", 
                model_provider: str = "google",
                max_iterations: int = 5,
                verbose: bool = False):
        """
        Initialize the agentic search engine.
        
        Args:
            model_name: The LLM model to use for research planning and synthesis
            model_provider: Which model provider to use: "openai", "google", or "anthropic"
            max_iterations: Maximum number of research iterations
            verbose: Whether to log detailed information
        """
        self.model_name = model_name
        self.model_provider = model_provider.lower()
        self.max_iterations = max_iterations
        self.verbose = verbose
        
        # Initialize LLM for reasoning and synthesis
        self.llm = self._initialize_llm()
        
        # Initialize search tools
        self.search_executor = ParallelSearchExecutor()
        self._setup_search_tools()
        
        # Track active research plans
        self.active_plans = {}
    
    def _initialize_llm(self):
        """Initialize the appropriate LLM based on provider"""
        # Force using Google Gemini regardless of provider setting
        # This is temporary until we fix the environment variables
        try:
            # For debugging only - add a default API key
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                logger.warning("No GOOGLE_API_KEY found in environment variables")
                # IMPORTANT: DO NOT COMMIT YOUR ACTUAL KEY - THIS IS JUST FOR TESTING
                google_api_key = "AIzaSyDummyKeyForTestingPurposesOnly"
                
            logger.info(f"Initializing Google Gemini LLM: {self.model_name}")
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-preview-04-17",
                temperature=0.1,
                google_api_key=google_api_key
            )
        except Exception as e:
            logger.error(f"Error initializing Google Gemini: {str(e)}")
            # As a fallback, use OpenAI if Google fails
            logger.warning(f"Falling back to OpenAI")
            return ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.1,
                api_key=os.getenv("OPENAI_API_KEY")
            )
    
    def _setup_search_tools(self):
        """Set up search tools with appropriate priorities"""
        # Main search tools
        serper_search = SerperSearchTool()
        duck_search = DuckDuckGoSearchTool()
        wiki_search = WikipediaSearchTool()
        
        # Register with the parallel executor
        self.search_executor.register_tool(
            tool=serper_search, 
            priority=SearchPriority.HIGH,
            timeout=10.0,
            max_results=10,
            weight=1.0
        )
        
        self.search_executor.register_tool(
            tool=duck_search, 
            priority=SearchPriority.MEDIUM,
            timeout=10.0,
            max_results=10,
            weight=0.8
        )
        
        self.search_executor.register_tool(
            tool=wiki_search, 
            priority=SearchPriority.MEDIUM,
            timeout=10.0,
            max_results=5,
            weight=0.9
        )
    
    async def _execute_search(self, query: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Execute search and return results and sources"""
        response = await self.search_executor.execute_prioritized_search(query)
        results = response.get("results", [])
        
        # Process sources to match format expected by frontend
        sources = []
        for source in response.get("results", []):
            if "url" in source and "title" in source:
                sources.append({
                    "title": source.get("title", "No title"),
                    "url": source.get("url", ""),
                    "snippet": source.get("snippet", source.get("content", "")),
                    "source": source.get("source", "web search"),
                    "isRelevant": True
                })
        
        return results, sources
    
    async def _plan_initial_research(self, query: str, conversation_context: Optional[str] = None) -> Dict[str, Any]:
        """Plan the initial research approach based on the query"""
        
        context_prompt_addition = ""
        if conversation_context:
            context_prompt_addition = f"""
Conversation Context:
---
{conversation_context}
---
Considering the conversation context, for the given query for this step, identify:
"""
        else:
            context_prompt_addition = "For the given query, identify:"

        system_message_content = f"""
You are an expert research assistant planning a comprehensive research strategy.
{(
    "You have access to the ongoing conversation history. Use this context to inform your plan." 
    if conversation_context 
    else ""
)}
{context_prompt_addition}
1. 3-5 specific search queries that would gather different aspects of the information needed
2. The reasoning behind each query
3. The order in which these queries should be performed
4. Any potential challenges or limitations to be aware of

Respond with a JSON object containing:
{{
    "initial_queries": [
        {{"query": "specific search query 1", "reasoning": "why this query helps answer the original question"}},
        {{"query": "specific search query 2", "reasoning": "why this query helps answer the original question"}},
        ...
    ],
    "research_approach": "short description of the overall research approach",
    "potential_challenges": "description of potential challenges"
}}
"""
        system_message = SystemMessage(content=system_message_content)
        
        human_message_content = f"Original query for this step: {query}"
        if conversation_context: # Prepend context to human message if not in system (alternative)
             pass # Already handled in system_message_content construction

        human_message = HumanMessage(content=human_message_content)
        
        messages = [system_message, human_message]
        response = await self.llm.ainvoke(messages)
        
        try:
            plan_dict = json.loads(response.content)
            return plan_dict
        except json.JSONDecodeError:
            # Handle case where LLM didn't return valid JSON
            logger.error(f"LLM didn't return valid JSON for research planning. Response: {response.content}")
            # Create a fallback plan with a single query
            return {
                "initial_queries": [
                    {"query": query, "reasoning": "Direct search for the original query"}
                ],
                "research_approach": "Direct search for the original query",
                "potential_challenges": "May not capture all aspects of the question"
            }
    
    async def _analyze_results_and_plan_next(self, 
                                           plan: ResearchPlan, 
                                           current_results: List[Dict[str, Any]],
                                           conversation_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze search results and plan the next research steps.
        """
        steps_context = ""
        for i, step in enumerate(plan.steps):
            steps_context += f"Step {i+1}: Query: '{step.query}'\nReasoning: {step.reasoning}\n"
            if step.results:
                steps_context += f"Found {len(step.results)} results\n\n"
        
        # Format current results for context
        results_context = "Current search results:\n"
        for i, result in enumerate(current_results[:5]):  # Limit to avoid token overflow
            results_context += f"[{i+1}] {result.get('title', 'No title')}\n"
            results_context += f"URL: {result.get('url', 'No URL')}\n"
            results_context += f"Summary: {result.get('snippet', 'No summary')[:200]}...\n\n"
        
        context_prompt_addition = ""
        human_message_context_section = ""
        if conversation_context:
            context_prompt_addition = "You have access to the ongoing conversation history. Use this context to inform your analysis and planning."
            human_message_context_section = f"""
Conversation Context:
---
{conversation_context}
---
"""

        system_message_content = f"""
You are an expert research assistant analyzing search results and planning next steps.
{context_prompt_addition}
Based on the original query for the overall research, conversation context (if provided), the research steps taken so far, and the current results, 
determine what additional information is needed and what the next search queries should be.

Analyze gaps in knowledge, evaluate the quality and relevance of current results, 
and identify new angles to explore.

If sufficient information has been gathered, indicate that the research can be concluded.

IMPORTANT: Your response must be a valid JSON object. Do not include any markdown formatting or code blocks.
Do not wrap your JSON in ```json or ``` tags. Return ONLY the raw JSON object.

Respond with a JSON object containing:
{{
    "analysis": "deep analysis of current results and information gaps",
    "information_sufficient": true/false,
    "next_queries": [
        {{"query": "specific search query", "reasoning": "why this query is needed"}},
        ...
    ],
    "topics_to_synthesize": ["topic1", "topic2", ...],
    "recommendation": "overall recommendation for next steps"
}}
"""
        system_message = SystemMessage(content=system_message_content)
        
        human_message_content = f"""
{human_message_context_section}
Original query for the overall research: {plan.original_query}

Research steps so far:
{steps_context}

{results_context}

What are the next steps for this research, keeping the conversation context (if provided) in mind?
"""
        human_message = HumanMessage(content=human_message_content)
        
        messages = [system_message, human_message]
        response = await self.llm.ainvoke(messages)
        
        try:
            # Extract JSON content if wrapped in markdown code blocks
            content = response.content.strip()
            
            # Check if JSON is wrapped in code blocks and extract it
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            # Handle any trailing commas in JSON objects or arrays which cause parsing errors
            import re
            content = re.sub(r',\s*}', '}', content)
            content = re.sub(r',\s*\]', ']', content)
            
            # Fix any missing closing brackets/braces
            open_braces = content.count('{')
            close_braces = content.count('}')
            if open_braces > close_braces:
                content += '}' * (open_braces - close_braces)
                
            open_brackets = content.count('[')
            close_brackets = content.count(']')
            if open_brackets > close_brackets:
                content += ']' * (open_brackets - close_brackets)
            
            # Now parse the cleaned JSON
            analysis_dict = json.loads(content)
            logger.info(f"Successfully parsed analysis JSON response")
            return analysis_dict
        except json.JSONDecodeError as e:
            # Log the specific JSON error and content that failed parsing
            logger.error(f"LLM didn't return valid JSON for result analysis. Error: {str(e)}, Response: {response.content[:200]}...")
            # Create a fallback analysis
            return {
                "analysis": "Unable to parse results properly. Continuing with default approach.",
                "information_sufficient": len(plan.steps) >= self.max_iterations,
                "next_queries": [
                    {"query": f"{plan.original_query} {len(plan.steps) + 1}th perspective", 
                     "reasoning": f"Exploring another angle on the topic for iteration {len(plan.steps) + 1}"}
                ],
                "topics_to_synthesize": [plan.original_query],
                "recommendation": "Continue with research from a different perspective"
            }
    
    async def _synthesize_research(self, plan: ResearchPlan, conversation_context: Optional[str] = None) -> str:
        """
        Synthesize all research results into a comprehensive answer.
        """
        # Prepare context from all steps and results
        all_results = []
        steps_context = ""
        
        for i, step in enumerate(plan.steps):
            steps_context += f"Step {i+1}: Query: '{step.query}'\nReasoning: {step.reasoning}\n\n"
            all_results.extend(step.results)
        
        # Prepare results context (limit to avoid token overflow)
        results_context = "Information gathered from searches:\n\n"
        unique_sources = []
        seen_urls = set()
        
        for i, result in enumerate(all_results[:20]):  # Limit to 20 most relevant results
            title = result.get('title', 'No title')
            url = result.get('url', 'No URL')
            content = result.get('snippet', result.get('content', 'No content'))
            
            # Avoid duplicate sources
            if url in seen_urls:
                continue
                
            seen_urls.add(url)
            # Track source with index for citations
            unique_sources.append({
                "index": len(unique_sources) + 1,
                "title": title,
                "url": url,
                "content": content
            })
            results_context += f"[Source {len(unique_sources)}] {title}\nURL: {url}\n\n"
            results_context += f"{content[:300]}...\n\n"
        
        context_prompt_addition = ""
        human_message_context_section = ""
        if conversation_context:
            context_prompt_addition = "You have access to the ongoing conversation history. Use this context to ensure your synthesis is relevant to the entire discussion."
            human_message_context_section = f"""
Conversation Context:
---
{conversation_context}
---
"""

        system_message_content = f"""
You are an expert researcher synthesizing information into a comprehensive report.
{context_prompt_addition}
Based on the original query for this research task, conversation context (if provided), and all the information gathered through multiple searches,
create a detailed, accurate, and well-structured report that thoroughly answers the query.

Your report should:
1. Be comprehensive and cover all important aspects of the topic
2. Synthesize information from multiple sources into a coherent whole
3. Clearly cite sources when presenting specific facts or claims using citation format [1], [2], etc.
4. Acknowledge limitations or areas of uncertainty
5. Present a balanced view that considers multiple perspectives
6. Be well-organized with logical sections and flow

When including facts or data from a specific source, cite it using numbered citation format [1], [2], etc.
The source numbers correspond to the source indices provided in the information section.

Format your response as a comprehensive research report with sections,
not just a simple answer.
"""
        system_message = SystemMessage(content=system_message_content)
        
        human_message_content = f"""
{human_message_context_section}
Original query for this research task: {plan.original_query}

Research process for this task:
{steps_context}

{results_context}

Available sources for citation (use these numbers when citing):
{', '.join([f"[{s['index']}] {s['title']}" for s in unique_sources])}

Please synthesize all this information into a comprehensive report that thoroughly answers the original query for this task,
using appropriate citations [1], [2], etc. when referencing specific information from sources.
Take into account the full conversation context (if provided).
"""
        human_message = HumanMessage(content=human_message_content)
         
        messages = [system_message, human_message]
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_related_searches(self, query: str, synthesis: str, max_suggestions: int = 5) -> List[str]:
        """
        Generate related search suggestions based on the original query and research synthesis.
        This is similar to the method in SearchAgent but adapted for AgenticSearchEngine.
        """
        try:
            # Create a focused prompt for related searches based on synthesis
            prompt = f"""
            Based on the user's original research query: "{query}" and the following synthesized research report:
            ---
            {synthesis[:2000]} # Limit synthesis length to avoid overly long prompts
            ---

            Generate {max_suggestions} SPECIFIC and DIVERSE related search queries that a user might find helpful to explore next.
            These queries should branch out from the main findings or explore related facets not fully covered in the report.
            Avoid generic follow-ups like "more about {query}". Each query should be unique and insightful.

            IMPORTANT: Format your response as a JSON array of strings containing ONLY the related search queries.
            No explanations or additional text.

            For example:
            ["specific related query 1 based on synthesis", "another distinct query", "a third exploration path"]
            """

            logger.info(f"Generating related searches for agentic query: '{query}'")
            response = await self.llm.ainvoke(prompt)
            result_text = response.content.strip()
            logger.info(f"Raw LLM response for agentic related searches: {result_text[:200]}...")

            # Attempt to parse the entire response as JSON
            try:
                clean_text = result_text
                if "```json" in result_text:
                    clean_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text: # Handle cases with just ```
                    parts = result_text.split("```")
                    if len(parts) > 1:
                        clean_text = parts[1].strip()
                    else: # No closing ```, try to find JSON start
                        json_start_index = result_text.find("[")
                        if json_start_index != -1:
                            clean_text = result_text[json_start_index:]


                related_queries = json.loads(clean_text)
                if isinstance(related_queries, list) and all(isinstance(q, str) for q in related_queries):
                    logger.info(f"Successfully parsed JSON for agentic related searches: {related_queries}")
                    return related_queries[:max_suggestions]
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed for agentic related searches: {str(e)}. Attempting line-by-line extraction.")

            # Fallback: Line-by-line extraction (similar to SearchAgent)
            fallback_queries = []
            lines = result_text.split('\\n') # Use escaped newline for splitting, as LLM might use it
            if len(lines) == 1 and "\n" in result_text: # If escaped didn't work, try literal newline
                lines = result_text.split('\n')

            for line in lines:
                line = line.strip()
                if not line or line in ['[', ']', '{', '}', ','] or line.startswith('//') or line.startswith('#'):
                    continue
                
                cleaned_line = re.sub(r'^\\d+[\.\)]\\s*', '', line.strip('"\'').rstrip(',')) # Remove numbering, quotes, commas
                if cleaned_line and len(cleaned_line) > 3 and not cleaned_line.lower().startswith(("here", "example", "sure", "based on")):
                    fallback_queries.append(cleaned_line)
                    if len(fallback_queries) >= max_suggestions:
                        break
            
            if fallback_queries:
                logger.info(f"Extracted {len(fallback_queries)} agentic related searches using line-by-line method.")
                return fallback_queries[:max_suggestions]

            logger.warning(f"Could not extract structured related searches for agentic query: '{query}'. Returning empty list.")
            return []

        except Exception as e:
            logger.error(f"Error generating agentic related searches for query '{query}': {str(e)}")
            # Fallback to very generic suggestions if all else fails
            return [
                f"Explore deeper aspects of {query}",
                f"Follow-up questions for {query} research",
                f"Related topics to {query} synthesis"
            ][:max_suggestions]
    
    async def execute_research(self, 
                             query: str, 
                             plan_id: Optional[str] = None,
                             session_id: Optional[str] = None,
                             conversation_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a full research process for the given query.
        
        Args:
            query: The research query
            plan_id: Optional ID of an existing research plan to continue
            session_id: Optional session ID
            conversation_context: Optional conversation context
            
        Returns:
            Dictionary with research results
        """
        # Create or retrieve research plan
        if plan_id and plan_id in self.active_plans:
            plan = self.active_plans[plan_id]
            logger.info(f"Continuing research plan {plan_id} for query: {query}")
        else:
            plan = ResearchPlan(original_query=query)
            plan_id = plan.id
            self.active_plans[plan_id] = plan
            logger.info(f"Created new research plan {plan_id} for query: {query}")
        
        try:
            # Update plan status
            plan.status = "in_progress"
            
            # If this is a new plan, create initial research strategy
            if not plan.steps:
                initial_plan = await self._plan_initial_research(query, conversation_context)
                
                # Execute the first planned query
                if initial_plan and "initial_queries" in initial_plan and initial_plan["initial_queries"]:
                    first_query_info = initial_plan["initial_queries"][0]
                    first_query = first_query_info["query"]
                    first_reasoning = first_query_info["reasoning"]
                    
                    # Create and execute first step
                    first_step = ResearchStep(query=first_query, reasoning=first_reasoning)
                    start_time = time.time()
                    results, sources = await self._execute_search(first_query)
                    first_step.execution_time = time.time() - start_time
                    first_step.results = results
                    first_step.sources = sources  # Save sources
                    
                    # Add to plan
                    plan.add_step(first_step)
                    
                    # Also store additional planned queries for later steps
                    plan.planned_queries = initial_plan["initial_queries"][1:]
                else:
                    # Fallback if planning failed
                    first_step = ResearchStep(
                        query=query, 
                        reasoning="Initial direct search for the original query"
                    )
                    start_time = time.time()
                    results, sources = await self._execute_search(query)
                    first_step.execution_time = time.time() - start_time
                    first_step.results = results
                    first_step.sources = sources  # Save sources
                    
                    # Add to plan
                    plan.add_step(first_step)
                    plan.planned_queries = []
            
            # Continue research with additional iterations until sufficient or max_iterations
            iteration = len(plan.steps)
            while iteration < self.max_iterations:
                # Get the latest search results
                latest_step = plan.steps[-1]
                latest_results = latest_step.results
                
                # Analyze results and determine next steps
                analysis = await self._analyze_results_and_plan_next(plan, latest_results, conversation_context)
                
                # Check if we have sufficient information
                if analysis.get("information_sufficient", False):
                    logger.info(f"Research complete for plan {plan_id} after {iteration} iterations")
                    break
                
                # Get next query from analysis
                next_queries = analysis.get("next_queries", [])
                if not next_queries:
                    # Try to use a previously planned query if available
                    if hasattr(plan, "planned_queries") and plan.planned_queries:
                        next_query_info = plan.planned_queries.pop(0)
                        next_query = next_query_info["query"]
                        next_reasoning = next_query_info["reasoning"]
                    else:
                        # Fallback
                        next_query = f"{query} additional details"
                        next_reasoning = "Gathering more specific information"
                else:
                    next_query_info = next_queries[0]
                    next_query = next_query_info["query"]
                    next_reasoning = next_query_info["reasoning"]
                    
                    # Save additional planned queries
                    plan.planned_queries = next_queries[1:] if len(next_queries) > 1 else []
                
                # Execute the next step
                next_step = ResearchStep(query=next_query, reasoning=next_reasoning)
                start_time = time.time()
                results, sources = await self._execute_search(next_query)
                next_step.execution_time = time.time() - start_time
                next_step.results = results
                next_step.sources = sources  # Save sources
                
                # Add to plan
                plan.add_step(next_step)
                
                # Increment iteration counter
                iteration += 1
                
                # Log progress
                logger.info(f"Completed research iteration {iteration} for plan {plan_id}")
            
            # Synthesize final results
            plan.synthesis = await self._synthesize_research(plan, conversation_context)
            plan.status = "completed"
            
            # Generate related searches based on the synthesis
            related_searches = await self._generate_related_searches(plan.original_query, plan.synthesis)
            logger.info(f"Generated related searches for plan {plan_id}: {related_searches}")

            # Get all sources from the plan
            all_sources = plan.get_all_sources()
            
            # Create response
            response = {
                "plan_id": plan.id,
                "original_query": plan.original_query,
                "research_steps": [step.to_dict() for step in plan.steps],
                "synthesis": plan.synthesis,
                "status": plan.status,
                "iterations_completed": len(plan.steps),
                "max_iterations": self.max_iterations,
                "sources": all_sources,  # Include all sources using our method
                "related_searches": related_searches # Add related searches to the response
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error in agentic search: {str(e)}")
            
            # Update plan status
            plan.status = "error"
            
            # Create error response
            return {
                "plan_id": plan.id,
                "original_query": plan.original_query,
                "research_steps": [step.to_dict() for step in plan.steps],
                "synthesis": "An error occurred during the research process.",
                "status": "error",
                "error": str(e),
                "iterations_completed": len(plan.steps),
                "max_iterations": self.max_iterations,
                "sources": plan.get_all_sources(),  # Include any sources we did gather
                "related_searches": [] # Empty list for errors
            }
    
    async def get_research_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status and results of a research plan"""
        if plan_id in self.active_plans:
            plan = self.active_plans[plan_id]
            return plan.to_dict()
        return None
    
    async def close(self):
        """Close all resources"""
        await self.search_executor.close()