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


def get_minimal_planning_context(messages: List[ModelMessage]) -> List[ModelMessage]:
    """Get minimal context for planning agent to avoid memory explosion.
    
    Keeps only system prompt + last 2 successful planning decisions.
    """
    if not messages:
        return []
    
    minimal = []
    
    # Always keep system prompt if present
    if messages and hasattr(messages[0], 'role') and getattr(messages[0], 'role', None) == 'system':
        minimal.append(messages[0])
    
    # Find the last 2 successful planning interactions
    successful_interactions = []
    i = len(messages) - 1
    
    while i >= 0 and len(successful_interactions) < 2:
        message = messages[i]
        
        # Look for user requests (planning evaluations)
        if hasattr(message, 'role') and getattr(message, 'role', None) == 'user':
            content = getattr(message, 'content', '')
            if 'PLAN UPDATE EVALUATION' in content:
                # Found a planning request - collect this interaction
                interaction = [message]  # Start with user request
                
                # Look ahead for the assistant response and successful tool call
                j = i + 1
                while j < len(messages):
                    next_msg = messages[j]
                    interaction.append(next_msg)
                    
                    # Stop after we get the successful tool response
                    if (hasattr(next_msg, 'role') and 
                        getattr(next_msg, 'role', None) == 'tool' and
                        'Final result processed' in getattr(next_msg, 'content', '')):
                        break
                    j += 1
                
                successful_interactions.insert(0, interaction)  # Insert at beginning to maintain order
        
        i -= 1
    
    # Add successful interactions to minimal context
    for interaction in successful_interactions:
        minimal.extend(interaction)
    
    return minimal


def filter_successful_planning_messages(messages: List[ModelMessage]) -> List[ModelMessage]:
    """Filter planning messages to keep only successful results, removing duplicates.
    
    Removes duplicate tool calls and 'Result tool not used' messages.
    """
    filtered = []
    
    for message in messages:
        # Keep user requests and assistant responses
        if hasattr(message, 'role'):
            role = getattr(message, 'role', None)
            if role in ['user', 'assistant']:
                filtered.append(message)
            elif role == 'tool':
                content = getattr(message, 'content', '')
                # Only keep successful tool responses, skip duplicates
                if 'Final result processed' in content:
                    filtered.append(message)
                # Skip "Result tool not used" messages
        else:
            # Keep other message types to be safe
            filtered.append(message)
    
    return filtered


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

Provide clear reasoning for your decision and maintain focus on investment objectives.

IMPORTANT: Make only ONE tool call per evaluation. Do not make duplicate calls."""
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
    
    # Simplified approach: Use minimal context to avoid memory explosion
    # Only keep essential context - last 2 successful plan updates
    minimal_history = None
    if message_history:
        minimal_history = get_minimal_planning_context(message_history)
    
    result = await adaptive_planning_agent.run(prompt, message_history=minimal_history)
    
    # Build lean message history - only keep essential messages
    if message_history is None:
        updated_history = result.all_messages()
    else:
        # Add only the new successful planning messages, filter out duplicates
        new_messages = filter_successful_planning_messages(result.new_messages())
        updated_history = message_history + new_messages
    
    return result.data, updated_history