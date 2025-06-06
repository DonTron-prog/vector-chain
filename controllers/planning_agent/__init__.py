"""Investment Research Planning Agent - Simplified architecture using Atomic Agents framework."""

# Simplified components
from .investment_agent import (
    research_investment,
    create_planning_agent,
    execute_research_plan
)

# Simplified schemas
from .schemas import (
    InvestmentQuery,
    PlanStep,
    ResearchPlan
)

__all__ = [
    # Main functions
    'research_investment',
    'create_planning_agent', 
    'execute_research_plan',
    
    # Schemas
    'InvestmentQuery',
    'PlanStep',
    'ResearchPlan'
]