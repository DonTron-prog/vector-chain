"""Simplified investment research agent using Atomic Agents framework."""

import openai
import instructor
from typing import List
from pydantic import Field
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from orchestration_engine import ConfigManager, ToolManager, OrchestratorCore, create_orchestrator_agent
from orchestration_engine.utils.interfaces import ExecutionContext
from orchestration_engine.utils.context_utils import ContextAccumulator
from controllers.planning_agent.schemas import InvestmentQuery, PlanStep, ResearchPlan


class PlanningOutputSchema(BaseIOSchema):
    """Output schema for the planning agent (internal use only)."""
    
    steps: List[PlanStep] = Field(
        ..., 
        description="Generated plan steps in logical order (2-4 steps)",
        min_items=2,
        max_items=4
    )
    reasoning: str = Field(..., description="Explanation of the planning approach and rationale")


def create_planning_agent(client: instructor.Instructor, model: str = "gpt-4") -> BaseAgent:
    """Create an investment research planning agent."""
    
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
            input_schema=InvestmentQuery,
            output_schema=PlanningOutputSchema,
            max_retries=3,
            temperature=0.1
        )
    )


def execute_research_plan(plan: ResearchPlan, orchestrator_core: OrchestratorCore) -> ResearchPlan:
    """Execute a research plan step by step using the orchestrator."""
    
    print(f"🚀 Starting execution of plan with {len(plan.steps)} steps")
    
    for step_index, step in enumerate(plan.steps):
        print(f"\n🔄 Executing Step {step_index + 1}: {step.description}")
        
        try:
            # Create execution context for this step
            execution_context = ExecutionContext(
                investment_query=plan.query,
                research_context=plan.context,
                accumulated_knowledge=plan.accumulated_knowledge,
                step_id=f"step_{step_index + 1}",
                step_description=step.description
            )
            
            # Execute step using orchestrator
            result = orchestrator_core.execute_with_context(execution_context)
            
            # Extract orchestrator output and tool response
            orchestrator_output = result.get('orchestrator_output')
            tool_response = result.get('tool_response')
            
            # Get tool name from orchestrator output
            tool_name = orchestrator_output.tool if orchestrator_output else 'unknown'
            
            # Update step with results
            step.status = "completed"
            step.result = result
            
            # Update accumulated knowledge
            step_summary = ContextAccumulator.summarize_step_result(
                step.description,
                tool_response,
                tool_name
            )
            
            plan.accumulated_knowledge = ContextAccumulator.merge_contexts(
                plan.accumulated_knowledge,
                step_summary
            )
            
            print(f"✅ Step {step_index + 1} completed using {tool_name}")
            print(f"   Summary: {step_summary[:100]}...")
            
            # Check if we got a final answer
            if tool_name == 'final_answer':
                print("🎯 Final answer reached, stopping execution")
                break
                
        except Exception as e:
            print(f"❌ Step {step_index + 1} failed: {e}")
            step.status = "failed"
            step.result = {"error": str(e)}
            plan.success = False
            plan.status = "failed"
            return plan
    
    # Mark plan as completed
    plan.status = "completed"
    plan.success = True
    return plan


def research_investment(query: str, context: str = "", model: str = "mistral/ministral-8b") -> ResearchPlan:
    """
    Complete investment research workflow.
    
    Args:
        query: The investment query to research
        context: Contextual information for the research
        model: Model name for LLM calls
        
    Returns:
        ResearchPlan: Complete research plan with execution results
    """
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
    
    print(f"🤖 Starting investment research for: {query}")
    
    try:
        # 1. Create planning agent
        planning_agent = create_planning_agent(instructor_client, model)
        
        # 2. Generate plan
        planning_input = InvestmentQuery(query=query, context=context)
        planning_result = planning_agent.run(planning_input)
        
        # 3. Create research plan
        plan = ResearchPlan(
            query=query,
            context=context,
            steps=planning_result.steps,
            reasoning=planning_result.reasoning,
            accumulated_knowledge=f"Planning reasoning: {planning_result.reasoning}"
        )
        
        print(f"✅ Plan generated with {len(plan.steps)} steps")
        for i, step in enumerate(plan.steps, 1):
            print(f"  {i}. {step.description}")
        
        # 4. Execute the plan
        plan = execute_research_plan(plan, orchestrator_core)
        
        print(f"\n🎯 Research {'completed successfully' if plan.success else 'failed'}")
        return plan
        
    except Exception as e:
        print(f"❌ Research failed: {e}")
        return ResearchPlan(
            query=query,
            context=context,
            steps=[],
            reasoning=f"Research failed with error: {str(e)}",
            status="failed",
            success=False,
            accumulated_knowledge=f"Error occurred: {str(e)}"
        )


# Example usage
if __name__ == "__main__":
    from rich.console import Console
    
    console = Console()
    
    # Test scenarios
    test_queries = [
        {
            "query": "Should I invest in AAPL for long-term growth?",
            "context": "AAPL recently launched new products. Market sentiment is mixed."
        },
        {
            "query": "Assess MSFT's short-term investment potential",
            "context": "Client looking for 3-6 month holding period. Recent AI announcements."
        }
    ]
    
    for scenario in test_queries:
        console.print(f"\n[bold blue]Testing: {scenario['query']}[/bold blue]")
        
        result = research_investment(
            query=scenario["query"],
            context=scenario["context"]
        )
        
        console.print(f"[green]Success: {result.success}[/green]")
        console.print(f"[yellow]Steps: {len(result.steps)}[/yellow]")
        console.print(f"[cyan]Knowledge: {result.accumulated_knowledge[:100]}...[/cyan]")