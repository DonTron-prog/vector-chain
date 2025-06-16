# Pydantic-AI Investment Research System

This is the new pydantic-ai implementation of the investment research system, migrated from atomic-agents for improved clarity and natural agent loops.

## Architecture Overview

### Core Philosophy
- **Natural Agent Loops**: Trust pydantic-ai's built-in agent decision making
- **Type-Safe Dependencies**: Shared context through Pydantic models
- **Simplified Structure**: Clear separation of concerns without complex orchestration

### Directory Structure
```
agents/                    # Pydantic-AI agents
├── dependencies.py       # Shared context and dependencies
├── planning_agent.py     # Investment research planning
└── research_agent.py     # Research execution with tools

tools/                    # Tool functions
├── web_search.py        # SearxNG integration
├── web_scraper.py       # BeautifulSoup scraping
├── vector_search.py     # ChromaDB RAG search
└── calculator.py        # Financial calculations

models/                   # Clean Pydantic schemas
└── schemas.py           # All data models

main.py                  # Main entry point
test_pydantic_ai.py     # Test script
```

## Key Improvements

### 1. Natural Tool Loops
Instead of complex sub-agent orchestration, agents naturally decide when and how to use tools:

```python
@research_agent.tool
async def search_internal_docs(ctx: RunContext[ResearchDependencies], query: str) -> str:
    # Simple, focused tool function
    # Agent decides when to call this
```

### 2. Type-Safe Context Sharing
```python
class ResearchDependencies(BaseModel):
    vector_db: ChromaDBClient
    searxng_client: SearxNGClient
    current_query: str
    research_context: str = ""
```

### 3. Enhanced Web Capabilities
- **SearxNG Integration**: Comprehensive web search
- **BeautifulSoup Scraping**: Content extraction from specific pages
- **Async Support**: All operations are async for better performance

## Usage

### Basic Usage
```python
from main import research_investment

# Simple research query
analysis = await research_investment(
    query="Should I invest in AAPL for long-term growth?",
    context="Looking for 3-5 year investment horizon. Moderate risk tolerance."
)

print(analysis.findings.summary)
print(analysis.findings.recommendation)
```

### Running Tests
```bash
# Test core components
python test_pydantic_ai.py

# Full workflow test
python main.py
```

## Setup Requirements

### Dependencies
```bash
# Install new dependencies
poetry install
```

### Environment Variables
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### External Services
- **SearxNG**: Running on localhost:8080 (for web search)
- **ChromaDB**: Vector database for document search

## Migration Benefits

### Vs. Atomic Agents Implementation

| Aspect | Atomic Agents | Pydantic-AI |
|--------|---------------|-------------|
| **Architecture** | Complex orchestration with sub-agents | Natural agent loops with tools |
| **Code Files** | 15+ files across multiple directories | 8 core files in clear structure |
| **Tool Usage** | Forced through orchestrator decisions | Agent decides naturally |
| **Type Safety** | Basic schema validation | Full RunContext type safety |
| **Web Search** | Limited search functionality | SearxNG + BeautifulSoup integration |
| **Maintenance** | Complex interdependencies | Clear, modular components |

### Performance Improvements
- **Async Throughout**: All operations are async by default
- **Natural Decision Making**: Agents decide tool usage organically
- **Better Context Management**: Type-safe dependency injection
- **Enhanced Search**: More comprehensive web search and scraping

## Example Workflow

1. **Planning Phase**
   ```python
   plan = await create_research_plan(query, context)
   # Generates 2-4 structured research steps
   ```

2. **Research Phase**
   ```python
   findings = await conduct_research(query, plan, deps)
   # Agent naturally uses tools as needed:
   # - search_internal_docs for SEC filings
   # - search_web for current news
   # - scrape_webpage for detailed content
   # - calculate_financial_metrics for analysis
   ```

3. **Analysis Output**
   ```python
   # Structured findings with confidence scores
   analysis.findings.summary
   analysis.findings.key_insights
   analysis.findings.financial_metrics
   analysis.findings.recommendation
   ```

## Testing the Migration

The migration maintains full compatibility with the existing functionality while providing cleaner architecture and enhanced capabilities.

Run comparative tests to validate equivalent functionality:
```bash
# Test new system
python test_pydantic_ai.py
python main.py

# Compare with original system
python controllers/planning_agent/investment_agent.py
```

## Next Steps

1. **Validation**: Test against existing use cases
2. **Performance**: Compare execution times and accuracy
3. **Integration**: Migrate any remaining atomic-agents dependencies
4. **Optimization**: Fine-tune agent prompts and tool usage patterns