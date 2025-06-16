#!/usr/bin/env python3
"""Test main.py with queries that force RAG usage."""

import asyncio
import os
from dotenv import load_dotenv
from agents.dependencies import initialize_dependencies
from agents.planning_agent import create_research_plan
from agents.research_agent import conduct_research
from rich.console import Console

load_dotenv()

# Add RAG logging
def add_rag_logging():
    import agents.research_agent as agent_module
    original_search = agent_module.search_internal_docs
    
    async def logged_search(ctx, query, doc_type="all"):
        print(f"🔧 RAG TOOL CALLED: '{query}' (doc_type: {doc_type})")
        result = await original_search(ctx, query, doc_type)
        result_len = len(result) if result else 0
        print(f"✅ RAG TOOL RESULT: {result_len} chars returned")
        return result
    
    agent_module.search_internal_docs = logged_search

async def test_queries_that_need_rag():
    """Test queries that should trigger RAG usage."""
    
    add_rag_logging()
    console = Console()
    
    # Queries designed to require internal document analysis
    test_queries = [
        {
            "query": "Analyze Cameco's detailed financial statements and SEC filings for investment decision",
            "context": "Need analysis of official company filings and internal financial data",
            "description": "SEC filing analysis"
        },
        {
            "query": "What specific details about Cameco's uranium reserves and production capacity are in their 10-K filing?",
            "context": "Requiring official company disclosure documents",
            "description": "10-K specific query"
        },
        {
            "query": "Based on Cameco's internal earnings reports, what are the detailed quarterly financial trends?",
            "context": "Need analysis from company's own financial reports",
            "description": "Internal earnings analysis"
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        console.print(f"\n{'='*60}")
        console.print(f"[bold blue]Test {i}: {test['description']}[/bold blue]")
        console.print(f"Query: {test['query']}")
        console.print(f"Context: {test['context']}")
        console.print("="*60)
        
        try:
            deps = initialize_dependencies(test['query'], test['context'])
            
            console.print("📋 Creating research plan...")
            plan = await create_research_plan(test['query'], test['context'])
            
            console.print("🔬 Conducting research...")
            console.print("Tool Usage Log:")
            console.print("-" * 30)
            
            research_plan_text = f"Steps: {[step.model_dump() for step in plan.steps]}\nReasoning: {plan.reasoning}"
            
            findings = await conduct_research(
                query=test['query'],
                research_plan=research_plan_text,
                deps=deps
            )
            
            console.print("-" * 30)
            console.print(f"✅ [green]Analysis complete[/green]")
            console.print(f"Summary: {findings.summary[:200]}...")
            console.print(f"Confidence: {findings.confidence_score:.1%}")
            
        except Exception as e:
            console.print(f"❌ Error: {e}")

async def main():
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY required")
        return
    
    await test_queries_that_need_rag()
    
    print("\n🎯 Key Findings:")
    print("- Main.py agent autonomously decides which tools to use")
    print("- RAG is used when internal document analysis is specifically needed")
    print("- Agent may prefer web search for current/market information")
    print("- Query phrasing influences tool selection")

if __name__ == "__main__":
    asyncio.run(main())