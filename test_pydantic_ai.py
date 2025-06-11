"""Simple test script for pydantic-ai migration."""

import asyncio
import os
from agents.planning_agent import create_research_plan
from agents.dependencies import initialize_dependencies
from models.schemas import ResearchPlan
from rich.console import Console


async def test_planning_agent():
    """Test the planning agent functionality."""
    console = Console()
    console.print("🧪 [bold blue]Testing Planning Agent[/bold blue]")
    
    try:
        # Test planning agent
        query = "Should I invest in AAPL for long-term growth?"
        context = "Looking for 3-5 year investment. Moderate risk tolerance."
        
        console.print(f"Query: {query}")
        console.print(f"Context: {context}")
        
        plan = await create_research_plan(query, context)
        
        console.print("\\n✅ [green]Planning agent test successful![/green]")
        console.print(f"Generated {len(plan.steps)} steps:")
        
        for i, step in enumerate(plan.steps, 1):
            console.print(f"  {i}. [cyan]{step.description}[/cyan]")
            console.print(f"     Focus: [dim]{step.focus_area}[/dim]")
            console.print(f"     Expected: [dim]{step.expected_outcome}[/dim]")
        
        console.print(f"\\nReasoning: [yellow]{plan.reasoning}[/yellow]")
        console.print(f"Priority Areas: [magenta]{', '.join(plan.priority_areas)}[/magenta]")
        
        return True
        
    except Exception as e:
        console.print(f"❌ [bold red]Planning agent test failed:[/bold red] {str(e)}")
        return False


async def test_dependencies():
    """Test dependency initialization."""
    console = Console()
    console.print("\\n🧪 [bold blue]Testing Dependencies[/bold blue]")
    
    try:
        deps = initialize_dependencies(
            query="Test query",
            context="Test context"
        )
        
        console.print("✅ [green]Dependencies initialized successfully![/green]")
        console.print(f"Vector DB: [cyan]{type(deps.vector_db).__name__}[/cyan]")
        console.print(f"SearxNG Client: [cyan]{type(deps.searxng_client).__name__}[/cyan]")
        console.print(f"Knowledge Base: [cyan]{type(deps.knowledge_base).__name__}[/cyan]")
        console.print(f"Current Query: [yellow]{deps.current_query}[/yellow]")
        
        return True
        
    except Exception as e:
        console.print(f"❌ [bold red]Dependencies test failed:[/bold red] {str(e)}")
        return False


async def main():
    """Main test function."""
    console = Console()
    console.print("[bold green]🚀 Pydantic-AI Migration Tests[/bold green]")
    console.print("="*50)
    
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        console.print("⚠️  [yellow]OPENAI_API_KEY not set - some tests may fail[/yellow]")
    
    # Run tests
    test_results = []
    
    test_results.append(await test_dependencies())
    test_results.append(await test_planning_agent())
    
    # Summary
    console.print("\\n" + "="*50)
    passed = sum(test_results)
    total = len(test_results)
    
    if passed == total:
        console.print(f"🎉 [bold green]All tests passed! ({passed}/{total})[/bold green]")
    else:
        console.print(f"⚠️  [yellow]Some tests failed: {passed}/{total} passed[/yellow]")
    
    console.print("\\n[dim]Migration components ready for full testing![/dim]")


if __name__ == "__main__":
    asyncio.run(main())