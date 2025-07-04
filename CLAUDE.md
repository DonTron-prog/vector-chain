# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the pydantic-ai investment research system.

## Development Commands

### Setup
```bash
# Install dependencies (use conda environment: agentsre)
conda activate agentsre
pip install -e .
pip install -r requirements-dev.txt

# Required environment variables (available in .env file)
export OPENROUTER_API_KEY="your-openrouter-api-key"
export OPENAI_API_KEY="your-openai-api-key"  # fallback

# Optional: Setup Logfire for LLM tracing and observability
logfire auth
logfire projects use <your-project-name>
```

### Testing
```bash
# Install testing dependencies (first time setup)
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run specific test categories
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests only
pytest tests/e2e/                     # End-to-end tests only

# Run tests with coverage
pytest --cov=tools --cov=models --cov=agents --cov-report=html

# Run fast tests only (exclude slow/network tests)
pytest -m "not slow and not network"

# Use the convenient test runner
python run_tests.py

# Or use Makefile commands
make test                    # Run all tests
make test-unit              # Unit tests only
make test-cov               # Tests with coverage
make test-fast              # Fast tests only

# New test structure - Manual testing
python tests/rag/simple_rag_test.py          # Interactive RAG testing
python tests/rag/test_rag_only.py            # Comprehensive RAG tests
python tests/rag/test_rag_agent_only.py      # RAG-only agent tests
python tests/agents/test_research_agent_full.py  # Full agent tests
```

### Running Examples
```bash
# Main investment research workflow
python main.py

# Test individual components
python test_pydantic_ai.py
```

### Streamlit Chat Web App
```bash
# Launch the Streamlit chat interface
python run_streamlit.py

# Or directly with streamlit
streamlit run streamlit_app.py
```

**Chat Interface Features:**
- 💬 **Multi-Mode Chat**: Choose from 4 research modes with increasing depth
- 📁 **Document Management**: Upload and manage investment documents (TXT/PDF)
- 🎛️ **Mode Selection**: Switch between research modes in real-time
- 📊 **Context Persistence**: Maintain conversation history across mode switches
- 📥 **Export Options**: Download chat history and analysis results

**Research Modes:**
1. **💬 Simple Chat**: Quick Q&A with LLM for general investment questions
2. **📚 RAG Only**: Search internal documents + LLM analysis for company-specific queries
3. **🔍 Deep Research**: Web search + scraping + calculations for current market analysis
4. **🎯 Full Planning**: Complete research workflow with planning agent (original functionality)

**App Usage:**
1. **Select Mode**: Choose research depth in sidebar (Simple → RAG → Deep → Full Planning)
2. **Upload Documents**: Add company documents to knowledge base for RAG and Full Planning modes
3. **Chat Interface**: Ask investment questions and get mode-appropriate responses
4. **Context Settings**: Set investment context (timeframe, risk tolerance) in sidebar
5. **Export Results**: Download chat history or full analysis results

**Mode Descriptions:**
- **Simple Chat**: Fast conversational AI for general investment education and quick questions
- **RAG Only**: Searches your uploaded documents to answer specific company questions
- **Deep Research**: Uses live web search for current market trends and news analysis  
- **Full Planning**: Comprehensive research with structured planning, all tools, and detailed analysis

## Architecture Overview

### Clean Pydantic-AI Structure

**Agents** (`agents/`): Pydantic-AI agents with natural tool loops
- `dependencies.py`: Type-safe shared context and dependencies
- `planning_agent.py`: Investment research planning with structured output
- `research_agent.py`: Research execution with natural tool selection

**Tools** (`tools/`): Tool functions for agent use
- `web_search.py`: SearxNG integration for web search
- `web_scraper.py`: BeautifulSoup content extraction
- `vector_search.py`: ChromaDB vector database search
- `calculator.py`: Financial calculations and metrics

**Models** (`models/`): Clean Pydantic data models
- `schemas.py`: All structured data models for the system

### Core Principles

1. **Natural Agent Loops**: Agents decide when and how to use tools organically
2. **Type-Safe Dependencies**: Shared context through RunContext with typed dependencies
3. **Simple Architecture**: Clear separation of concerns without complex orchestration

### Investment Research Flow

1. **Planning Phase**: `planning_agent` creates structured research plan
2. **Research Phase**: `research_agent` uses tools naturally based on plan
3. **Output**: Complete investment analysis with metrics, insights, and recommendations

### Key Features

- **SearxNG Integration**: Comprehensive web search capabilities
- **BeautifulSoup Scraping**: Intelligent content extraction from web pages
- **ChromaDB Vector Search**: Semantic search through investment documents
- **Financial Calculations**: Automated ratio and metric calculations
- **Rich Output**: Formatted analysis with structured insights

### Dependencies

- **pydantic-ai**: Main agent framework with natural tool loops
- **aiohttp**: Async HTTP client for web operations
- **beautifulsoup4**: HTML parsing and content extraction
- **chromadb**: Vector database for document search
- **rich**: Terminal formatting for better output display

### Data Sources

Investment documents stored in `knowledge_base/`:
- `AAPL/`: Apple financial documents (10K, 10Q, analyst reports, earnings)
- `MSFT/`: Microsoft financial documents
- Vector embeddings in `investment_chroma_db/`

### Configuration

- Uses OpenRouter as API proxy: `base_url="https://openrouter.ai/api/v1"`
- Model: `gpt-4o-mini` (configurable)
- Environment variables loaded from `.env` file
- ChromaDB persistence in `./investment_chroma_db`
- SearxNG expected at `http://localhost:8080`

### Example Usage

```python
from main import research_investment

# Conduct investment research
analysis = await research_investment(
    query="Should I invest in AAPL for long-term growth?",
    context="Looking for 3-5 year investment horizon. Moderate risk tolerance."
)

print(analysis.findings.summary)
print(analysis.findings.recommendation)
```