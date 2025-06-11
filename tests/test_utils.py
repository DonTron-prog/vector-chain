"""Shared test utilities to eliminate duplication across test files."""

import asyncio
from typing import List
from agents.dependencies import initialize_dependencies, ResearchDependencies
from tools.vector_search import search_internal_docs, format_document_results
from models.schemas import DocumentSearchResult


async def setup_test_dependencies(query: str = "test query", context: str = "") -> ResearchDependencies:
    """Initialize test dependencies with consistent setup.
    
    Args:
        query: Test query string
        context: Test context string
        
    Returns:
        Initialized ResearchDependencies
    """
    return initialize_dependencies(query, context)


async def run_vector_search_test(
    query: str, 
    doc_type: str = "all", 
    n_results: int = 3
) -> List[DocumentSearchResult]:
    """Run a vector search test with standard setup.
    
    Args:
        query: Search query
        doc_type: Document type filter
        n_results: Number of results to return
        
    Returns:
        List of search results
    """
    deps = await setup_test_dependencies(query)
    return await search_internal_docs(deps.vector_db, query, doc_type, n_results)


def print_search_results(results: List[DocumentSearchResult], query: str):
    """Print search results in a consistent format.
    
    Args:
        results: Search results to display
        query: Original query for context
    """
    print(f"🔍 Query: {query}")
    print("=" * 50)
    
    if not results:
        print("❌ No results found")
        return
    
    print(f"✅ Found {len(results)} results:")
    print()
    
    for i, result in enumerate(results, 1):
        print(f"{i}. Score: {result.score:.3f}")
        company = result.metadata.get('company', 'Unknown')
        doc_type = result.metadata.get('document_type', 'Unknown')
        print(f"   📊 Source: {company} - {doc_type}")
        content = result.content[:200] + "..." if len(result.content) > 200 else result.content
        print(f"   📄 Content: {content}")
        print()


def print_formatted_results(results: List[DocumentSearchResult], query: str):
    """Print formatted results as they would appear to LLM.
    
    Args:
        results: Search results to format
        query: Original query for context
    """
    print(f"🔍 Formatted Results for: {query}")
    print("=" * 50)
    
    formatted = format_document_results(results)
    print(formatted)


class TestQueries:
    """Standard test queries for consistent testing."""
    
    # Cameco-focused queries (matches current ChromaDB content)
    PRODUCTION = "uranium production capacity"
    FINANCIAL = "revenue and financial performance"
    DIVIDEND = "dividend policy"
    RISKS = "investment risks"
    QUARTERLY = "quarterly earnings results"
    
    # Complex queries
    COMPREHENSIVE = """Provide a comprehensive investment analysis covering:
    1. Business operations and production
    2. Financial performance and profitability  
    3. Market position and competitive advantages
    4. Investment risks and opportunities
    5. Overall investment recommendation"""
    
    @classmethod
    def get_all_basic_queries(cls) -> List[str]:
        """Get all basic test queries."""
        return [cls.PRODUCTION, cls.FINANCIAL, cls.DIVIDEND, cls.RISKS, cls.QUARTERLY]


class TestDocumentTypes:
    """Standard document type filters for testing."""
    
    ALL = "all"
    ANNUAL = "10k"
    QUARTERLY = "10q" 
    EARNINGS = "earnings"
    ANALYST = "analyst"
    
    @classmethod
    def get_all_types(cls) -> List[str]:
        """Get all document type filters."""
        return [cls.ALL, cls.ANNUAL, cls.QUARTERLY, cls.EARNINGS, cls.ANALYST]


async def run_comprehensive_rag_test():
    """Run a comprehensive RAG test covering all basic scenarios."""
    print("🧪 Running Comprehensive RAG Test Suite")
    print("=" * 60)
    
    # Test all query types
    for query in TestQueries.get_all_basic_queries():
        results = await run_vector_search_test(query)
        print_search_results(results, query)
        print("-" * 60)
    
    # Test document type filtering
    print("\n📋 Testing Document Type Filtering")
    print("=" * 40)
    
    base_query = TestQueries.FINANCIAL
    for doc_type in TestDocumentTypes.get_all_types():
        results = await run_vector_search_test(base_query, doc_type, 2)
        print(f"Doc Type '{doc_type}': {len(results)} results")
        if results:
            print(f"  Best score: {results[0].score:.3f}")
        print()


def add_rag_logging_to_function(func, tool_name: str):
    """Add logging to a RAG function for debugging.
    
    Args:
        func: Function to wrap with logging
        tool_name: Name to display in logs
        
    Returns:
        Wrapped function with logging
    """
    async def logged_wrapper(*args, **kwargs):
        print(f"🔧 {tool_name} CALLED")
        result = await func(*args, **kwargs)
        result_len = len(str(result)) if result else 0
        print(f"✅ {tool_name} RESULT: {result_len} chars returned")
        return result
    
    return logged_wrapper


# Edge case test data
EDGE_CASE_QUERIES = [
    ("", "Empty query"),
    ("a", "Single character"),
    ("the and or but", "Stop words only"),
    ("nonexistent company xyz", "Non-existent content"),
    ("uranium " * 50, "Very long query")
]


async def run_edge_case_tests():
    """Run edge case tests for RAG system."""
    print("🧪 Testing RAG Edge Cases")
    print("=" * 35)
    
    for query, description in EDGE_CASE_QUERIES:
        print(f"Testing: {description}")
        print(f"Query: '{query[:50]}{'...' if len(query) > 50 else ''}'")
        
        try:
            results = await run_vector_search_test(query, "all", 2)
            print(f"Result: {len(results)} items found")
            if results:
                print(f"Best score: {results[0].score:.3f}")
        except Exception as e:
            print(f"Error: {e}")
        print()


if __name__ == "__main__":
    # Run comprehensive tests when executed directly
    asyncio.run(run_comprehensive_rag_test())
    asyncio.run(run_edge_case_tests())