"""Simplified schemas for investment research planning."""

from typing import List, Dict, Any
from pydantic import Field
from atomic_agents.lib.base.base_io_schema import BaseIOSchema


class InvestmentQuery(BaseIOSchema):
    """Input schema for investment research."""
    
    query: str = Field(..., description="The investment query to research")
    context: str = Field(default="", description="Contextual information for the research")


class PlanStep(BaseIOSchema):
    """Individual research step."""
    
    description: str = Field(..., description="Natural language description of the step")
    status: str = Field(default="pending", description="Current status: pending, completed, failed")
    result: Dict[str, Any] = Field(default_factory=dict, description="Result data from execution")


class ResearchPlan(BaseIOSchema):
    """Complete research plan with execution capability."""
    
    query: str = Field(..., description="The original investment query")
    context: str = Field(..., description="Research context information")
    steps: List[PlanStep] = Field(..., description="Ordered steps in the research plan")
    reasoning: str = Field(..., description="Explanation of the planning approach")
    status: str = Field(default="pending", description="Overall plan status")
    accumulated_knowledge: str = Field(default="", description="Accumulated findings")
    success: bool = Field(default=False, description="Whether the research was successful")