"""Investment research planning agent using pydantic-ai."""

from pydantic_ai import Agent
from models.schemas import ResearchPlan
from config import get_openai_model

# Configure OpenRouter
openai_model = get_openai_model()

planning_agent = Agent(
    openai_model,
    result_type=ResearchPlan,
    system_prompt="""You are an expert investment research planner.

Create 2-4 logical research steps following investment methodology:
1. Data gathering (financials, market position, recent developments)
2. Analysis (competitive landscape, growth drivers, business model)  
3. Valuation (metrics, comparisons, fair value assessment)
4. Investment recommendation (risk/return profile, recommendation)

Consider the client's context and investment objectives.
Focus on actionable, specific steps that build upon each other.
Each step should have a clear focus area and expected outcome.

Your reasoning should explain why these specific steps are optimal for the query."""
)


async def create_research_plan(query: str, context: str = "") -> ResearchPlan:
    """Create a structured investment research plan.
    
    Args:
        query: The investment question to research
        context: Additional context about the client or situation
        
    Returns:
        ResearchPlan: Structured plan with 2-4 logical steps
    """
    prompt = f"""Investment Query: {query}

Context: {context}

Create a research plan to thoroughly investigate this investment opportunity."""
    
    result = await planning_agent.run(prompt)
    return result.data