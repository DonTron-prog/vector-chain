#!/usr/bin/env python3
"""Main.py with RAG tool usage logging to see agentic behavior."""

import os
import asyncio
from agents.dependencies import initialize_dependencies
from agents.planning_agent import create_research_plan
from agents.research_agent import conduct_research
from models.schemas import InvestmentAnalysis
from rich.console import Console

# Patch the research agent to add RAG logging
def add_rag_logging():
    """Add logging to RAG tool in research agent."""
    import agents.research_agent as agent_module
    
    original_search = agent_module.search_internal_docs
    
    async def logged_search(ctx, query, doc_type="all"):
        print(f"🔧 RAG TOOL CALLED: '{query}' (doc_type: {doc_type})")
        result = await original_search(ctx, query, doc_type)
        result_len = len(result) if result else 0
        print(f"✅ RAG TOOL RESULT: {result_len} chars returned")
        return result
    
    # Replace the tool with logged version
    agent_module.search_internal_docs = logged_search

async def test_main_with_rag_logging():
    """Test main.py workflow with RAG logging enabled."""
    
    # Add RAG logging
    add_rag_logging()
    
    console = Console()
    
    # Test with Cameco query since that's what's in ChromaDB
    query = "Should I invest in Cameco Corporation (CCO) for uranium exposure?"
    context = "Looking for commodity exposure in nuclear energy sector. 3-5 year horizon."
    
    console.print(f"🔍 [bold blue]Testing main.py with RAG logging:[/bold blue] {query}")
    console.print("=" * 60)
    
    try:
        # Initialize dependencies
        deps = initialize_dependencies(query, context)
        
        # Step 1: Create research plan
        console.print("📋 [yellow]Creating research plan...[/yellow]")
        plan = await create_research_plan(query, context)
        
        console.print(f"✅ [green]Plan created with {len(plan.steps)} steps[/green]")
        
        # Step 2: Conduct research with tool logging
        console.print("\n🔬 [yellow]Conducting research with tool logging...[/yellow]")
        console.print("Tool Usage Log:")
        console.print("-" * 30)
        
        research_plan_text = f"Steps: {[step.model_dump() for step in plan.steps]}\nReasoning: {plan.reasoning}"
        
        findings = await conduct_research(
            query=query,
            research_plan=research_plan_text,
            deps=deps
        )
        
        console.print("-" * 30)
        console.print("🎯 [bold green]Research completed![/bold green]")
        
        # Display results
        console.print(f"\n📊 Summary: {findings.summary}")
        console.print(f"🔑 Key Insights: {len(findings.key_insights)} insights")
        console.print(f"⚠️ Risk Factors: {len(findings.risk_factors)} risks") 
        console.print(f"📈 Confidence: {findings.confidence_score:.1%}")
        
        return findings
        
    except Exception as e:
        console.print(f"❌ [bold red]Research failed:[/bold red] {str(e)}")
        raise

async def main():
    """Run main.py workflow with RAG logging."""
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY environment variable required")
        return
    
    await test_main_with_rag_logging()
    
    print("\n" + "="*60)
    print("🎉 Main.py RAG Logging Test Complete!")
    print("\nObservations:")
    print("- Shows how RAG is used alongside other tools")
    print("- Agent decides when to use RAG vs web search vs calculator")
    print("- Multiple RAG calls demonstrate agentic behavior")

if __name__ == "__main__":
    asyncio.run(main())