#!/usr/bin/env python
"""
Test script for the Nexus search functionality
"""
import asyncio
import time
import json
import os
from dotenv import load_dotenv

from src.agents.search_agent import SearchAgent

# Load environment variables
load_dotenv()

async def test_search():
    """Test the search agent with a sample query"""
    # Initialize search agent
    agent = SearchAgent()
    
    # Example query
    query = "What are the latest advancements in AI?"
    
    print(f"\nExecuting search for: '{query}'")
    print("=" * 50)
    
    start_time = time.time()
    
    # Execute search
    results, reasoning_steps, sources, execution_time = await agent.search(
        query=query,
        max_results=3,
        use_web=True,
        depth=1
    )
    
    print(f"\nSearch completed in {execution_time:.2f} seconds")
    print("=" * 50)
    
    # Display results
    print("\nResults:")
    print(json.dumps(results, indent=2))
    
    print("\nReasoning Steps:")
    print(json.dumps(reasoning_steps, indent=2))
    
    print("\nSources:")
    print(json.dumps(sources, indent=2))
    
    return results

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set in environment variables or .env file")
        print("Please set your OpenAI API key before running this test")
        exit(1)
        
    # Run the test
    asyncio.run(test_search()) 