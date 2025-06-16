#!/usr/bin/env python3
"""Test pydantic-ai agent using ONLY the RAG tool - no web search, no calculations."""

import asyncio
import os
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from agents.dependencies import ResearchDependencies, initialize_dependencies
from models.schemas import InvestmentFindings
from tools.vector_search import search_internal_docs as _search_internal_docs, format_document_results

load_dotenv()

# Configure model
openai_model = OpenAIModel(
    'gpt-4o-mini',
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY')
)

# Create RAG-only agent (no web search, no calculator, no scraper)
rag_only_agent = Agent(
    openai_model,
    deps_type=ResearchDependencies,
    result_type=InvestmentFindings,
    system_prompt="""You are an investment research agent with access to ONLY internal documents via vector search.

You have ONE tool available:
- search_internal_docs: Search SEC filings, earnings reports, analyst reports in vector database

RESTRICTIONS:
- You CANNOT search the web
- You CANNOT scrape webpages  
- You CANNOT perform financial calculations
- You can ONLY use the internal document search

RESEARCH APPROACH:
1. Understand the investment query
2. Search internal documents multiple times with different search terms
3. Analyze the retrieved document content to answer the question
4. Build your analysis solely from internal document findings
5. Provide confidence score based on document coverage and relevance

Use multiple search queries to gather comprehensive information from the vector database.
Focus on extracting insights directly from the document content."""
)

@rag_only_agent.tool
async def search_internal_docs(
    ctx: RunContext[ResearchDependencies], 
    query: str,
    doc_type: str = "all"
) -> str:
    """Search internal investment documents (SEC filings, earnings, analyst reports).
    
    Args:
        query: Search query for documents
        doc_type: Type of document (10k, 10q, earnings, analyst, all)
    """
    print(f"🔧 RAG TOOL CALLED: '{query}' (doc_type: {doc_type})")
    
    results = await _search_internal_docs(
        ctx.deps.vector_db,
        query,
        doc_type=doc_type,
        n_results=5
    )
    
    formatted = format_document_results(results)
    print(f"✅ RAG TOOL RESULT: {len(results)} documents found, {len(formatted)} chars returned")
    
    return formatted

async def test_rag_agent_queries():
    """Test RAG-only agent with various investment queries."""
    
    rag_test_queries = [
        {
            "query": "What is Cameco's uranium production capacity and recent production trends?",
            "context": "Analyzing production capabilities for investment decision",
            "description": "Production analysis test"
        },
        {
            "query": "How has Cameco's financial performance been in recent quarters?",
            "context": "Looking at revenue, earnings, and profitability trends",
            "description": "Financial performance test"
        },
        {
            "query": "What are the main investment risks associated with Cameco?",
            "context": "Risk assessment for portfolio allocation",
            "description": "Risk analysis test"
        },
        {
            "query": "Explain Cameco's dividend policy and shareholder returns",
            "context": "Income investing evaluation",
            "description": "Dividend analysis test"
        }
    ]
    
    print("🤖 RAG-ONLY AGENT Testing Suite")
    print("=" * 60)
    print("Testing pydantic-ai agent with ONLY RAG tool available")
    print("=" * 60)
    
    for i, test in enumerate(rag_test_queries, 1):
        print(f"\n{i}. {test['description']}")
        print(f"Query: {test['query']}")
        print(f"Context: {test['context']}")
        print("-" * 50)
        print("Tool Usage Log:")
        
        try:
            # Initialize dependencies
            deps = initialize_dependencies(test['query'], test['context'])
            
            # Create agent prompt
            prompt = f"""Investment Query: {test['query']}
            
Context: {test['context']}

Research this question using only internal documents. Use multiple search queries if needed to gather comprehensive information."""

            # Run RAG-only agent
            result = await rag_only_agent.run(prompt, deps=deps)
            
            print("-" * 50)
            print("🎯 AGENT ANALYSIS:")
            print(f"Summary: {result.data.summary}")
            print(f"Key Insights: {result.data.key_insights}")
            print(f"Risk Factors: {result.data.risk_factors}")
            print(f"Recommendation: {result.data.recommendation}")
            print(f"Confidence: {result.data.confidence_score:.1%}")
            print(f"Sources: {len(result.data.sources)}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            
        print("=" * 60)

async def test_rag_agent_iterative():
    """Test agent's ability to make multiple RAG calls for complex queries."""
    
    print("\n🔄 Testing Iterative RAG Usage")
    print("=" * 40)
    
    complex_query = """Provide a comprehensive investment analysis of Cameco Corporation covering:
1. Business operations and uranium production
2. Financial performance and profitability  
3. Market position and competitive advantages
4. Investment risks and opportunities
5. Overall investment recommendation

Use multiple searches to gather complete information."""

    deps = initialize_dependencies(complex_query)
    
    print("Query: Comprehensive Cameco investment analysis")
    print("Expected: Multiple RAG tool calls for different aspects")
    print("-" * 40)
    print("Tool Usage Log:")
    
    try:
        result = await rag_only_agent.run(complex_query, deps=deps)
        
        print("-" * 40)
        print("🏁 COMPREHENSIVE ANALYSIS:")
        print(f"Summary: {result.data.summary}")
        print(f"Key Insights: {len(result.data.key_insights)} insights")
        print(f"Risk Factors: {len(result.data.risk_factors)} risks")
        print(f"Confidence: {result.data.confidence_score:.1%}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    """Run RAG-only agent tests."""
    if not os.getenv('OPENROUTER_API_KEY'):
        print("❌ OPENROUTER_API_KEY environment variable required")
        return
    
    try:
        await test_rag_agent_queries()
        await test_rag_agent_iterative()
        
        print("\n🎉 RAG-Only Agent Testing Complete!")
        print("\nKey Observations:")
        print("- Agent can only use search_internal_docs tool")
        print("- Multiple RAG calls demonstrate agentic behavior") 
        print("- Analysis built entirely from vector database content")
        
    except Exception as e:
        print(f"❌ RAG agent testing failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())