"""
Parallel Search Execution Module with Prioritization

This module provides functionality to execute multiple search tools in parallel
with prioritization, timeout control, and fallback mechanisms.
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Tuple, Callable, Union, TypeVar
from enum import Enum
from dataclasses import dataclass, field

from .search_tools import SearchTool
from .logger import setup_logger

logger = setup_logger(__name__)

# Type definition for search results
SearchResults = List[Dict[str, Any]]
T = TypeVar('T')  # Generic type for prioritized results

class SearchPriority(Enum):
    """Priority levels for search tools"""
    CRITICAL = 0    # Must have results from this source
    HIGH = 1        # Preferred source, try first
    MEDIUM = 2      # Standard priority
    LOW = 3         # Use only if higher priority sources fail or are slow
    FALLBACK = 4    # Last resort sources

@dataclass
class SearchToolConfig:
    """Configuration for a search tool with priority settings"""
    tool: SearchTool
    priority: SearchPriority
    timeout: float  # Timeout in seconds
    max_results: int
    weight: float = 1.0  # Result quality/reliability weight (0.0-1.0)
    enabled: bool = True
    
    # Statistics fields for monitoring performance
    avg_response_time: float = field(default=0.0, init=False)
    success_rate: float = field(default=1.0, init=False)
    last_success: bool = field(default=True, init=False)
    request_count: int = field(default=0, init=False)
    
    def update_stats(self, response_time: float, success: bool):
        """Update performance statistics for this tool"""
        self.request_count += 1
        # Update average response time with exponential moving average
        alpha = 0.3  # Weight for new observation (0.0-1.0)
        if self.request_count > 1:
            self.avg_response_time = (1 - alpha) * self.avg_response_time + alpha * response_time
        else:
            self.avg_response_time = response_time
            
        # Update success rate
        self.success_rate = (self.success_rate * (self.request_count - 1) + (1.0 if success else 0.0)) / self.request_count
        self.last_success = success

class ParallelSearchExecutor:
    """
    Executes multiple search tools in parallel with prioritization and fallback handling.
    
    Features:
    - Prioritized execution with timeout control
    - Adaptive prioritization based on historical performance
    - Circuit breaker to prevent repeated calls to failing services
    - Result merging and deduplication
    """
    
    def __init__(self):
        self._tool_configs: List[SearchToolConfig] = []
        self._circuit_breaker_threshold = 0.3  # Success rate below which to trigger circuit breaker
        self._circuit_breaker_reset_time = 60.0  # Seconds to wait before retrying a broken circuit
        self._last_circuit_break: Dict[SearchTool, float] = {}  # Maps tool to timestamp of last break
        self._semaphore = asyncio.Semaphore(10)  # Limit concurrent external API calls
        
    def register_tool(self, tool: SearchTool, priority: SearchPriority, 
                     timeout: float, max_results: int, weight: float = 1.0):
        """Register a search tool with its configuration"""
        config = SearchToolConfig(
            tool=tool,
            priority=priority,
            timeout=timeout,
            max_results=max_results,
            weight=weight
        )
        self._tool_configs.append(config)
        logger.info(f"Registered search tool {tool.__class__.__name__} with priority {priority.name}")
        
    def _is_circuit_broken(self, config: SearchToolConfig) -> bool:
        """Check if the circuit breaker is active for this tool"""
        # Skip check if success rate is acceptable
        if config.success_rate > self._circuit_breaker_threshold:
            return False
            
        # Check if enough time has passed to retry
        tool_id = id(config.tool)
        last_break_time = self._last_circuit_break.get(tool_id, 0)
        now = time.time()
        
        if now - last_break_time < self._circuit_breaker_reset_time:
            return True  # Circuit still broken
            
        # Reset the circuit breaker - will try again
        if tool_id in self._last_circuit_break:
            logger.info(f"Resetting circuit breaker for {config.tool.__class__.__name__}")
            
        return False
        
    def _break_circuit(self, config: SearchToolConfig):
        """Break the circuit for a failing tool"""
        tool_id = id(config.tool)
        self._last_circuit_break[tool_id] = time.time()
        logger.warning(f"Circuit breaker triggered for {config.tool.__class__.__name__}")
    
    async def _execute_search_with_timeout(self, 
                                         config: SearchToolConfig, 
                                         query: str) -> Tuple[List[Dict[str, Any]], bool]:
        """Execute a search with timeout handling and statistics tracking"""
        if not config.enabled or self._is_circuit_broken(config):
            return [], False
            
        start_time = time.time()
        success = False
        results = []
        
        try:
            # Use semaphore to limit concurrent API calls
            async with self._semaphore:
                # Execute search with timeout
                tool_results = await asyncio.wait_for(
                    config.tool.search(query, max_results=config.max_results),
                    timeout=config.timeout
                )
                
                results = tool_results if tool_results else []
                success = True
                
        except asyncio.TimeoutError:
            logger.warning(f"Search timeout for {config.tool.__class__.__name__} after {config.timeout}s")
            
        except Exception as e:
            logger.error(f"Search error with {config.tool.__class__.__name__}: {str(e)}")
            
        finally:
            # Update statistics regardless of outcome
            elapsed = time.time() - start_time
            config.update_stats(elapsed, success)
            
            # Check if we need to break the circuit
            if not success and config.success_rate < self._circuit_breaker_threshold:
                self._break_circuit(config)
                
            # Log outcome
            status = "succeeded" if success else "failed"
            logger.info(f"Search with {config.tool.__class__.__name__} {status} in {elapsed:.2f}s")
                
        return results, success
        
    async def execute_prioritized_search(self, query: str) -> Dict[str, Any]:
        """
        Execute search across multiple tools with prioritization.
        
        Returns a dictionary with:
        - results: merged search results
        - sources: list of sources that provided results
        - stats: performance statistics
        """
        if not self._tool_configs:
            logger.error("No search tools registered")
            return {"results": [], "sources": [], "stats": {}}
            
        # Sort tools by priority
        sorted_configs = sorted(self._tool_configs, key=lambda c: c.priority.value)
        
        # Hold all results and track which tools succeeded
        all_results: List[Dict[str, Any]] = []
        successful_tools: List[str] = []
        start_time = time.time()
        
        # Execute critical and high priority searches first (sequential)
        high_priority_configs = [c for c in sorted_configs 
                              if c.priority in (SearchPriority.CRITICAL, SearchPriority.HIGH)]
        
        critical_succeeded = False
        
        for config in high_priority_configs:
            results, success = await self._execute_search_with_timeout(config, query)
            
            if success:
                all_results.extend(results)
                successful_tools.append(config.tool.__class__.__name__)
                
                if config.priority == SearchPriority.CRITICAL:
                    critical_succeeded = True
                    
        # If any critical search succeeded and we have enough results, skip lower priorities
        if critical_succeeded and len(all_results) >= 5:
            lower_priority_configs = []
        else:
            # Run medium and lower priority searches in parallel
            lower_priority_configs = [c for c in sorted_configs 
                                   if c.priority not in (SearchPriority.CRITICAL, SearchPriority.HIGH)]
        
        if lower_priority_configs:
            # Execute all remaining searches in parallel
            tasks = [
                self._execute_search_with_timeout(config, query)
                for config in lower_priority_configs
            ]
            
            results_list = await asyncio.gather(*tasks)
            
            # Process results
            for i, (results, success) in enumerate(results_list):
                config = lower_priority_configs[i]
                if success:
                    all_results.extend(results)
                    successful_tools.append(config.tool.__class__.__name__)
        
        # Deduplicate results based on URL
        seen_urls = set()
        deduplicated_results = []
        
        for result in all_results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduplicated_results.append(result)
            elif not url:
                # Keep results without URLs (might be some non-web results)
                deduplicated_results.append(result)
                
        # Calculate execution statistics
        execution_time = time.time() - start_time
        
        # Gather performance stats for monitoring
        stats = {
            "execution_time": execution_time,
            "successful_tools": successful_tools,
            "total_results_before_dedup": len(all_results),
            "total_results_after_dedup": len(deduplicated_results),
            "tool_stats": {
                config.tool.__class__.__name__: {
                    "priority": config.priority.name,
                    "avg_response_time": config.avg_response_time,
                    "success_rate": config.success_rate,
                    "request_count": config.request_count
                }
                for config in self._tool_configs
            }
        }
        
        logger.info(f"Parallel search completed in {execution_time:.2f}s with {len(successful_tools)} successful tools")
        
        return {
            "results": deduplicated_results,
            "sources": successful_tools,
            "stats": stats
        }
        
    async def close(self):
        """Close all search tool sessions"""
        for config in self._tool_configs:
            await config.tool.close() 