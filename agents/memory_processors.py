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
    IMPORTANT: Preserves tool call/response pairs to maintain message sequence integrity.
    """
    filtered = []
    i = 0
    
    while i < len(messages):
        message = messages[i]
        
        if isinstance(message, ModelRequest):
            # Keep all user requests and system prompts
            filtered.append(message)
            i += 1
        elif isinstance(message, ModelResponse):
            # Check if this response has tool calls
            has_tool_calls = hasattr(message, 'parts') and any(
                hasattr(part, 'tool_name') for part in message.parts
            )
            
            if has_tool_calls:
                # This is a tool call response - keep it and check for tool responses
                filtered.append(message)
                i += 1
                
                # Look ahead for tool response messages that belong to this tool call
                while i < len(messages):
                    next_message = messages[i]
                    # Check if this is a tool response message
                    if hasattr(next_message, 'role') and getattr(next_message, 'role', None) == 'tool':
                        filtered.append(next_message)
                        i += 1
                    else:
                        break
            else:
                # Regular model response - filter based on content value
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
                i += 1
        else:
            # Handle any other message types (including tool responses)
            # Check if this is a tool response that should be kept with its tool call
            if hasattr(message, 'role') and getattr(message, 'role', None) == 'tool':
                # This is a tool response - keep it (it should follow a tool call)
                filtered.append(message)
            else:
                # Keep other message types to be safe
                filtered.append(message)
            i += 1
    
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


def validate_tool_call_sequences(messages: List[ModelMessage]) -> List[ModelMessage]:
    """Validate and fix tool call/response sequences to prevent API errors.
    
    Ensures that messages with tool calls are properly followed by tool responses.
    Removes orphaned tool responses that don't have preceding tool calls.
    """
    validated = []
    expecting_tool_response = False
    last_tool_call_message = None
    
    for message in messages:
        # Check if this is a model response with tool calls
        if isinstance(message, ModelResponse):
            has_tool_calls = hasattr(message, 'parts') and any(
                hasattr(part, 'tool_name') for part in message.parts
            )
            
            if has_tool_calls:
                validated.append(message)
                expecting_tool_response = True
                last_tool_call_message = message
            else:
                # Regular model response
                validated.append(message)
                expecting_tool_response = False
                last_tool_call_message = None
        
        # Check if this is a tool response message
        elif hasattr(message, 'role') and getattr(message, 'role', None) == 'tool':
            if expecting_tool_response:
                # This tool response follows a tool call - keep it
                validated.append(message)
            else:
                # Orphaned tool response - skip it to avoid API errors
                continue
        
        # All other message types
        else:
            validated.append(message)
            expecting_tool_response = False
            last_tool_call_message = None
    
    return validated


def adaptive_memory_processor(messages: List[ModelMessage]) -> List[ModelMessage]:
    """Adaptive memory processor that combines multiple strategies.
    
    Uses different strategies based on conversation length and content.
    Optimized for research workflows with many tool calls.
    IMPORTANT: Ensures tool call/response sequence integrity.
    """
    # For short conversations, keep everything but validate sequences
    if len(messages) <= 6:
        return validate_tool_call_sequences(messages)
    
    # For medium conversations, filter and trim more aggressively
    if len(messages) <= 12:
        filtered = filter_research_responses(messages)
        contextual = keep_recent_with_context(filtered, max_messages=8)
        return validate_tool_call_sequences(contextual)
    
    # For long conversations (common in research), be more aggressive
    # Filter out low-value responses and keep only essential context
    filtered = filter_research_responses(messages)
    # Keep only the most recent and most important messages
    result = keep_recent_with_context(filtered, max_messages=6)
    
    # Always preserve the first message if it's a system prompt
    if messages and result and messages[0] != result[0]:
        result = [messages[0]] + result[1:]
    
    # Final validation to ensure tool call sequences are intact
    return validate_tool_call_sequences(result)


# Export commonly used processors
__all__ = [
    'summarize_old_research_messages',
    'filter_research_responses', 
    'keep_recent_with_context',
    'validate_tool_call_sequences',
    'adaptive_memory_processor'
]