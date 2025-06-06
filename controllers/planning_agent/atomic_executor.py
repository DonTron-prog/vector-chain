#!/usr/bin/env python3
"""
Atomic Planning Agent Executor - Entry point using Atomic Agents framework.
"""

import openai
import instructor
from rich.console import Console
from rich.panel import Panel
from orchestration_engine import ConfigManager, ToolManager, OrchestratorCore, create_orchestrator_agent
from controllers.planning_agent.atomic_planning_agent import (
    create_atomic_planning_agent
)
# Import the correct input schema from planner_schemas
from controllers.planning_agent.planner_schemas import PlanningAgentInputSchema
from controllers.planning_agent.execution_orchestrator import (
    ExecutionOrchestrator,
    ExecutionOrchestratorInputSchema
)

from controllers.planning_agent.planner_schemas import (
    PlanningAgentOutputSchema,
    SimplePlanSchema
)


def process_query_with_atomic_planning(investment_query: str, research_context: str = "", model: str = "mistral/ministral-8b") -> PlanningAgentOutputSchema:
    """
    Process an investment query using the atomic planning agent architecture.
    
    This function demonstrates the atomic agents pattern:
    1. AtomicPlanningAgent generates structured investment research plans
    2. ExecutionOrchestrator executes these plans
    3. Clean separation of concerns with schema-based chaining
    
    Args:
        investment_query: The investment query to process
        research_context: Contextual information for the research
        model: Model name for LLM calls
        
    Returns:
        PlanningAgentOutputSchema: Complete planning execution results
    """
    console = Console()
    
    # Initialize components
    config = ConfigManager.load_configuration()
    tools = ConfigManager.initialize_tools(config)
    
    # Create instructor client for orchestrator agent
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=config.get("openrouter_api_key")
    )
    instructor_client = instructor.from_openai(client, mode=instructor.Mode.JSON)
    
    # Create orchestrator core
    orchestrator_agent = create_orchestrator_agent(instructor_client, model)
    tool_manager = ToolManager(tools)
    orchestrator_core = OrchestratorCore(orchestrator_agent, tool_manager)
    
    console.print(Panel(
        "[bold blue]🤖 Atomic Investment Planning Agent[/bold blue]\n"
        "Using Atomic Agents framework for structured investment research planning...",
        title="Investment Planning Phase",
        border_style="blue"
    ))
    
    # Step 1: Create atomic planning agent using the factory function
    planning_agent = create_atomic_planning_agent(
        client=instructor_client,
        model=model
    )
    
    # Step 2: Generate plan using atomic planning agent
    planning_input = PlanningAgentInputSchema( # Use the schema from planner_schemas
        investment_query=investment_query,
        research_context=research_context
    )
    
    try:
        planning_result = planning_agent.run(planning_input)
        
        console.print(Panel(
            f"[green]✅ Plan Generated[/green]\n"
            f"[yellow]Steps:[/yellow] {len(planning_result.steps)}\n"
            f"[yellow]Reasoning:[/yellow] {planning_result.reasoning[:100]}...",
            title="Planning Complete",
            border_style="green"
        ))
        
        # Display the generated plan
        console.print("\n[bold cyan]📋 Generated Plan:[/bold cyan]")
        for i, step in enumerate(planning_result.steps, 1):
            console.print(f"  {i}. {step.description}")
        
        console.print(Panel(
            "[bold blue]🚀 Execution Phase[/bold blue]\n"
            "Executing plan using orchestration engine...",
            title="Execution Phase",
            border_style="blue"
        ))
        
        # Step 3: Execute plan using execution orchestrator with direct integration
        execution_orchestrator = ExecutionOrchestrator(orchestrator_core)
        execution_input = ExecutionOrchestratorInputSchema(
            investment_query=investment_query,
            research_context=research_context,
            planning_output=planning_result
        )
        
        execution_result = execution_orchestrator.run(execution_input)
        
        # Step 4: Generate final summary
        final_summary = f"""# Atomic Investment Planning Agent Execution Summary

## Planning Phase
**Reasoning:** {planning_result.reasoning}

## Execution Phase
{execution_result.final_summary}

## Overall Result
- **Success:** {'✅ Yes' if execution_result.success else '❌ No'}
- **Steps Executed:** {len(execution_result.executed_steps)}
- **Tools Used:** {', '.join(set(step.tool_used for step in execution_result.executed_steps))}

## Key Insights
{execution_result.accumulated_knowledge}
"""
        
        # Create a simple plan for the final result with execution results
        simple_plan = SimplePlanSchema( # This schema is already updated with investment_query and research_context
            investment_query=investment_query,
            research_context=research_context,
            steps=planning_result.steps,
            accumulated_knowledge=execution_result.accumulated_knowledge
        )
        
        # Update the simple plan with execution results
        for i, step_result in enumerate(execution_result.executed_steps):
            if i < len(simple_plan.steps):
                simple_plan.steps[i].status = step_result.status
                simple_plan.steps[i].result = step_result.full_result
        
        return PlanningAgentOutputSchema(
            plan=simple_plan,
            summary=final_summary,
            success=execution_result.success
        )
        
    except Exception as e:
        console.print(Panel(
            f"[red]❌ Error in atomic planning: {e}[/red]",
            title="Planning Error",
            border_style="red"
        ))
        
        # Return error result
        error_plan = SimplePlanSchema( # This schema is already updated
            investment_query=investment_query,
            research_context=research_context,
            steps=[],
            accumulated_knowledge=f"Error occurred: {str(e)}"
        )
        
        return PlanningAgentOutputSchema(
            plan=error_plan,
            summary=f"Planning failed with error: {str(e)}",
            success=False
        )


def run_atomic_planning_scenarios(example_data, model: str = "mistral/ministral-8b"):
    """
    Run example investment research scenarios using the atomic planning agent.
    
    Args:
        example_data: List of investment query scenarios
        model: Model name for LLM calls
    """
    console = Console()
    
    for i, scenario in enumerate(example_data, 1):
        console.print(Panel(
            f"[bold blue]Atomic Investment Planning Scenario {i}[/bold blue]\n"
            f"[yellow]Investment Query:[/yellow] {scenario['investment_query']}\n"
            f"[yellow]Research Context:[/yellow] {scenario['research_context']}",
            title="🤖 Atomic Investment Planning Agent",
            border_style="blue"
        ))
        
        try:
            result = process_query_with_atomic_planning(
                scenario["investment_query"],
                scenario["research_context"],
                model
            )
            
            # Display the summary
            console.print(Panel(
                result.summary,
                title="📋 Atomic Investment Planning Execution Summary",
                border_style="green" if result.success else "red"
            ))
            
        except Exception as e:
            console.print(Panel(
                f"[red]Error processing scenario: {e}[/red]",
                title="❌ Atomic Investment Planning Error",
                border_style="red"
            ))
        
        console.print("\n" + "="*80 + "\n")


def main():
    """Main entry point for the atomic planning agent."""
    import sys
    
    # Define example investment research scenarios
    example_investment_queries = [
        {
            "investment_query": "Assess the short-term investment potential of MSFT.",
            "research_context": "Client is looking for a 3-6 month holding period. MSFT recently announced new AI initiatives. Access to latest 10-Q and analyst reports available."
        },
        {
            "investment_query": "Is AAPL overvalued at its current price for a long-term hold (5+ years)?",
            "research_context": "AAPL has seen significant stock price appreciation. Concerns about future growth drivers. Latest 10-K, earnings call transcripts, and competitor analysis needed."
        },
        {
            "investment_query": "Compare the growth prospects of NVDA vs AMD in the AI chip market.",
            "research_context": "Both companies are key players. Need to analyze market share, R&D, partnerships, and financial performance. Access to industry reports and company filings."
        }
    ]
    
    console = Console()
    console.print(Panel(
        "[bold blue]🤖 Atomic Investment Planning Agent[/bold blue]\n"
        "Running example investment research scenarios with atomic agents architecture...\n"
        "[green]✨ Features:[/green]\n"
        "• Structured planning with guaranteed schemas\n"
        "• Separation of planning and execution concerns\n"
        "• Schema-based component chaining\n"
        "• Full transparency and debuggability",
        title="Atomic Investment Planning Agent Executor",
        border_style="blue"
    ))
    
    run_atomic_planning_scenarios(example_investment_queries)


if __name__ == "__main__":
    main()