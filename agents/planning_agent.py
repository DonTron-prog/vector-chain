"""Investment research planning agent using pydantic-ai."""

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from models.schemas import ResearchPlan, PlanUpdateResponse, PlanUpdateRequest
from config import get_openai_model
from typing import List, Optional
from .memory_processors import adaptive_memory_processor

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


def keep_recent_planning_messages(messages: List[ModelMessage]) -> List[ModelMessage]:
    """Keep only the last 8 messages to manage token usage while preserving context."""
    return messages[-8:] if len(messages) > 8 else messages


adaptive_planning_agent = Agent(
    openai_model,
    result_type=PlanUpdateResponse,
    system_prompt="""You are an adaptive investment research planner with memory.

Your role is to evaluate research execution feedback and decide whether to update the research plan.

EVALUATION CRITERIA:
- If findings_quality < 0.6, consider plan updates
- If data_gaps are significant, adjust steps to fill gaps  
- If unexpected_findings are valuable, incorporate them
- If confidence_level < 0.5, reassess approach

DECISION FACTORS:
- Quality of current findings
- Significance of data gaps
- Value of unexpected discoveries
- Confidence in current direction
- Remaining research budget/time

UPDATE GUIDELINES:
1. Modify existing steps to address gaps
2. Add new steps for unexpected opportunities
3. Reorder steps based on new priorities
4. Remove redundant or low-value steps

Provide clear reasoning for your decision and maintain focus on investment objectives."""
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


async def evaluate_plan_update(
    update_request: PlanUpdateRequest,
    message_history: Optional[List[ModelMessage]] = None
) -> tuple[PlanUpdateResponse, List[ModelMessage]]:
    """Evaluate whether research plan needs updating based on execution feedback.
    
    Args:
        update_request: Request containing feedback and current plan state
        message_history: Previous planning conversation history for context
        
    Returns:
        Tuple of (PlanUpdateResponse, updated_message_history)
    """
    feedback = update_request.feedback
    
    prompt = f"""PLAN UPDATE EVALUATION

Current Step: {update_request.current_step}
Step Completed: {feedback.step_completed}

EXECUTION FEEDBACK:
- Findings Quality: {feedback.findings_quality:.2f}/1.0
- Confidence Level: {feedback.confidence_level:.2f}/1.0
- Data Gaps: {feedback.data_gaps}
- Unexpected Findings: {feedback.unexpected_findings}
- Suggested Adjustments: {feedback.suggested_adjustments}

REMAINING PLAN STEPS:
{[step.model_dump() for step in update_request.remaining_steps]}

DECISION REQUIRED: Should the research plan be updated based on this feedback?

If updating, provide new/modified steps that address the feedback while maintaining research objectives."""
    
    # Apply memory processing if history is provided
    processed_history = None
    if message_history:
        processed_history = adaptive_memory_processor(message_history)
    
    result = await adaptive_planning_agent.run(prompt, message_history=processed_history)
    
    # Return both the response and the updated message history
    updated_history = result.all_messages() if message_history is None else message_history + result.new_messages()
    return result.data, updated_history