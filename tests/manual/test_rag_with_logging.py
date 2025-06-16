#!/usr/bin/env python3
"""Test RAG agent with tool usage logging."""

import asyncio
import os
from dotenv import load_dotenv
from agents.dependencies import initialize_dependencies
from agents.research_agent import research_agent

load_dotenv()

# Monkey patch to add logging to tools
original_search_internal = None
original_search_web = None
original_calculate = None

def log_tool_usage(tool_name):
    """Decorator to log tool usage."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            print(f"🔧 TOOL USED: {tool_name}")
            result = await func(*args, **kwargs)
            print(f"✅ TOOL RESULT: {len(str(result))} chars returned")
            return result
        return wrapper
    return decorator

async def test_with_logging():
    """Test agent with tool usage logging."""
    
    # Patch the tools to add logging
    import agents.research_agent as agent_module
    agent_module.search_internal_docs = log_tool_usage("SEARCH_INTERNAL_DOCS")(agent_module.search_internal_docs)
    agent_module.search_web = log_tool_usage("SEARCH_WEB")(agent_module.search_web)
    agent_module.calculate_financial_metrics = log_tool_usage("CALCULATE_METRICS")(agent_module.calculate_financial_metrics)
    
    query = "What is Cameco's uranium production capacity and financial performance?"
    
    print(f"🤖 Testing Query: {query}")
    print("=" * 60)
    print("Tool Usage Log:")
    print("-" * 30)
    
    deps = initialize_dependencies(query)
    
    prompt = f"""Investment Query: {query}
    
    Research this question about Cameco Corporation (CCO).
    Use internal documents first, then add financial analysis if relevant."""
    
    try:
        result = await research_agent.run(prompt, deps=deps)
        
        print("-" * 30)
        print(f"📊 Final Result:")
        print(f"Summary: {result.data.summary}")
        print(f"Confidence: {result.data.confidence_score:.1%}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY required")
        return
    
    await test_with_logging()

if __name__ == "__main__":
    asyncio.run(main())