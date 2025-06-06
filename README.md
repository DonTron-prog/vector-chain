# Investment Research Planning Agent with Atomic Agents

This module provides a modern investment research planning and execution system built with the Atomic Agents framework.

## Architecture Overview

The investment research planning agent uses **Atomic Agents** architecture with clear separation of concerns:

- **Planning**: [`atomic_planning_agent.py`](controllers/planning_agent/atomic_planning_agent.py) - Pure investment research planning with structured outputs
- **Execution**: [`execution_orchestrator.py`](controllers/planning_agent/execution_orchestrator.py) - Pure execution logic for research plans
- **Schemas**: [`planner_schemas.py`](controllers/planning_agent/planner_schemas.py) - Structured I/O contracts for investment queries
- **Orchestration**: [`atomic_executor.py`](controllers/planning_agent/atomic_executor.py) - Complete investment research workflow coordination

## Quick Start

### Basic Usage

```python
from controllers.planning_agent import (
    create_atomic_planning_agent,
    ExecutionOrchestrator,
    PlanningAgentInputSchema,
    ExecutionOrchestratorInputSchema
)
import instructor
import openai
import os

# 0. Create a shared client (ensure api_key is available)
api_key = os.getenv("OPENAI_API_KEY") # Example
shared_client = instructor.from_openai(openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key))

# 1. Create atomic investment planning agent
planning_agent = create_atomic_planning_agent(shared_client, model="gpt-4")

# 2. Generate structured investment research plan
planning_result = planning_agent.run(PlanningAgentInputSchema(
    investment_query="Analyze AAPL's growth prospects for the next 5 years",
    research_context="Client is risk-averse, focus on fundamentals and market position"
))

# 3. Execute plan (requires orchestrator setup)
execution_orchestrator = ExecutionOrchestrator(orchestrator_core)
execution_result = execution_orchestrator.run(
    ExecutionOrchestratorInputSchema(
        investment_query=planning_result.investment_query,
        research_context=planning_result.research_context,
        planning_output=planning_result
    )
)
```

### Complete Workflow

```python
from controllers.planning_agent import process_query_with_atomic_planning

# One-line execution of complete investment research workflow
result = process_query_with_atomic_planning(
    investment_query="Should I invest in MSFT for short-term gains?",
    research_context="Client has 3-6 month holding period, high risk tolerance",
    model="gpt-4"
)

print(f"Success: {result.success}")
print(f"Steps executed: {len(result.plan.steps)}")
print(f"Summary: {result.summary}")
```

## File Structure

```
controllers/planning_agent/
├── README.md                          # This file
├── __init__.py                        # Module exports
├── planner_schemas.py                 # Pydantic schemas
│
├── # Atomic Agents Implementation  
├── atomic_planning_agent.py           # Pure planning agent
├── execution_orchestrator.py          # Pure execution logic
├── atomic_executor.py                 # Atomic workflow orchestration
│
└── # Testing & Demo
    ├── test_atomic_components.py      # Component tests
    └── demo_atomic_agents.py          # Architecture demo
```

## Key Components

### 1. AtomicPlanningAgent

**Purpose**: Generate structured investment research plans

**Features**:
- Uses Instructor for guaranteed structured outputs
- Follows investment research best practices (data gathering → analysis → valuation → recommendation)
- Generates 2-4 actionable research steps with reasoning
- Fully testable and debuggable

**Input Schema**:
```python
class PlanningAgentInputSchema(BaseIOSchema):
    investment_query: str = Field(..., description="The investment query to create a plan for")
    research_context: str = Field(..., description="Contextual information for the research")
```

**Output Schema**:
```python
class AtomicPlanningOutputSchema(BaseIOSchema):
    steps: List[PlanStepSchema] = Field(..., description="Generated plan steps (2-4)")
    reasoning: str = Field(..., description="Planning approach and rationale")
```

### 2. ExecutionOrchestrator

**Purpose**: Execute investment research plans step-by-step using the orchestration engine

**Features**:
- Pure execution logic (no planning)
- Context accumulation across research steps
- Detailed step-by-step results
- Error handling and recovery

**Input Schema**:
```python
class ExecutionOrchestratorInputSchema(BaseIOSchema):
    investment_query: str = Field(..., description="The original investment query")
    research_context: str = Field(..., description="Contextual information for the research")
    planning_output: AtomicPlanningOutputSchema = Field(..., description="Output from the planning agent")
```

**Output Schema**:
```python
class ExecutionOrchestratorOutputSchema(BaseIOSchema):
    executed_steps: List[StepExecutionResult] = Field(...)
    final_summary: str = Field(...)
    success: bool = Field(...)
    accumulated_knowledge: str = Field(...)
```

### 3. Schema-Based Chaining

Components are connected through matching schemas:

```python
# Planning output → Execution input
planning_result = planning_agent.run(planning_input)
execution_result = execution_orchestrator.run(
    ExecutionOrchestratorInputSchema(
        investment_query=planning_input.investment_query,
        research_context=planning_input.research_context,
        planning_output=planning_result
    )
)
```

## Running Examples

### 1. Test Components

```bash
# Test individual atomic components
python controllers/planning_agent/test_atomic_components.py
```

### 2. Explore Architecture

```bash
# Interactive demo of atomic agents features
python controllers/planning_agent/demo_atomic_agents.py
```

### 3. Run Complete Workflow

```bash
# Run atomic agents workflow
python controllers/planning_agent/atomic_executor.py
```

## Benefits of Atomic Agents Architecture

### 🔍 **Transparency**
- Clear input/output contracts for every component
- No hidden "magic" or black boxes
- Easy to understand data flow

### 🧪 **Testability**
- Unit test each atomic component independently
- Mock inputs/outputs with Pydantic schemas
- Isolated testing of planning vs execution logic

### 🐛 **Debuggability**
- Set breakpoints on specific atomic components
- Inspect exact schemas at each step
- Clear separation of concerns

### 🔧 **Modularity**
- Swap planning strategies without changing execution
- Replace execution engines without touching planning
- Mix and match components as needed

### 📊 **Reliability**
- Guaranteed structured outputs with Instructor
- Pydantic validation catches schema errors
- Consistent data formats across components

### 🔗 **Composability**
- Chain components through schema matching
- Build complex workflows from simple atoms
- Reuse components in different contexts

## Architecture Diagram

```mermaid
graph TD
    A[Investment Query] --> B[AtomicPlanningAgent]
    B --> C[AtomicPlanningOutputSchema]
    C --> D[ExecutionOrchestrator]
    D --> E[OrchestratorCore]
    E --> F[Investment Tool Execution]
    F --> G[ExecutionOrchestratorOutputSchema]
    G --> H[Investment Research Summary]
    
    style B fill:#e8f5e8
    style D fill:#e8f5e8
    style C fill:#e3f2fd
    style G fill:#e3f2fd
```

## Configuration

### Environment Variables

```bash
# Required for planning agent
export OPENAI_API_KEY="your-openai-api-key"

# Optional model selection
export PLANNING_MODEL="gpt-4"  # Default: gpt-4
```

### Dependencies

The atomic agents implementation requires:

```toml
atomic-agents = "^1.1.2"
instructor = "^1.6.1"
pydantic = ">=2.10.3,<3.0.0"
openai = ">=1.35.12,<2.0.0"
```

## Best Practices

### 1. **Use Type Hints**
```python
def process_investment_query(input_data: PlanningAgentInputSchema) -> AtomicPlanningOutputSchema:
    return planning_agent.run(input_data)
```

### 2. **Validate Schemas**
```python
# Always validate inputs
input_schema = PlanningAgentInputSchema(
    investment_query="Analyze NVDA vs AMD in AI chip market",
    research_context="Client interested in semiconductor exposure"
)
result = planning_agent.run(input_schema)
assert isinstance(result, AtomicPlanningOutputSchema)
```

### 3. **Handle Errors Gracefully**
```python
try:
    result = planning_agent.run(input_schema)
except Exception as e:
    logger.error(f"Planning failed: {e}")
    # Implement fallback logic
```

### 4. **Test Components Independently**
```python
def test_planning_agent():
    # shared_client = instructor.from_openai(openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)) # Example
    agent = create_atomic_planning_agent(shared_client, model)
    result = agent.run(test_input)
    assert len(result.steps) >= 3
    assert result.reasoning is not None
```

## Troubleshooting

### Common Issues

1. **Schema Validation Errors**
   - Check that all required fields are provided
   - Ensure field types match schema definitions
   - Validate nested objects (e.g., PlanStepSchema)

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
result = planning_agent.run(input_schema)
```

## Contributing

When adding new atomic components:

1. **Follow the IPO Pattern**: Input Schema → Process → Output Schema
2. **Inherit from BaseIOSchema**: Use Pydantic for all schemas
3. **Add Tests**: Create unit tests for each component
4. **Document Schemas**: Add clear field descriptions
5. **Update __init__.py**: Export new components

## Example Scenarios

The system handles various investment research scenarios:

### 1. Individual Stock Analysis
```python
result = process_query_with_atomic_planning(
    investment_query="Assess AAPL's long-term growth potential for 5+ year hold",
    research_context="AAPL has seen significant price appreciation. Need fundamental analysis and valuation."
)
```

### 2. Comparative Analysis
```python
result = process_query_with_atomic_planning(
    investment_query="Compare growth prospects of NVDA vs AMD in AI chip market",
    research_context="Both are key players. Analyze market share, R&D, partnerships, and financials."
)
```

### 3. Short-term Investment Assessment
```python
result = process_query_with_atomic_planning(
    investment_query="Evaluate MSFT for 3-6 month holding period",
    research_context="Client interested in short-term gains. MSFT recently announced AI initiatives."
)
```

## Future Enhancements

- [ ] Add streaming support for real-time investment research updates
- [ ] Implement plan validation against available financial data sources
- [ ] Add support for conditional execution flows based on research findings
- [ ] Create specialized planning agents for different investment strategies (value, growth, quant)
- [ ] Add metrics and observability for research plan effectiveness
- [ ] Support for multi-step plan dependencies and research workflows
- [ ] Integration with external financial data providers and market feeds
