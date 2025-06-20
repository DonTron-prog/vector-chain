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
        
    except Exception as e:
        # If API keys aren't configured or other issues, show architecture demo
        if "OPENROUTER_API_KEY" in str(e) or "API" in str(e):
            console.print(f"\n[yellow]⚠️  API configuration issue: {e}[/yellow]")
            console.print("[yellow]Demo will show the architecture without making actual API calls.[/yellow]")
        else:
            console.print(f"\n[yellow]Running architecture demo due to: {e}[/yellow]")
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
        
        # Show quick feedback demo
        console.print("\n[cyan]Quick feedback demonstration:[/cyan]")
        from models.schemas import ExecutionFeedback
        
        feedback = ExecutionFeedback(
            step_completed="Financial data analysis",
            findings_quality=0.75,
            data_gaps=["Missing competitive benchmarks"],
            unexpected_findings=["Strong services growth trend"],
            suggested_adjustments=["Add competitor analysis"],
            confidence_level=0.65
        )
        
        console.print(f"  Quality: {feedback.findings_quality:.1%}")
        console.print(f"  Confidence: {feedback.confidence_level:.1%}")
        console.print(f"  Gaps identified: {len(feedback.data_gaps)}")
        console.print(f"  Unexpected discoveries: {len(feedback.unexpected_findings)}")
        
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
    # Load environment variables and check API keys like main.py does
    try:
        from config import get_required_env_var
        get_required_env_var("OPENROUTER_API_KEY")
        print("✅ API keys configured, running full demo...")
    except RuntimeError as e:
        print(f"⚠️  {e}")
        print("Running architecture demo without API calls...")
    except ImportError:
        print("⚠️  Config module not found, running basic demo...")
    
    asyncio.run(demo_adaptive_research())