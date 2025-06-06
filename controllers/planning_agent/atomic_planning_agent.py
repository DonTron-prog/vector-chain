"""Atomic Planning Agent using Atomic Agents framework."""

from typing import List
from pydantic import Field
import instructor
import openai
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from controllers.planning_agent.planner_schemas import PlanStepSchema, PlanningAgentInputSchema


class AtomicPlanningOutputSchema(BaseIOSchema):
    """Output schema for the Atomic Planning Agent."""
    
    steps: List[PlanStepSchema] = Field(
        ..., 
        description="Generated plan steps in logical order (3-5 steps)",
        min_items=2,
        max_items=4
    )
    reasoning: str = Field(..., description="Explanation of the planning approach and rationale")


def create_atomic_planning_agent(client: instructor.Instructor, model: str = "gpt-4") -> BaseAgent:
    """
    Factory function to create an Atomic Planning Agent with a shared client.
    
    Args:
        client: Pre-configured instructor-wrapped OpenAI client
        model: Model name for LLM calls
        
    Returns:
        BaseAgent: Configured planning agent
    """
    return BaseAgent(
        BaseAgentConfig(
            client=client,
            model=model,
            system_prompt_generator=SystemPromptGenerator(
                background=[
                    "You are an expert investment research planning agent.",
                    "You specialize in creating structured, actionable investment research plans.",
                    "You analyze investment queries and research context to generate logical step-by-step research plans.",
                    "Your plans follow investment research best practices: data gathering → financial analysis → valuation → risk assessment → recommendation."
                ],
                steps=[
                    "1. Analyze the investment query and research context to understand the core research question and available information.",
                    "2. Identify key information to gather (e.g., financial statements, industry reports, market data, news).",
                    "3. Plan steps for fundamental analysis (e.g., ratio analysis, trend analysis, competitive landscape).",
                    "4. Outline steps for valuation (e.g., DCF, comparables, precedent transactions) if applicable.",
                    "5. Define steps for risk assessment and formulating a final recommendation or outlook.",
                    "6. Structure the plan as 2-4 clear, actionable steps in logical sequence."
                ],
                output_instructions=[
                    "Generate exactly 2-4 steps in logical order following a data gathering → analysis → valuation/synthesis → recommendation flow.",
                    "Each step description should be specific, actionable, and focused on a single research objective.",
                    "Start with understanding the query and gathering necessary data.",
                    "Progress through analysis of the company/asset, its financials, and market position.",
                    "End with steps to synthesize findings, assess risks, and form a conclusion or recommendation.",
                    "Provide clear reasoning for your overall planning approach.",
                    "Consider the specific company, sector, and type of investment query."
                ]
            ),
            input_schema=PlanningAgentInputSchema, # Use schema from planner_schemas
            output_schema=AtomicPlanningOutputSchema,
            max_retries=3,
            temperature=0.1  # Low temperature for consistent planning
        )
    )


# Example usage
if __name__ == "__main__":
    import os
    from rich.console import Console
    
    console = Console()
    
    # Create a shared client
    shared_client = instructor.from_openai(openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENAI_API_KEY")))

    # Create agent using the factory function
    agent = create_atomic_planning_agent(
        client=shared_client,
        model="gpt-4"
    )
    
    # Example input
    test_input = PlanningAgentInputSchema( # Use schema from planner_schemas
        investment_query="Should I invest in AAPL stock for long-term growth?",
        research_context="AAPL recently launched a new product line. Current market sentiment is mixed. I have access to their latest 10-K and analyst reports."
    )
    
    # Run planning
    try:
        result = agent.run(test_input)
        
        console.print("[bold blue]Generated Plan:[/bold blue]")
        for i, step in enumerate(result.steps, 1):
            console.print(f"{i}. {step.description}")
        
        console.print(f"\n[bold green]Reasoning:[/bold green] {result.reasoning}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")