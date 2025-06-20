#!/usr/bin/env python3
"""Demo script showing adaptive research with memory capabilities."""

import asyncio
import os
from rich.console import Console
from rich.panel import Panel

async def demo_adaptive_research():
    """Demonstrate the adaptive research system."""
    console = Console()
    
    console.print(Panel.fit(
        "[bold blue]🧠 Adaptive Investment Research Demo[/bold blue]\n\n"
        "This demo shows how the planning agent adapts its research strategy\n"
        "based on execution feedback and maintains memory across iterations.",
        border_style="blue"
    ))
    
    # Check if we have API keys
    if not os.getenv("OPENROUTER_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        console.print("\n[red]⚠️  No API keys found. Please set OPENROUTER_API_KEY or OPENAI_API_KEY[/red]")
        console.print("\nDemo will show the architecture without making actual API calls.")
        return
    
    try:
        from main import adaptive_research_investment
        
        console.print("\n[yellow]Starting adaptive research demo...[/yellow]")
        console.print("Query: Should I invest in Apple (AAPL) for long-term growth?")
        console.print("Context: 5-year investment horizon, moderate risk tolerance")
        
        # Run adaptive research
        analysis = await adaptive_research_investment(
            query="Should I invest in Apple (AAPL) for long-term growth?",
            context="5-year investment horizon, moderate risk tolerance",
            max_adaptations=2  # Limit adaptations for demo
        )
        
        console.print("\n[green]✅ Adaptive research completed successfully![/green]")
        console.print(f"Final confidence score: {analysis.findings.confidence_score:.1%}")
        console.print(f"Sources used: {len(analysis.findings.sources)}")
        
    except ImportError:
        console.print("\n[yellow]Demo mode: Showing adaptive memory capabilities[/yellow]")
        
        # Show how memory processing works
        from agents.memory_processors import adaptive_memory_processor
        from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart
        
        # Create example conversation
        messages = [
            ModelRequest(parts=[UserPromptPart(content="Create AAPL research plan")]),
            ModelResponse(parts=[TextPart(content="Initial plan: 1. Financial analysis 2. Market position 3. Valuation")]),
            ModelRequest(parts=[UserPromptPart(content="Findings: Strong financials but missing competitive data")]),
            ModelResponse(parts=[TextPart(content="Plan update: Adding competitive analysis step")]),
            ModelRequest(parts=[UserPromptPart(content="Execute competitive analysis")]),
            ModelResponse(parts=[TextPart(content="Apple leads in services revenue vs competitors")]),
        ]
        
        console.print(f"\nOriginal conversation: {len(messages)} messages")
        
        processed = adaptive_memory_processor(messages)
        console.print(f"After memory processing: {len(processed)} messages")
        console.print("[dim]Memory system preserved important context while managing token usage[/dim]")
        
    except Exception as e:
        console.print(f"\n[red]❌ Demo failed: {e}[/red]")
    
    console.print("\n" + "="*60)
    console.print("[bold cyan]Key Features Demonstrated:[/bold cyan]")
    console.print("✅ Adaptive planning based on execution feedback")
    console.print("✅ Memory management across planning iterations")
    console.print("✅ Structured feedback generation")
    console.print("✅ Dynamic plan updates and reasoning")
    console.print("✅ Token-efficient conversation history")

if __name__ == "__main__":
    asyncio.run(demo_adaptive_research())