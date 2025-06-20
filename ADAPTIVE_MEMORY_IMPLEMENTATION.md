# Adaptive Memory Implementation for PydanticAI Investment Research

## Overview

Successfully implemented adaptive memory capabilities for the investment research planning agent using PydanticAI's native message history features. This enables dynamic plan adaptation based on execution feedback while maintaining conversation context across iterations.

## Key Features Implemented

### 1. Enhanced Data Models (`models/schemas.py`)

#### New Models Added:
- **`ExecutionFeedback`**: Structured feedback from research execution
  - `findings_quality` (0-1): Quality assessment of research findings
  - `data_gaps`: List of identified missing information
  - `unexpected_findings`: Valuable discoveries not anticipated
  - `suggested_adjustments`: Recommended plan modifications
  - `confidence_level` (0-1): Confidence in current research direction

- **`PlanUpdateRequest`**: Request structure for plan adaptation
- **`PlanUpdateResponse`**: Response with update decision and reasoning
- **`AdaptivePlan`**: Tracks plan evolution over time

### 2. Memory-Enabled Planning Agent (`agents/planning_agent.py`)

#### Features:
- **`adaptive_planning_agent`**: New agent specialized for plan adaptation
- **Memory Management**: Processes message history to maintain context
- **`evaluate_plan_update()`**: Evaluates feedback and decides on plan changes
- **Structured Decision Making**: Clear criteria for when to update plans

#### Decision Criteria:
- Findings quality < 0.6 → Consider plan updates
- Confidence level < 0.5 → Reassess approach
- Significant data gaps → Adjust steps to fill gaps
- Valuable unexpected findings → Incorporate into plan

### 3. Feedback Generation (`agents/research_agent.py`)

#### New Components:
- **`feedback_agent`**: Specialized agent for execution evaluation
- **`generate_execution_feedback()`**: Creates structured feedback
- **Quality Assessment**: Evaluates findings comprehensiveness
- **Gap Analysis**: Identifies missing information
- **Strategic Recommendations**: Suggests concrete improvements

### 4. Advanced Memory Processors (`agents/memory_processors.py`)

#### Memory Management Strategies:
- **`adaptive_memory_processor()`**: Dynamic memory management
- **`filter_research_responses()`**: Removes low-value messages
- **`keep_recent_with_context()`**: Preserves important context
- **Token Optimization**: Maintains conversation flow within limits

#### Memory Processing Logic:
- **Short conversations (≤8 messages)**: Keep everything
- **Medium conversations (≤15 messages)**: Filter and trim
- **Long conversations (>15 messages)**: Aggressive summarization

### 5. Adaptive Research Loop (`main.py`)

#### New Function: `adaptive_research_investment()`

**Process Flow:**
1. **Initial Planning**: Create structured research plan
2. **Step-by-Step Execution**: Execute each research step individually
3. **Feedback Generation**: Evaluate each step's findings
4. **Adaptation Decision**: Determine if plan needs updating
5. **Plan Update**: Modify steps based on feedback (if needed)
6. **Memory Management**: Maintain conversation context
7. **Iteration**: Continue until research complete

#### Adaptive Loop Features:
- **Dynamic Plan Updates**: Plans evolve based on discovered information
- **Memory Persistence**: Context maintained across iterations
- **Quality Tracking**: Monitor findings quality and confidence
- **Adaptation Limits**: Prevent infinite adaptation loops
- **Rich Feedback**: Detailed console output showing adaptations

## Technical Implementation

### Memory Management with PydanticAI

Since the current version (0.0.14) doesn't support `history_processors` parameter, we implemented manual memory management:

```python
# Apply memory processing before passing to agent
processed_history = adaptive_memory_processor(message_history)
result = await agent.run(prompt, message_history=processed_history)

# Update conversation history
updated_history = message_history + result.new_messages()
```

### Feedback-Driven Adaptation

```python
# Generate feedback after each step
feedback = await generate_execution_feedback(
    step_description=current_step.description,
    findings=step_findings,
    original_expectations=current_step.expected_outcome,
    deps=deps
)

# Evaluate need for plan update
if (feedback.findings_quality < 0.6 or 
    feedback.confidence_level < 0.5 or 
    feedback.suggested_adjustments):
    
    update_response, planning_messages = await evaluate_plan_update(
        update_request, message_history=planning_messages
    )
```

### Memory Processing Strategies

```python
def adaptive_memory_processor(messages: List[ModelMessage]) -> List[ModelMessage]:
    """Adaptive memory processor that combines multiple strategies."""
    if len(messages) <= 8:
        return messages  # Keep short conversations intact
    elif len(messages) <= 15:
        # Filter and trim medium conversations
        filtered = filter_research_responses(messages)
        return keep_recent_with_context(filtered, max_messages=10)
    else:
        # Aggressive processing for long conversations
        filtered = filter_research_responses(messages)
        return keep_recent_with_context(filtered, max_messages=8)
```

## Benefits Achieved

### 1. **Dynamic Adaptation**
- Plans evolve based on actual findings rather than static assumptions
- Research adapts to unexpected discoveries and data gaps
- Quality-driven decision making for plan modifications

### 2. **Intelligent Memory**
- Maintains conversation context across multiple planning iterations
- Token-efficient memory management prevents context overflow
- Preserves important research insights while filtering noise

### 3. **Structured Feedback**
- Type-safe feedback models ensure consistent evaluation
- Clear criteria for adaptation decisions
- Actionable recommendations for plan improvements

### 4. **Enhanced User Experience**
- Rich console output showing adaptation reasoning
- Transparency in planning decisions
- Progress tracking across research iterations

### 5. **Robust Architecture**
- Clean separation of concerns between planning and execution
- Extensible feedback and memory processing systems
- Backward compatibility with existing research workflows

## Testing and Validation

### Test Results:
- ✅ **Schema Validation**: All new models work correctly
- ✅ **Planning Agent**: Successfully creates and adapts plans
- ✅ **Memory Processing**: Proper message history management
- ✅ **Feedback Generation**: Structured evaluation of research steps
- ✅ **Integration**: Seamless integration with existing codebase

### Demo Capabilities:
- Successfully demonstrated plan adaptation based on feedback
- Showed memory management across planning iterations
- Validated reasoning and decision-making transparency

## Usage Examples

### Basic Adaptive Research:
```python
analysis = await adaptive_research_investment(
    query="Should I invest in AAPL for long-term growth?",
    context="5-year horizon, moderate risk tolerance",
    max_adaptations=3
)
```

### Manual Feedback Testing:
```python
feedback = ExecutionFeedback(
    step_completed="Financial data collection",
    findings_quality=0.7,
    data_gaps=["Missing competitor analysis"],
    confidence_level=0.6
)

update_response, history = await evaluate_plan_update(
    PlanUpdateRequest(current_step=1, feedback=feedback, remaining_steps=steps)
)
```

## Future Enhancements

1. **Persistent Memory**: Store conversation history across sessions
2. **Advanced Summarization**: Use dedicated LLM for conversation summarization
3. **Learning from History**: Learn from past adaptations to improve future planning
4. **Multi-Agent Coordination**: Coordinate memory across multiple research agents
5. **Performance Metrics**: Track adaptation effectiveness over time

## Conclusion

The adaptive memory implementation successfully transforms the static planning system into an intelligent, self-improving research framework. The planning agent now maintains context, learns from execution feedback, and dynamically adapts its strategy to achieve better research outcomes.

This implementation leverages PydanticAI's native message history capabilities while adding sophisticated memory management and feedback-driven adaptation, creating a robust foundation for advanced AI research workflows.