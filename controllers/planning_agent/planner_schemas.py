"""Schemas for the Planning Agent."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import Field
from atomic_agents.lib.base.base_io_schema import BaseIOSchema


class PlanStepSchema(BaseIOSchema):
    """Schema for individual planning steps."""
    
    description: str = Field(..., description="Natural language description of what this step should accomplish")
    status: str = Field(default="pending", description="Current status: pending, completed, failed")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Result data from step execution")


class SimplePlanSchema(BaseIOSchema):
    """Schema for the simple planning agent's plan."""
    
    investment_query: str = Field(..., description="The original investment query")
    research_context: str = Field(..., description="Contextual information for the research")
    steps: List[PlanStepSchema] = Field(..., description="Ordered list of plan steps")
    current_step_index: int = Field(default=0, description="Index of currently executing step")
    accumulated_knowledge: str = Field(default="", description="Running summary of findings from completed steps")
    created_at: datetime = Field(default_factory=datetime.now, description="When the plan was created")


class PlanningAgentInputSchema(BaseIOSchema):
    """Input schema for the Planning Agent."""
    
    investment_query: str = Field(..., description="The investment query to create a plan for")
    research_context: str = Field(..., description="Contextual information for the research")


class PlanningAgentOutputSchema(BaseIOSchema):
    """Output schema for the Planning Agent execution summary."""
    
    plan: SimplePlanSchema = Field(..., description="The executed plan with all steps and results")
    summary: str = Field(..., description="Human-readable summary of the planning execution")
    success: bool = Field(..., description="Whether the planning execution was successful")