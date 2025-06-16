#!/usr/bin/env python3
"""Simple RAG testing for ChromaDB queries using shared test utilities."""

import asyncio
import sys
import os

# Add parent directory to path for test_utils
test_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(test_dir)

from test_utils import run_vector_search_test, print_search_results, TestQueries

async def query_rag(query: str, doc_type: str = "all", n_results: int = 3):
    """Simple RAG query function using shared utilities."""
    results = await run_vector_search_test(query, doc_type, n_results)
    print_search_results(results, query)

async def main():
    """Test different query types."""
    
    test_queries = [
        "revenue growth",
        "financial performance", 
        "uranium production",
        "dividend information",
        "investment strategy",
        "quarterly results"
    ]
    
    print("🧪 Testing RAG with ChromaDB")
    print("=" * 60)
    
    for query in test_queries:
        await query_rag(query)
        print("-" * 60)
        
    # Interactive mode
    print("\n💬 Interactive Mode - Enter queries (or 'quit' to exit):")
    while True:
        try:
            query = input("\n> ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                break
            if query:
                await query_rag(query)
        except (KeyboardInterrupt, EOFError):
            break
    
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())