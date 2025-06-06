"""Core orchestrator functionality for reusable components."""

from typing import Dict, Any, Tuple, Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from pydantic import Field

from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from orchestration_engine.schemas.orchestrator_schemas import (
    OrchestratorInputSchema,
    OrchestratorOutputSchema,
    FinalAnswerSchema
)
from orchestration_engine.utils.tool_manager import ToolManager
from orchestration_engine.utils.interfaces import ExecutionContext, PlanningCapableOrchestrator
from orchestration_engine.utils.context_utils import CurrentDateProvider

from orchestration_engine.tools.searxng_search import SearxNGSearchToolConfig
from orchestration_engine.tools.calculator import CalculatorToolConfig
from orchestration_engine.tools.rag_search import RAGSearchToolConfig
from orchestration_engine.tools.deep_research import DeepResearchToolConfig


#######################
# AGENT CONFIGURATION #
#######################
class OrchestratorAgentConfig(BaseAgentConfig):
    """Configuration for the Orchestrator Agent."""

    searxng_config: SearxNGSearchToolConfig
    calculator_config: CalculatorToolConfig
    rag_config: RAGSearchToolConfig
    deep_research_config: DeepResearchToolConfig


###########################
# ORCHESTRATOR FUNCTIONS  #
###########################


class OrchestratorCore(PlanningCapableOrchestrator):
    """Core orchestrator functionality that can be used by planning agents."""
    def __init__(self, agent, tool_manager: ToolManager, console: Optional[Console] = None):
        """Initialize the orchestrator core.
        
        Args:
            agent: The orchestrator agent instance
            tool_manager: Tool manager for executing tools
            console: Rich console for output (optional)
        """
        self.agent = agent
        self.tool_manager = tool_manager
        self.console = console or Console()
    
    def execute_orchestration_step(self, input_schema: OrchestratorInputSchema, 
                                 reset_memory: bool = True) -> Tuple[OrchestratorOutputSchema, Any]:
        """Execute a single orchestration step.
        
        Args:
            input_schema: Input schema with alert and context
            reset_memory: Whether to reset agent memory after execution
            
        Returns:
            Tuple of (orchestrator_output, tool_response)
        """
        # Execute orchestrator to get tool selection
        orchestrator_output = self.agent.run(input_schema)
        
        # Execute the selected tool
        tool_response = self.tool_manager.execute_tool(orchestrator_output)
        
        # Reset memory if requested
        if reset_memory:
            self.reset_agent_memory()
            
        return orchestrator_output, tool_response
    
    def execute_with_context(self, execution_context: ExecutionContext) -> Dict[str, Any]:
        """Execute orchestration with planning context.

        Args:
            execution_context: Context containing query, research context, and accumulated knowledge

        Returns:
            Dict containing orchestrator_output and tool_response
        """
        # Create input schema from execution context
        input_schema = OrchestratorInputSchema(
            investment_query=execution_context.investment_query,
            research_context=execution_context.research_context
        )
        
        # Execute the orchestration step without resetting memory (planning agent manages this)
        orchestrator_output, tool_response = self.execute_orchestration_step(
            input_schema, reset_memory=False
        )
        
        return {
            "orchestrator_output": orchestrator_output,
            "tool_response": tool_response,
            "step_id": execution_context.step_id,
            "step_description": execution_context.step_description
        }
    
    def get_available_tools(self) -> list[str]:
        """Get list of available tool names."""
        return self.tool_manager.get_available_tools()
    
    def generate_final_answer(self, input_schema: OrchestratorInputSchema, tool_response: Any) -> FinalAnswerSchema:
        """Generate a final answer based on the tool's output.
        
        Args:
            input_schema: Original input schema
            tool_response: Response from tool execution
            
        Returns:
            Final answer schema
        """
        # Store original output schema
        original_schema = self.agent.output_schema
        
        try:
            # Temporarily change output schema to FinalAnswerSchema
            self.agent.output_schema = FinalAnswerSchema
            
            # Add tool response to memory
            self.agent.memory.add_message("system", tool_response)
            
            # Generate final answer
            final_answer_obj = self.agent.run(input_schema)
            
            return final_answer_obj
            
        finally:
            # Restore original output schema
            self.agent.output_schema = original_schema
    
    def reset_agent_memory(self):
        """Reset the agent's memory for the next interaction."""
        self.agent.memory = AgentMemory()
    
    def process_single_query(self, query_data: Dict[str, str],
                           generate_final_answer_flag: bool = False,
                           reset_memory: bool = True,
                           verbose: bool = True) -> Dict[str, Any]:
        """Process a single investment research query through the complete orchestration pipeline.
        
        Args:
            query_data: Dictionary with 'query' and 'context' keys
            generate_final_answer_flag: Whether to generate a final answer
            reset_memory: Whether to reset memory after processing
            verbose: Whether to print detailed output
            
        Returns:
            Dictionary containing all results from the processing
        """
        print("Here: Processing single query with orchestrator core")
        if verbose:
            self.console.print(Panel(
                f"[bold cyan]Investment Query:[/bold cyan] {query_data['query']}\n"
                f"[bold cyan]Research Context:[/bold cyan] {query_data.get('context', 'N/A')}", # Use .get for safety and correct key
                expand=False
            ))
        
        # Prepare input schema
        input_schema = OrchestratorInputSchema(
            investment_query=query_data["query"], # Corrected key
            research_context=query_data.get("context") # Corrected key and use .get for safety
        )
        
        # Execute orchestration step
        orchestrator_output, tool_response = self.execute_orchestration_step(
            input_schema, reset_memory=False
        )
        
        if verbose:
            self.console.print("\n[bold magenta]Orchestrator Output:[/bold magenta]")
            orchestrator_syntax = Syntax(
                str(orchestrator_output.model_dump_json(indent=2)),
                "json",
                theme="monokai",
                line_numbers=True
            )
            self.console.print(orchestrator_syntax)
            
            self.console.print("\n[bold green]Tool Output:[/bold green]")
            output_syntax = Syntax(
                str(tool_response.model_dump_json(indent=2)),
                "json",
                theme="monokai",
                line_numbers=True
            )
            self.console.print(output_syntax)
            
            self.console.print("\n" + "-" * 80 + "\n")
        
        results = {
            "orchestrator_output": orchestrator_output,
            "tool_response": tool_response,
            "final_answer": None
        }
        
        # Handle final answer generation based on tool type
        if generate_final_answer_flag:
            if orchestrator_output.tool == "deep-research":
                # Deep research already provides comprehensive answer, no need to re-analyze
                if verbose:
                    self.console.print(f"\n[bold blue]Research Answer:[/bold blue] {tool_response.answer}")
                results["final_answer"] = tool_response.answer
            else:
                # Other tools return raw data that needs final answer generation
                final_answer_obj = self.generate_final_answer(input_schema, tool_response)
                if verbose:
                    self.console.print(f"\n[bold blue]Final Answer:[/bold blue] {final_answer_obj.final_answer}")
                results["final_answer"] = final_answer_obj.final_answer
        
        # Reset memory if requested
        if reset_memory:
            self.reset_agent_memory()
        
        return results