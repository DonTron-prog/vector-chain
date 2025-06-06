# Investment Research Planning Agent - Simplified Architecture

This module provides a streamlined implementation for investment research planning and execution using the Atomic Agents framework. The complex multi-component architecture has been simplified into a clean, easy-to-understand system with a single entry point.

## Architecture Overview

### Simplified Architecture for Investment Research
- **Single Entry Point**: [`research_investment()`](investment_agent.py) - Complete investment research workflow in one function
- **Schemas**: [`schemas.py`](schemas.py) - Three clean, focused schemas for the entire workflow
- **Benefits**: Simpler, more maintainable, easier to test, with full compatibility with the existing orchestrator

## Quick Start

### Using the Simplified Investment Research Agent

```python
from controllers.planning_agent import research_investment

# Simple one-line usage
result = research_investment(
    query="Should I invest in AAPL for long-term growth?",
    context="AAPL recently launched new products. Market sentiment is mixed."
)

print(f"Success: {result.success}")
print(f"Steps: {len(result.steps)}")
print(f"Knowledge: {result.accumulated_knowledge}")
```

## File Structure

```
controllers/planning_agent/
├── README.md                     # This file
├── SIMPLIFICATION_SUMMARY.md     # Documentation of the simplification process
├── __init__.py                   # Module exports
├── schemas.py                    # 3 simple schemas
├── investment_agent.py           # Unified agent + executor
└── test_simplified.py            # Test suite
```

## Key Components

### 1. Simplified Schemas

**Purpose**: Provide clean, focused data structures for the entire workflow.

**Schemas** (from `schemas.py`):
```python
class InvestmentQuery(BaseIOSchema):
    query: str
    context: str = ""

class PlanStep(BaseIOSchema):
    description: str
    status: str = "pending"
    result: Dict[str, Any] = {}

class ResearchPlan(BaseIOSchema):
    query: str
    context: str
    steps: List[PlanStep]
    reasoning: str
    status: str = "pending"
    accumulated_knowledge: str = ""
    success: bool = False
```

### 2. Unified Research Function

**Purpose**: Provide a single entry point for the complete investment research workflow.

**Function** (from `investment_agent.py`):
```python
def research_investment(query: str, context: str = "", model: str = "mistral/ministral-8b") -> ResearchPlan:
    """Complete investment research workflow."""
    # 1. Generate plan
    # 2. Execute steps
    # 3. Return results
```

### 3. Helper Functions

The `investment_agent.py` file also contains two helper functions that are used by the main `research_investment()` function:

- `create_planning_agent()`: Creates an investment research planning agent
- `execute_research_plan()`: Executes a research plan step by step using the orchestrator

## Running Examples

### Test the Simplified Implementation

```bash
# Run the simplified test suite
python controllers/planning_agent/test_simplified.py
```

## Benefits of the Simplified Approach

### 🔍 **Clarity**
- **3 schemas instead of 7+** - Much simpler to understand
- **Single entry point** - One function instead of multiple components
- **Self-contained tracking** - `ResearchPlan` holds everything in one place

### 🧪 **Testability**
- **Easier testing** - Test one workflow instead of multiple components
- **Cleaner imports** - Less complexity in test setup
- **Fewer moving parts** - Reduced surface area for bugs

### 🐛 **Debuggability**
- **Simplified flow** - Easier to follow the execution path
- **Consolidated logic** - All code in one place
- **Clearer state management** - Research plan tracks all state

### 🔧 **Maintainability**
- **Reduced code duplication** - No overlapping schemas
- **Fewer files** - Less to maintain and update
- **Clearer responsibilities** - Each schema has a specific purpose

### 📊 **Reliability**
- **Full orchestrator compatibility** - Works with existing infrastructure
- **Consistent terminology** - Investment research focus throughout
- **Simplified error handling** - Centralized in one function

## Configuration

### Environment Variables

```bash
# Required for planning agent
export OPENAI_API_KEY="your-openai-api-key"

# Optional model selection
export PLANNING_MODEL="gpt-4"  # Default: gpt-4
```

### Dependencies

The simplified implementation requires:

```toml
atomic-agents = "^1.1.2"
instructor = "^1.6.1"
pydantic = ">=2.10.3,<3.0.0"
openai = ">=1.35.12,<2.0.0"
```

## Best Practices

### 1. **Use Type Hints**
```python
def process_query(query: str, context: str = "") -> ResearchPlan:
    return research_investment(query, context)
```

### 2. **Validate Schemas**
```python
# Input validation happens automatically
query = InvestmentQuery(query="Should I invest in AAPL?", context="Recent product launch")
assert isinstance(query, InvestmentQuery)

# Result is always a ResearchPlan
result = research_investment(query.query, query.context)
assert isinstance(result, ResearchPlan)
```

### 3. **Handle Errors Gracefully**
```python
try:
    result = research_investment(query, context)
except Exception as e:
    logger.error(f"Research failed: {e}")
    # Implement fallback logic
```

### 4. **Access Results Directly**
```python
result = research_investment(query, context)
if result.success:
    print(f"Research completed with {len(result.steps)} steps")
    print(f"Key findings: {result.accumulated_knowledge}")
```

## Troubleshooting

### Common Issues

1. **Schema Validation Errors**
   - Check that all required fields are provided
   - Ensure field types match schema definitions
   - Validate nested objects (e.g., PlanStep)

2. **API Key Issues**
   - Verify OPENAI_API_KEY is set correctly
   - Check API key permissions and quotas
   - Test with a simple OpenAI call first

3. **Import Errors**
   - Ensure atomic-agents is installed: `pip install atomic-agents`
   - Check Python path includes the project root
   - Verify all dependencies are installed

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with verbose output
result = research_investment(query, context)
```

## Contributing

When extending the simplified architecture:

1. **Maintain Simplicity**: Keep the three-schema design
2. **Single Entry Point**: Preserve the `research_investment()` function as the main API
3. **Add Tests**: Create unit tests for any new functionality
4. **Document Changes**: Update this README.md with any changes
5. **Update __init__.py**: Export any new components

## Future Enhancements

- [ ] Add streaming support for real-time investment research updates
- [ ] Implement plan validation against available financial tools and data sources
- [ ] Add support for conditional execution flows based on interim research findings
- [ ] Create specialized research functions for different investment strategies (e.g., value, growth, quant)
- [ ] Add metrics and observability for tracking research plan effectiveness and tool usage