# Pydantic-AI Investment Research System

A modern investment research system built with **pydantic-ai** featuring natural agent loops, type-safe dependencies, and comprehensive analysis capabilities.

## 🚀 Quick Start

### Installation
```bash
# Install dependencies
poetry install

# Set up environment variables (available in .env file)
export OPENROUTER_API_KEY="your-openrouter-api-key"
```

### Basic Usage
```python
from main import research_investment

# Conduct comprehensive investment research
analysis = await research_investment(
    query="Should I invest in AAPL for long-term growth?",
    context="Looking for 3-5 year investment horizon. Moderate risk tolerance."
)

print(analysis.findings.summary)
print(analysis.findings.recommendation)
```

### Run Examples
```bash
# Test core components
python test_pydantic_ai.py

# Run full investment workflow
python main.py
```

## 🏗️ Architecture

### Clean, Natural Design
```
agents/                    # Pydantic-AI agents with natural tool loops
├── dependencies.py       # Type-safe shared context
├── planning_agent.py     # Investment research planning
└── research_agent.py     # Research execution with tools

tools/                    # Tool functions for agents
├── web_search.py        # SearxNG integration
├── web_scraper.py       # BeautifulSoup content extraction
├── vector_search.py     # ChromaDB document search
└── calculator.py        # Financial calculations

models/                   # Clean Pydantic schemas
└── schemas.py           # All data models

main.py                  # Main entry point
```

### Core Principles
1. **Natural Agent Loops**: Agents decide when and how to use tools organically
2. **Type-Safe Dependencies**: Shared context through RunContext with dependency injection
3. **Simple Architecture**: Clear separation without complex orchestration

## 🎯 Key Features

### Natural Tool Integration
The research agent naturally decides which tools to use:
```python
@research_agent.tool
async def search_internal_docs(ctx: RunContext[ResearchDependencies], query: str) -> str:
    """Search SEC filings, earnings reports, analyst documents."""
    # Agent calls this when it needs internal company data

@research_agent.tool  
async def search_web(ctx: RunContext[ResearchDependencies], query: str) -> str:
    """Search current market news and trends."""
    # Agent calls this for real-time market information
```

### Rich Analysis Output
- **Financial Metrics**: P/E ratios, debt ratios, growth rates
- **Key Insights**: Bullet-pointed findings from research
- **Risk Assessment**: Identified risk factors and opportunities  
- **Investment Recommendation**: Clear buy/hold/sell guidance
- **Confidence Score**: AI confidence in analysis quality

### Enhanced Web Capabilities
- **SearxNG Integration**: Comprehensive web search across multiple engines
- **BeautifulSoup Scraping**: Intelligent content extraction from financial sites
- **Vector Search**: Semantic search through SEC filings and company documents

## 📊 Example Output

```
🔍 Starting investment research for: Should I invest in AAPL for long-term growth?

✅ Plan created with 4 steps:
  1. Gather comprehensive financial statements...
  2. Conduct competitive analysis...
  3. Perform valuation analysis...
  4. Develop investment recommendation...

📊 Investment Analysis Summary
Apple Inc. (AAPL) has shown resilience in the technology sector despite recent 
challenges. Q4 revenues of $89.5 billion with strong services growth...

💰 Financial Metrics
P/E Ratio: 32.30
Profit Margin: 1260.00%

🔑 Key Insights:
• EPS increased to $1.46, surpassing analyst expectations
• Services sector outperformed with 16% year-over-year growth
• iPhone sales remained stable despite market challenges

🎯 Investment Recommendation
Given solid services performance and iPhone resilience, investing in AAPL 
could be favorable for long-term growth...

📈 Confidence Score: 75.0%
```

## 🛠️ Technical Details

### Dependencies
- **pydantic-ai**: Natural agent framework with tool loops
- **aiohttp**: Async HTTP for web operations
- **beautifulsoup4**: HTML parsing and content extraction
- **chromadb**: Vector database for document search
- **rich**: Terminal formatting for output

### Configuration
- Uses OpenRouter as API proxy: `https://openrouter.ai/api/v1`
- Model: `gpt-4o-mini` (configurable)
- ChromaDB persistence: `./investment_chroma_db`
- SearxNG endpoint: `http://localhost:8080`

### Data Sources
- **Knowledge Base**: SEC filings, earnings transcripts, analyst reports
  - `knowledge_base/AAPL/`: Apple financial documents
  - `knowledge_base/MSFT/`: Microsoft financial documents
- **Real-time Data**: Web search for current market information
- **Vector Embeddings**: Semantic search through company documents

## 🔄 Investment Research Flow

1. **Planning Phase**
   ```python
   plan = await create_research_plan(query, context)
   # → Generates 2-4 structured research steps
   ```

2. **Research Phase** 
   ```python
   findings = await conduct_research(query, plan, deps)
   # → Agent naturally uses tools:
   #   - search_internal_docs for SEC filings
   #   - search_web for current news
   #   - scrape_webpage for detailed content
   #   - calculate_financial_metrics for analysis
   ```

3. **Analysis Output**
   ```python
   analysis = InvestmentAnalysis(query, context, plan, findings)
   # → Complete structured analysis with confidence score
   ```

## 🧪 Testing

### Component Tests
```bash
# Test planning agent
python test_pydantic_ai.py

# Test dependencies initialization
python -c "from agents.dependencies import initialize_dependencies; print('✅ Dependencies OK')"
```

### Full Workflow Test
```bash
# Run complete investment research
python main.py
```

## 🎨 Migration Benefits

Compared to the previous atomic-agents implementation:

| Aspect | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Success Rate** | 50% | 100% | ✅ +50% |
| **Architecture** | Complex orchestration | Natural loops | ✅ Simplified |
| **File Count** | 15+ files | 8 files | ✅ Cleaner |
| **Tool Usage** | Forced by orchestrator | Agent decides | ✅ More natural |
| **Output** | Plain text | Rich formatted | ✅ Better UX |
| **Type Safety** | Basic schemas | Full RunContext | ✅ Stronger |

## 🚀 Advanced Usage

### Custom Research Context
```python
analysis = await research_investment(
    query="Analyze semiconductor ETFs vs individual stocks",
    context="Portfolio diversification strategy. Risk tolerance: moderate. Timeline: 2-3 years.",
    searxng_url="http://custom-searxng:8080",  # Custom search endpoint
    chroma_path="./custom_vector_db"           # Custom vector database
)
```

### Accessing Individual Components
```python
from agents.planning_agent import create_research_plan
from agents.research_agent import conduct_research
from agents.dependencies import initialize_dependencies

# Use components independently
deps = initialize_dependencies(query, context)
plan = await create_research_plan(query, context)
findings = await conduct_research(query, plan, deps)
```

## 📚 Documentation

- [CLAUDE.md](CLAUDE.md) - Development guidance
- [COMPARISON_RESULTS.md](COMPARISON_RESULTS.md) - Migration comparison
- [README_PYDANTIC_AI.md](README_PYDANTIC_AI.md) - Migration documentation

## 🤝 Contributing

1. Follow pydantic-ai patterns and natural agent loops
2. Use type-safe RunContext for tool functions
3. Add clear docstrings for tool functions (LLM reads these)
4. Test components individually and as complete workflows
5. Maintain clean separation between agents, tools, and models

## 📈 Future Enhancements

- [ ] Portfolio analysis capabilities
- [ ] Real-time market data integration
- [ ] Advanced financial modeling tools
- [ ] Multi-asset class support
- [ ] Risk management analytics
- [ ] ESG (Environmental, Social, Governance) analysis

## 📄 License

This project demonstrates modern agentic AI architecture patterns using pydantic-ai for investment research workflows.