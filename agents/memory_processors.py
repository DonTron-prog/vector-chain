"""Advanced memory processors for PydanticAI agents with investment research focus."""

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart
from typing import List
import asyncio


# Summary agent for condensing old messages
summary_agent = Agent(
    'openai:gpt-4o-mini',  # Use cheaper model for summarization
    result_type=str,
    system_prompt="""You are a research conversation summarizer for investment analysis.

Summarize conversation history while preserving:
- Key research findings and data points
- Important plan decisions and adaptations
- Critical gaps or issues identified
- Strategic insights and recommendations

Omit:
- Routine tool calls and mundane responses
- Repetitive information
- Low-value conversational elements

Keep summaries concise but information-rich for investment decision making."""
)


async def summarize_old_research_messages(messages: List[ModelMessage]) -> List[ModelMessage]:
    """Summarize older messages to preserve context while reducing token usage.
    
    Keeps recent messages and summarizes older ones using a dedicated summarization agent.
    Designed for investment research conversations.
    """
    if len(messages) <= 6:
        return messages
    
    # Keep the most recent 3 messages
    recent_messages = messages[-3:]
    
    # Summarize the older messages (all but the last 3)
    old_messages = messages[:-3]
    
    try:
        # Create summarization prompt from old messages
        summary_result = await summary_agent.run(
            "Summarize this investment research conversation:",
            message_history=old_messages
        )
        
        # Return summary + recent messages
        return summary_result.new_messages() + recent_messages
    
    except Exception:
        # Fallback: just keep recent messages if summarization fails
        return recent_messages


def filter_research_responses(messages: List[ModelMessage]) -> List[ModelMessage]:
    """Filter out low-value model responses while keeping important requests and findings.
    
    Removes routine acknowledgments but preserves substantive research content.
    """
    filtered = []
    
    for message in messages:
        if isinstance(message, ModelRequest):
            # Keep all user requests and system prompts
            filtered.append(message)
        elif isinstance(message, ModelResponse):
            # Filter model responses based on content value
            if any(part for part in message.parts if isinstance(part, TextPart)):
                text_content = " ".join(
                    part.content for part in message.parts 
                    if isinstance(part, TextPart)
                ).lower()
                
                # Keep responses with research value
                research_keywords = [
                    'analysis', 'findings', 'recommendation', 'financial', 'risk',
                    'opportunity', 'metric', 'valuation', 'growth', 'market',
                    'plan', 'strategy', 'update', 'adapt', 'confidence'
                ]
                
                if any(keyword in text_content for keyword in research_keywords):
                    filtered.append(message)
                elif len(text_content) > 50:  # Keep substantial responses
                    filtered.append(message)
                # Skip short, low-value responses
    
    return filtered


def keep_recent_with_context(messages: List[ModelMessage], max_messages: int = 10) -> List[ModelMessage]:
    """Keep recent messages with intelligent context preservation.
    
    Maintains recent conversation flow while respecting token limits.
    Ensures system prompts and important context are preserved.
    """
    if len(messages) <= max_messages:
        return messages
    
    # Always keep the first message if it's a system prompt
    result = []
    if messages and isinstance(messages[0], ModelRequest):
        result.append(messages[0])
        remaining_messages = messages[1:]
        max_messages -= 1
    else:
        remaining_messages = messages
    
    # Take the most recent messages up to the limit
    if remaining_messages:
        recent = remaining_messages[-max_messages:]
        result.extend(recent)
    
    return result


def adaptive_memory_processor(messages: List[ModelMessage]) -> List[ModelMessage]:
    """Adaptive memory processor that combines multiple strategies.
    
    Uses different strategies based on conversation length and content.
    """
    # For short conversations, keep everything
    if len(messages) <= 8:
        return messages
    
    # For medium conversations, filter and trim
    if len(messages) <= 15:
        filtered = filter_research_responses(messages)
        return keep_recent_with_context(filtered, max_messages=10)
    
    # For long conversations, use aggressive summarization
    # This would typically use the async summarizer, but since processors
    # must be synchronous, we fall back to filtering + trimming
    filtered = filter_research_responses(messages)
    return keep_recent_with_context(filtered, max_messages=8)


# Export commonly used processors
__all__ = [
    'summarize_old_research_messages',
    'filter_research_responses', 
    'keep_recent_with_context',
    'adaptive_memory_processor'
]