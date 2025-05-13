# Parallel Search Execution with Prioritization

This document describes the parallel search execution system with prioritization implemented in the Windsurf AI Search Engine.

## Overview

The parallel search system allows the search engine to:

1. Execute multiple search tools concurrently to minimize response time
2. Prioritize more reliable/faster search tools
3. Handle failures gracefully with fallback mechanisms
4. Scale efficiently to handle large numbers of concurrent users

## Architecture

The system consists of these key components:

### 1. `ParallelSearchExecutor`

Core component responsible for:
- Managing and scheduling search executions
- Tracking performance statistics
- Implementing circuit breakers to prevent calls to failing services
- Deduplicating results
- Sorting and merging results from different sources

### 2. `SearchPriority` Enum

Defines priority levels for search tools:
- `CRITICAL`: Must-have sources, always executed first
- `HIGH`: Primary sources, executed early and given preference
- `MEDIUM`: Standard importance sources
- `LOW`: Lower importance sources
- `FALLBACK`: Last resort sources used only when others fail

### 3. Search Tool Configurations

Each search tool is registered with:
- Timeout settings
- Priority level
- Result weighting
- Performance tracking metrics

## Execution Flow

1. Critical and High-priority searches execute first
2. If sufficient results are found, lower-priority searches may be skipped
3. Medium and low-priority searches execute in parallel
4. Results are merged, deduplicated, and ranked
5. Performance statistics are updated for adaptive prioritization

## Features

### Circuit Breaker Pattern

The system implements a circuit breaker pattern to:
- Detect failing services
- Temporarily disable calls to failing services
- Periodically retry to see if services have recovered
- Log and monitor service health

### Adaptive Prioritization

Based on historical performance metrics, the system:
- Adjusts timeouts dynamically
- Reprioritizes tools based on response time and success rate
- Prefers more reliable tools over time

### Concurrency Control

The system limits concurrent external API calls to prevent:
- Rate limiting issues
- Excessive resource consumption
- Network congestion

## Performance Benefits

- **Reduced Latency**: By running searches in parallel, the total search time approaches the duration of the slowest successful search rather than the sum of all search times.
- **Improved Reliability**: With fallback mechanisms, the system can still return results even if some search services fail.
- **Resource Efficiency**: By canceling unnecessary searches when sufficient results are found, the system conserves API quotas and computational resources.
- **Scalability**: The architecture efficiently handles high volumes of concurrent search requests.

## Configuration Example

```python
# Register search tools with priorities (example)
search_executor.register_tool(
    tool=serper_search,
    priority=SearchPriority.HIGH,
    timeout=5.0,
    max_results=8,
    weight=1.0
)

search_executor.register_tool(
    tool=duckduckgo_search,
    priority=SearchPriority.MEDIUM,
    timeout=6.0,
    max_results=8,
    weight=0.8
)
``` 