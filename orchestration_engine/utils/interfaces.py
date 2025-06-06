"""Interfaces and abstractions for planning agent compatibility."""
"""This file serves as a bridge between planning agents and orchestrators"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ExecutionContext:
    """Context object for passing state between investment research steps."""
    
    investment_query: str
    research_context: str
    accumulated_knowledge: str = ""
    step_id: Optional[str] = None
    step_description: Optional[str] = None


class PlanningCapableOrchestrator(ABC):
    """Interface that orchestrator can implement for planning agent compatibility."""
    
    @abstractmethod
    def execute_with_context(self, execution_context: ExecutionContext) -> Dict[str, Any]:
        """Execute orchestration with planning context.
        
        Args:
            execution_context: Context containing investment query, research context, and accumulated knowledge
            
        Returns:
            Dict containing orchestrator_output and tool_response
        """
        pass
    
    @abstractmethod
    def get_available_tools(self) -> list[str]:
        """Get list of available tool names."""
        pass