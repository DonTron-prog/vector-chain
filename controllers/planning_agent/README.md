# Investment Research Planning Agent with Atomic Agents

This module provides an Atomic Agents implementation for investment research planning and execution. The legacy SRE-focused `SimplePlanningAgent` has been deprecated by this more robust and domain-specific approach.

## Architecture Overview

### Atomic Agents Architecture for Investment Research
- **Planning**: [`atomic_planning_agent.py`](atomic_planning_agent.py) - Generates structured investment research plans.
- **Execution**: [`execution_orchestrator.py`](execution_orchestrator.py) - Executes these research plans step-by-step.
- **Schemas**: [`planner_schemas.py`](planner_schemas.py) - Defines the structured Pydantic schemas for inputs and outputs (e.g., `PlanningAgentInputSchema`, `InvestmentPlanSchema`).
- **Benefits**: Modular, testable, debuggable, and composable, tailored for investment research workflows.

## Quick Start

### Using the Atomic Investment Planning Agent

```python
from controllers.planning_agent import (
    create_atomic_planning_agent,
    ExecutionOrchestrator,
    PlanningAgentInputSchema, # Updated schema
    ExecutionOrchestratorInputSchema
)
# Assuming OrchestratorCore and other necessary components are set up
# from orchestration_engine import OrchestratorCore, ConfigManager, ToolManager, create_orchestrator_agent
import instructor
import openai
import os

# 0. Create a shared client (ensure api_key is available)
# Example: api_key = os.getenv("OPENAI_API_KEY")
# shared_client = instructor.from_openai(openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key))

# --- OrchestratorCore setup (example, adapt as needed) ---
# config_manager = ConfigManager.load_configuration()
# tools = ConfigManager.initialize_tools(config_manager)
# orchestrator_agent_instance = create_orchestrator_agent(shared_client, model="gpt-4o-mini") # Or your chosen model
# tool_manager_instance = ToolManager(tools)
# orchestrator_core_instance = OrchestratorCore(orchestrator_agent_instance, tool_manager_instance)
# --- End OrchestratorCore setup ---


# 1. Create atomic investment planning agent
# planning_agent = create_atomic_planning_agent(shared_client, model="gpt-4o-mini") # Or your chosen model

# 2. Generate structured investment research plan
# planning_input = PlanningAgentInputSchema(
#     investment_query="Analyze the growth prospects of AAPL for the next 5 years.",
#     research_context="Client is risk-averse. Focus on fundamentals and market position. Access to 10-K, 10-Q, and analyst reports."
# )
# planning_result = planning_agent.run(planning_input)

# 3. Execute plan (requires orchestrator_core_instance from above)
# execution_orchestrator = ExecutionOrchestrator(orchestrator_core_instance)
# execution_input = ExecutionOrchestratorInputSchema(
# investment_query=planning_input.investment_query,
# research_context=planning_input.research_context,
# planning_output=planning_result
# )
# execution_result = execution_orchestrator.run(execution_input)
# print(execution_result.final_summary)
```

*(Note: The legacy `SimplePlanningAgent` for SRE is no longer the primary focus of this module.)*

## File Structure

```
controllers/planning_agent/
├── README.md                          # This file
├── __init__.py                        # Module exports
├── planner_schemas.py                 # Pydantic schemas
│
├── # (Legacy SRE files like simple_agent.py, executor.py, demo_atomic_vs_legacy.py may be removed or archived)
│
├── # Atomic Agents Implementation for Investment Research
├── atomic_planning_agent.py           # Generates investment research plans
├── execution_orchestrator.py          # Executes investment research plans
├── atomic_executor.py                 # Main entry point for investment planning workflow
│
└── # Testing
    └── test_atomic_components.py      # Component tests for investment planning
```

## Key Components

### 1. AtomicPlanningAgent (Investment Focus)

**Purpose**: Generate structured investment research plans.

**Features**:
- Uses Instructor for guaranteed structured outputs (via `AtomicPlanningOutputSchema`).
- Follows investment research best practices (e.g., data gathering → financial analysis → valuation → risk assessment → recommendation).
- Generates 2-4 actionable research steps with clear reasoning.
- Fully testable and debuggable.

**Input Schema** (from `planner_schemas.py`):
```python
class PlanningAgentInputSchema(BaseIOSchema): # Note: Renamed from AtomicPlanningInputSchema in atomic_planning_agent.py
    investment_query: str = Field(..., description="The investment query to create a plan for")
    research_context: str = Field(..., description="Contextual information for the research")
```

**Output Schema** (from `atomic_planning_agent.py`):
```python
class AtomicPlanningOutputSchema(BaseIOSchema): # This is the direct output of the agent
    steps: List[PlanStepSchema] = Field(
        ...,
        description="Generated plan steps in logical order (2-4 steps)", # Updated count
        min_items=2,
        max_items=4
    )
    reasoning: str = Field(..., description="Explanation of the planning approach and rationale")
```

### 2. ExecutionOrchestrator (Investment Focus)

**Purpose**: Execute investment research plans step-by-step using the main orchestration engine.

**Features**:
- Pure execution logic, taking a plan generated by `AtomicPlanningAgent`.
- Accumulates knowledge and context across research steps.
- Provides detailed results for each executed step.
- Handles errors during step execution.

**Input Schema** (from `execution_orchestrator.py`):
```python
class ExecutionOrchestratorInputSchema(BaseIOSchema):
    investment_query: str = Field(..., description="The original investment query")
    research_context: str = Field(..., description="Contextual information for the research")
    planning_output: AtomicPlanningOutputSchema = Field(..., description="Output from the planning agent") # Takes direct output
```

**Output Schema** (from `execution_orchestrator.py`):
```python
class ExecutionOrchestratorOutputSchema(BaseIOSchema):
    executed_steps: List[StepExecutionResult] = Field(...) # Contains results of each step
    final_summary: str = Field(...) # Overall summary of the research execution
    success: bool = Field(...) # Whether the overall execution was successful
    accumulated_knowledge: str = Field(...) # Knowledge gathered throughout the execution
```

### 3. Schema-Based Chaining

Components are connected directly through their defined Pydantic schemas:

```python
# planning_result (AtomicPlanningOutputSchema) from planning_agent.run()
# is directly used in ExecutionOrchestratorInputSchema.

# Example:
# planning_input = PlanningAgentInputSchema(investment_query="...", research_context="...")
# planning_result = planning_agent.run(planning_input)

# execution_input = ExecutionOrchestratorInputSchema(
#     investment_query=planning_input.investment_query,
#     research_context=planning_input.research_context,
#     planning_output=planning_result
# )
# execution_result = execution_orchestrator.run(execution_input)
```

## Running Examples

### 1. Test Components

```bash
# Test individual atomic investment planning components
python controllers/planning_agent/test_atomic_components.py
```

*(Legacy SRE demos and executors are no longer the focus.)*

### 2. Run Atomic Investment Executor

```bash
# Run atomic investment research workflow
python controllers/planning_agent/atomic_executor.py
```

## Benefits of Atomic Agents Approach (for Investment Research)

### 🔍 **Transparency**
- Clear input/output Pydantic schemas for each component (planning, execution).
- No hidden "magic"; data flow is explicit.
- Easy to understand how an investment query is processed into a plan and then executed.

### 🧪 **Testability**
- Unit test the `AtomicPlanningAgent` and `ExecutionOrchestrator` independently.
- Mock inputs/outputs easily using their Pydantic schemas.
- Isolated testing of investment plan generation vs. plan execution logic.

### 🐛 **Debuggability**
- Set breakpoints within the planning or execution components.
- Inspect the exact Pydantic schema data at each stage of the research process.
- Clear separation of concerns simplifies identifying issues.

### 🔧 **Modularity**
- Swap investment planning strategies (e.g., different LLM prompts or models for `AtomicPlanningAgent`) without altering the `ExecutionOrchestrator`.
- Modify how research steps are executed (e.g., different tools in the main orchestrator) without changing the planning agent.
- Potentially reuse components for different types of financial analysis.

### 📊 **Reliability**
- Instructor ensures the `AtomicPlanningAgent` produces structured output matching `AtomicPlanningOutputSchema`.
- Pydantic validation at each component boundary catches data inconsistencies early.
- Consistent data formats (defined by schemas) across the planning and execution pipeline.

### 🔗 **Composability**
- Components are chained via their Pydantic schemas (output of planner feeds input of executor).
- Build complex investment research workflows from these atomic building blocks.
- Reuse these specialized agents within larger financial analysis systems.

## (Migration Guide from Legacy SRE is less relevant now)

The focus has shifted to the new Atomic Agents architecture for investment research. If migrating from a previous SRE-based system:

1. **Adapt Input**: Instead of `alert` and `system_context`, use `investment_query` and `research_context` as defined in `PlanningAgentInputSchema`.
2. **Update Prompts**: The `AtomicPlanningAgent` now uses prompts tailored for investment research (see `atomic_planning_agent.py`).
3. **Use New Schemas**: Ensure all interactions use the updated Pydantic schemas from `planner_schemas.py`, `atomic_planning_agent.py`, and `execution_orchestrator.py`.
4. **Review Tooling**: The underlying `OrchestratorCore` should be configured with tools relevant to financial research (e.g., RAG for financial documents, web search for market news, data analysis tools).

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
def process_investment_query(input_data: PlanningAgentInputSchema) -> AtomicPlanningOutputSchema: # Using the correct input schema
    return planning_agent.run(input_data)
```

### 2. **Validate Schemas**
```python
# Always validate inputs
# input_schema = PlanningAgentInputSchema(investment_query="...", research_context="...")
# result = planning_agent.run(input_schema)
# assert isinstance(result, AtomicPlanningOutputSchema) # Output of the agent itself
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

## Future Enhancements

- [ ] Add streaming support for real-time investment research updates.
- [ ] Implement plan validation against available financial tools and data sources.
- [ ] Add support for conditional execution flows based on interim research findings.
- [ ] Create specialized planning agents for different investment strategies (e.g., value, growth, quant).
- [ ] Add metrics and observability for tracking research plan effectiveness and tool usage.