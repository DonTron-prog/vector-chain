#!/usr/bin/env python3
"""
Direct ChromaDB testing and querying script.
Allows you to test RAG functionality and query the investment knowledge base.
"""

import asyncio
from agents.dependencies import ChromaDBClient, initialize_dependencies
from tools.vector_search import search_internal_docs

async def test_chromadb_connection():
    """Test basic ChromaDB connection and collection info."""
    print("=== Testing ChromaDB Connection ===")
    
    client = ChromaDBClient()
    collection = client.get_collection()
    
    # Get collection info
    count = collection.count()
    print(f"Documents in collection: {count}")
    
    # Get sample documents
    sample = collection.get(limit=3)
    print(f"Sample documents: {len(sample['documents'])}")
    
    return client

async def test_vector_search(query: str, doc_type: str = "all"):
    """Test vector search with specific queries."""
    print(f"\n=== Testing Vector Search: '{query}' ===")
    
    # Initialize dependencies to get proper vector_db client
    deps = initialize_dependencies(query)
    
    results = await search_internal_docs(deps.vector_db, query, doc_type)
    
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result.score:.3f}")
        print(f"   Company: {result.metadata.get('company', 'Unknown')}")
        print(f"   Doc Type: {result.metadata.get('document_type', 'Unknown')}")
        print(f"   Content: {result.content[:200]}...")
    
    return results

async def test_different_queries():
    """Test various investment queries."""
    queries = [
        ("AAPL financial performance", "10k"),
        ("Microsoft revenue growth", "all"),
        ("quarterly earnings results", "earnings"),
        ("Should I invest in Apple?", "all"),
        ("dividend yield information", "all")
    ]
    
    for query, doc_type in queries:
        await test_vector_search(query, doc_type)
        print("-" * 50)

async def explore_collection():
    """Explore what's in the ChromaDB collection."""
    print("=== Exploring Collection Contents ===")
    
    client = ChromaDBClient()
    collection = client.get_collection()
    
    # Get all metadata to understand document structure
    all_data = collection.get()
    
    # Analyze document types
    doc_types = set()
    companies = set()
    
    for metadata in all_data['metadatas']:
        if metadata:
            doc_types.add(metadata.get('document_type', 'unknown'))
            companies.add(metadata.get('company', 'unknown'))
    
    print(f"Document types available: {sorted(doc_types)}")
    print(f"Companies available: {sorted(companies)}")
    print(f"Total documents: {len(all_data['documents'])}")

async def main():
    """Main testing function."""
    try:
        # Test connection
        await test_chromadb_connection()
        
        # Explore collection
        await explore_collection()
        
        # Test specific queries
        await test_different_queries()
        
        # Interactive query mode
        print("\n=== Interactive Query Mode ===")
        print("Enter investment queries (or 'quit' to exit):")
        
        while True:
            query = input("\nQuery: ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if query:
                await test_vector_search(query)
    
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure ChromaDB is set up with investment documents.")

if __name__ == "__main__":
    asyncio.run(main())