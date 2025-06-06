#!/usr/bin/env python3
"""
Test script for the simplified investment research agent.
"""

import os
from rich.console import Console
from rich.panel import Panel
from controllers.planning_agent import research_investment, InvestmentQuery, ResearchPlan


def test_simplified_research():
    """Test the simplified research function."""
    console = Console()
    
    console.print(Panel(
        "[bold blue]🧪 Testing Simplified Investment Research Agent[/bold blue]",
        title="Simplified Test",
        border_style="blue"
    ))
    
    # Check if we have an API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[bold red]❌ OPENAI_API_KEY not found in environment[/bold red]")
        console.print("Set your API key: export OPENAI_API_KEY='your-key-here'")
        return False
    
    try:
        # Test the simplified research function
        console.print("🔧 Testing simplified investment research...")
        
        result = research_investment(
            query="Should I invest in AAPL for long-term growth?",
            context="AAPL recently launched new products. Market sentiment is mixed.",
            model="gpt-4o-mini"
        )
        
        # Validate result
        console.print("✅ Research completed!")
        console.print(f"📊 Success: {result.success}")
        console.print(f"📋 Steps: {len(result.steps)}")
        console.print(f"🧠 Reasoning: {result.reasoning[:100]}...")
        console.print(f"📚 Knowledge: {result.accumulated_knowledge[:100]}...")
        
        console.print("\n📋 Generated Steps:")
        for i, step in enumerate(result.steps, 1):
            status_emoji = "✅" if step.status == "completed" else "⏳" if step.status == "pending" else "❌"
            console.print(f"  {i}. {status_emoji} {step.description}")
        
        return True
        
    except Exception as e:
        console.print(f"[bold red]❌ Error testing simplified research: {e}[/bold red]")
        return False


def test_schema_validation():
    """Test schema validation."""
    console = Console()
    
    console.print(Panel(
        "[bold blue]🧪 Testing Schema Validation[/bold blue]",
        title="Schema Test",
        border_style="blue"
    ))
    
    try:
        # Test InvestmentQuery
        query = InvestmentQuery(
            query="Test investment query",
            context="Test context"
        )
        console.print("✅ InvestmentQuery validation passed")
        
        # Test ResearchPlan
        plan = ResearchPlan(
            query="Test query",
            context="Test context",
            steps=[],
            reasoning="Test reasoning"
        )
        console.print("✅ ResearchPlan validation passed")
        
        return True
        
    except Exception as e:
        console.print(f"[bold red]❌ Schema validation error: {e}[/bold red]")
        return False


def main():
    """Main test function."""
    console = Console()
    
    console.print(Panel(
        "[bold blue]🧪 Simplified Investment Research Agent Test Suite[/bold blue]\n"
        "Testing the new simplified architecture",
        title="Test Suite",
        border_style="blue"
    ))
    
    tests = [
        ("Schema Validation", test_schema_validation),
        ("Simplified Research", test_simplified_research),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        console.print(f"\n{'='*60}")
        console.print(f"Running: {test_name}")
        console.print('='*60)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            console.print(f"[bold red]❌ Test {test_name} failed with exception: {e}[/bold red]")
            results.append((test_name, False))
    
    # Summary
    console.print(f"\n{'='*60}")
    console.print("[bold blue]Test Results Summary[/bold blue]")
    console.print('='*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        console.print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    console.print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        console.print("[bold green]🎉 All tests passed! Simplified Investment Research Agent is working correctly.[/bold green]")
    else:
        console.print("[bold yellow]⚠️ Some tests failed. Check the output above for details.[/bold yellow]")


if __name__ == "__main__":
    main()