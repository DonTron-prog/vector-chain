#!/usr/bin/env python3
"""Test ONLY the RAG functionality - no web search, no calculations, just ChromaDB vector search."""

import asyncio
from agents.dependencies import initialize_dependencies
from tools.vector_search import search_internal_docs, format_document_results

async def test_rag_queries():
    """Test various RAG queries against ChromaDB."""
    
    # Focused RAG test queries for Cameco data
    rag_tests = [
        {
            "query": "uranium production capacity",
            "doc_type": "all",
            "description": "Test production capacity search"
        },
        {
            "query": "revenue and financial performance", 
            "doc_type": "all",
            "description": "Test financial data retrieval"
        },
        {
            "query": "dividend policy",
            "doc_type": "all", 
            "description": "Test dividend information search"
        },
        {
            "query": "investment risks",
            "doc_type": "all",
            "description": "Test risk factor identification"
        },
        {
            "query": "quarterly earnings results",
            "doc_type": "earnings",
            "description": "Test document type filtering"
        }
    ]
    
    print("🔍 RAG-ONLY Testing Suite")
    print("=" * 50)
    print(f"Testing against ChromaDB with vector search only")
    print("=" * 50)
    
    # Initialize dependencies once
    deps = initialize_dependencies("rag test")
    collection_info = deps.vector_db.get_collection()
    print(f"📊 Collection: {collection_info.name} ({collection_info.count()} documents)")
    print()
    
    for i, test in enumerate(rag_tests, 1):
        print(f"{i}. {test['description']}")
        print(f"   Query: '{test['query']}'")
        print(f"   Doc Type: {test['doc_type']}")
        print("-" * 30)
        
        try:
            # Pure RAG search - no agent, no other tools
            results = await search_internal_docs(
                deps.vector_db, 
                test['query'], 
                test['doc_type'], 
                n_results=3
            )
            
            if results:
                print(f"   ✅ Found {len(results)} results")
                
                # Show top result details
                top_result = results[0]
                print(f"   🏆 Best match (score: {top_result.score:.3f})")
                print(f"      Company: {top_result.metadata.get('company', 'Unknown')}")
                print(f"      Doc Type: {top_result.metadata.get('document_type', 'Unknown')}")
                print(f"      Content: {top_result.content[:150]}...")
                
                # Show all scores
                scores = [r.score for r in results]
                print(f"   📈 All scores: {[f'{s:.3f}' for s in scores]}")
                
            else:
                print("   ❌ No results found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
        print()

async def test_rag_formatted_output():
    """Test RAG with formatted output for LLM consumption."""
    print("📄 Testing Formatted RAG Output")
    print("=" * 40)
    
    deps = initialize_dependencies("format test")
    
    query = "Cameco uranium production and revenue"
    results = await search_internal_docs(deps.vector_db, query, "all", 2)
    
    if results:
        # Test the formatting function used by agents
        formatted = format_document_results(results)
        
        print(f"Query: {query}")
        print(f"Raw results: {len(results)} items")
        print(f"Formatted length: {len(formatted)} characters")
        print()
        print("Formatted output for LLM:")
        print("-" * 25)
        print(formatted)
    else:
        print("No results to format")

async def test_rag_edge_cases():
    """Test RAG edge cases and error handling."""
    print("\n🧪 Testing RAG Edge Cases")
    print("=" * 35)
    
    deps = initialize_dependencies("edge test")
    
    edge_tests = [
        ("", "Empty query"),
        ("nonexistent company xyz", "Non-existent content"),
        ("a", "Very short query"),
        ("the and or but with for", "Stop words only"),
        ("uranium " * 50, "Very long query")
    ]
    
    for query, description in edge_tests:
        print(f"Testing: {description}")
        print(f"Query: '{query[:50]}{'...' if len(query) > 50 else ''}'")
        
        try:
            results = await search_internal_docs(deps.vector_db, query, "all", 2)
            print(f"Result: {len(results)} items found")
            if results:
                print(f"Best score: {results[0].score:.3f}")
        except Exception as e:
            print(f"Error: {e}")
        print()

async def main():
    """Run all RAG-only tests."""
    try:
        await test_rag_queries()
        await test_rag_formatted_output() 
        await test_rag_edge_cases()
        
        print("🎉 RAG-Only Testing Complete!")
        
    except Exception as e:
        print(f"❌ RAG testing failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())