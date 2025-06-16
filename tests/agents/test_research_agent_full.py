#!/usr/bin/env python3
"""Test the pydantic-ai research agent's RAG functionality."""

import asyncio
import os
from dotenv import load_dotenv
from agents.dependencies import initialize_dependencies
from agents.research_agent import research_agent
from models.schemas import InvestmentFindings

load_dotenv()

async def test_rag_agent():
    """Test research agent with RAG queries."""
    
    # Test queries focused on Cameco (CCO) since that's what's in ChromaDB
    test_queries = [
        "What is Cameco's uranium production capacity?",
        "Tell me about CCO's financial performance and revenue growth",
        "What are the main investment risks for Cameco?",
        "How does Cameco's dividend policy work?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"🤖 Testing RAG Agent Query: {query}")
        print("="*60)
        
        try:
            # Initialize dependencies with ChromaDB
            deps = initialize_dependencies(query)
            
            # Run research agent - it will naturally use RAG tool
            prompt = f"""Investment Query: {query}
            
            Use your tools to research this question about Cameco Corporation (CCO).
            Focus on searching internal documents first, then supplement with any needed analysis."""
            
            result = await research_agent.run(prompt, deps=deps)
            
            print(f"✅ Agent Response:")
            print(f"Summary: {result.data.summary}")
            print(f"Key Insights: {result.data.key_insights}")
            print(f"Confidence: {result.data.confidence_score:.1%}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_direct_rag_tool():
    """Test the RAG tool directly via vector search."""
    print("\n" + "="*60)
    print("🔧 Testing RAG Tool Directly")
    print("="*60)
    
    deps = initialize_dependencies("test")
    
    # Test the underlying vector search function
    from tools.vector_search import search_internal_docs, format_document_results
    
    results = await search_internal_docs(deps.vector_db, "uranium production", "all", 3)
    formatted = format_document_results(results)
    
    print("📄 RAG Tool Results:")
    print(formatted[:500] + "..." if len(formatted) > 500 else formatted)

async def main():
    """Main test function."""
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY required")
        return
        
    await test_direct_rag_tool()
    await test_rag_agent()

if __name__ == "__main__":
    asyncio.run(main())