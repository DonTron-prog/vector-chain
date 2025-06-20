#!/usr/bin/env python3
"""Quick demo of adaptive memory features without full research execution."""

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

async def quick_memory_demo():
    """Quick demonstration of memory and adaptation features."""
    console = Console()
    
    console.print(Panel.fit(
        "[bold blue]🧠 Quick Adaptive Memory Demo[/bold blue]\n\n"
        "Demonstrating key memory and adaptation features\n"
        "without running full research workflow.",
        border_style="blue"
    ))
    
    # Test 1: Show plan creation
    console.print("\n[bold yellow]1. Creating Initial Research Plan[/bold yellow]")
    try:
        from agents.planning_agent import create_research_plan
        
        plan = await create_research_plan(
            query="Should I invest in AAPL for growth?",
            context="5-year horizon, moderate risk tolerance"
        )
        
        console.print(f"✅ Plan created with {len(plan.steps)} steps:")
        for i, step in enumerate(plan.steps, 1):
            console.print(f"   {i}. [cyan]{step.focus_area}[/cyan]: {step.description[:80]}...")
            
    except Exception as e:
        console.print(f"❌ Plan creation failed: {e}")
        return
    
    # Test 2: Show feedback generation
    console.print("\n[bold yellow]2. Simulating Execution Feedback[/bold yellow]")
    from models.schemas import ExecutionFeedback
    
    feedback = ExecutionFeedback(
        step_completed="Financial data collection for AAPL",
        findings_quality=0.7,
        data_gaps=["Missing competitor analysis", "No macroeconomic context"],
        unexpected_findings=["Strong services growth", "China market concerns"],
        suggested_adjustments=["Add competitive benchmarking", "Include macro analysis"],
        confidence_level=0.6
    )
    
    # Create feedback table
    feedback_table = Table(title="Execution Feedback")
    feedback_table.add_column("Metric", style="cyan")
    feedback_table.add_column("Value", style="green")
    
    feedback_table.add_row("Findings Quality", f"{feedback.findings_quality:.1%}")
    feedback_table.add_row("Confidence Level", f"{feedback.confidence_level:.1%}")
    feedback_table.add_row("Data Gaps", f"{len(feedback.data_gaps)} identified")
    feedback_table.add_row("Unexpected Findings", f"{len(feedback.unexpected_findings)} discovered")
    feedback_table.add_row("Suggestions", f"{len(feedback.suggested_adjustments)} recommendations")
    
    console.print(feedback_table)
    
    # Test 3: Show plan adaptation decision
    console.print("\n[bold yellow]3. Evaluating Plan Adaptation[/bold yellow]")
    try:
        from models.schemas import PlanUpdateRequest
        from agents.planning_agent import evaluate_plan_update
        
        # Create update request
        update_request = PlanUpdateRequest(
            current_step=1,
            feedback=feedback,
            remaining_steps=plan.steps[1:] if len(plan.steps) > 1 else []
        )
        
        # Evaluate plan update
        update_response, message_history = await evaluate_plan_update(update_request)
        
        console.print(f"✅ Update Decision: [{'green' if update_response.should_update else 'yellow'}]{update_response.should_update}[/]")
        console.print(f"📊 Confidence: {update_response.confidence:.1%}")
        console.print(f"💭 Reasoning: [dim]{update_response.reasoning[:100]}...[/dim]")
        
        if update_response.updated_steps:
            console.print(f"🔄 Updated Steps: {len(update_response.updated_steps)} new/modified steps")
            
        console.print(f"🧠 Message History: {len(message_history)} messages tracked")
        
    except Exception as e:
        console.print(f"❌ Plan evaluation failed: {e}")
    
    # Test 4: Show memory processing
    console.print("\n[bold yellow]4. Memory Processing Demonstration[/bold yellow]")
    try:
        from agents.memory_processors import adaptive_memory_processor
        from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart
        
        # Create mock conversation
        mock_conversation = [
            ModelRequest(parts=[UserPromptPart(content="Create AAPL research plan")]),
            ModelResponse(parts=[TextPart(content="I'll analyze Apple's financials, market position, and growth prospects...")]),
            ModelRequest(parts=[UserPromptPart(content="Focus on services revenue growth")]),
            ModelResponse(parts=[TextPart(content="Services revenue has grown 15% annually, showing strong recurring revenue...")]),
            ModelRequest(parts=[UserPromptPart(content="Add competitive analysis vs Microsoft")]),
            ModelResponse(parts=[TextPart(content="Compared to Microsoft, Apple has stronger consumer brand loyalty but...")]),
            ModelRequest(parts=[UserPromptPart(content="Update plan based on China market concerns")]),
            ModelResponse(parts=[TextPart(content="Given regulatory risks in China, adjusting geographic analysis...")]),
        ]
        
        # Process memory
        processed = adaptive_memory_processor(mock_conversation)
        
        memory_table = Table(title="Memory Management")
        memory_table.add_column("Stage", style="cyan")
        memory_table.add_column("Messages", style="green")
        memory_table.add_column("Status", style="yellow")
        
        memory_table.add_row("Original Conversation", str(len(mock_conversation)), "Full context")
        memory_table.add_row("After Processing", str(len(processed)), "Optimized for tokens")
        memory_table.add_row("Reduction", f"{len(mock_conversation) - len(processed)}", "Messages filtered")
        
        console.print(memory_table)
        
    except Exception as e:
        console.print(f"❌ Memory processing failed: {e}")
    
    # Summary
    console.print("\n" + "="*60)
    console.print("[bold cyan]🎯 Key Features Demonstrated:[/bold cyan]")
    console.print("✅ Dynamic plan creation based on query and context")
    console.print("✅ Structured feedback evaluation (quality, gaps, findings)")  
    console.print("✅ Intelligent adaptation decision making")
    console.print("✅ Memory-based conversation tracking")
    console.print("✅ Token-efficient message processing")
    console.print("✅ Type-safe data models throughout")
    
    console.print(f"\n[green]🧠 Adaptive memory system ready for investment research![/green]")

if __name__ == "__main__":
    # Load environment variables and check API keys
    try:
        from config import get_required_env_var
        get_required_env_var("OPENROUTER_API_KEY")
        print("✅ API keys configured")
    except RuntimeError as e:
        print(f"⚠️  {e}")
    except ImportError:
        print("⚠️  Config module not found")
    
    asyncio.run(quick_memory_demo())