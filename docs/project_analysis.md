# Investment Research Agent - Complete Project Analysis

This project is a **agentic investment research system** that takes investment queries, creates multi-step research plans, and executes them using specialized tools. Here's the complete functionality and flow:

## Core Architecture & Flow

### **1. Main Entry Point**
```python
research_investment(query, context) → ResearchPlan
```

**Input:** 
- Investment query (e.g., "Should I invest in AAPL for long-term growth?")
- Research context (client preferences, timeframe, risk tolerance)

**Output:**
- Complete research plan with executed steps and accumulated knowledge

### **2. Two-Phase Execution**

#### **Phase 1: Planning Agent**
- **Agent:** `PlanningAgent` 
- **Input Schema:** `InvestmentQuery(query, context)`
- **Process:** Generates 2-4 logical research steps following investment methodology:
  1. Data gathering (financials, market data)
  2. Analysis (competitive position, growth drivers)  
  3. Valuation (metrics, comparisons)
  4. Recommendation (investment thesis)
- **Output Schema:** `ResearchPlan` with structured steps and reasoning

#### **Phase 2: Orchestrator Execution**
- **Core:** `OrchestratorCore` executes each step sequentially
- **Process:** For each step:
  1. Creates `ExecutionContext` with accumulated knowledge
  2. Uses orchestrator agent to select appropriate tool
  3. Executes tool with investment-focused parameters
  4. Accumulates findings using `ContextAccumulator`
  5. Updates step status and results

## Tool Ecosystem

### **1. RAG Search Tool (Sub-Agent Architecture)**
**Flow:** Query → Query Agent → Vector Search → QA Agent → Answer

**Sub-Agents:**
- **RAG Query Agent:** Converts questions into semantic search queries
- **RAG QA Agent:** Synthesizes retrieved document chunks into answers

**Data Source:** Internal knowledge base (SEC filings, earnings transcripts, analyst reports for AAPL/MSFT)

### **2. Deep Research Tool (Sub-Agent Architecture)**  
**Flow:** Query → Query Agent → Search → Scrape → Choice Agent → QA Agent → Answer

**Sub-Agents:**
- **Query Agent:** Generates diverse search queries for comprehensive coverage
- **Choice Agent:** Decides if additional searches are needed
- **QA Agent:** Synthesizes scraped web content into comprehensive answers

**Data Source:** Real-time web search via SearxNG + webpage scraping

### **3. Web Search Tool**
**Function:** External market information and news via SearxNG
**Integration:** Direct tool execution without sub-agents

### **4. Calculator Tool**
**Function:** Financial calculations, ratios, and metrics
**Integration:** Direct computational tool

## Data Flow Architecture

```
Investment Query
    ↓
Planning Agent (atomic-agents) 
    ↓
Research Plan (2-4 steps)
    ↓
For Each Step:
    ExecutionContext → OrchestratorCore → Tool Selection → Tool Execution
    ↓
    Tool Results → ContextAccumulator → Updated Knowledge
    ↓
Final Research Plan with Accumulated Knowledge
```

## Key Technical Features

### **Schema-Driven Design**
- **3 Core Schemas:** `InvestmentQuery`, `PlanStep`, `ResearchPlan`
- **Type Safety:** Pydantic validation throughout
- **Clear Contracts:** Structured input/output for all components

### **Context Management**
- **Accumulation:** Knowledge builds across steps
- **Summarization:** Tool results summarized by type
- **Token Management:** Smart truncation to prevent overflow

### **Atomic Agents Integration**
- **Planning Agent:** Uses instructor client with structured outputs
- **Orchestrator Agent:** Tool selection and parameter generation
- **Sub-Agents:** Specialized query generation and synthesis agents

### **Error Handling & Resilience**
- **Step-Level:** Individual step failures don't stop execution
- **Tool-Level:** Graceful degradation for tool failures
- **Memory Management:** Agent memory reset between steps

## Sub-Agent Query Generation Pattern

Both RAG and DeepResearch tools follow this pattern:
1. **Query Generation:** Specialized agent creates optimized queries
2. **Tool Execution:** Query used with search/retrieval tool
3. **Response Generation:** Another agent synthesizes results
4. **Context Management:** Results passed back to orchestrator

This creates a sophisticated multi-agent system where each tool has internal intelligence for query optimization and response synthesis.

## Detailed Component Analysis

### Planning Agent Structure

#### **Core Components:**
- **schemas.py**: 3 clean, focused schemas for complete data flow
- **investment_agent.py**: Main orchestration with three key functions:
  - `create_planning_agent()`: Creates atomic agent for research plan generation
  - `execute_research_plan()`: Executes plans using orchestration engine
  - `research_investment()`: Single entry point combining planning and execution

#### **Schema Structure:**
```python
# Input Schema
class InvestmentQuery(BaseIOSchema):
    query: str                    # The investment question
    context: str = ""            # Additional context

# Individual Step Schema  
class PlanStep(BaseIOSchema):
    description: str             # What this step accomplishes
    status: str = "pending"      # pending/completed/failed
    result: Dict[str, Any] = {}  # Execution results

# Complete Plan Schema
class ResearchPlan(BaseIOSchema):
    query: str                   # Original query
    context: str                 # Research context
    steps: List[PlanStep]        # 2-4 ordered steps
    reasoning: str               # Planning rationale
    status: str = "pending"      # Overall status
    accumulated_knowledge: str   # Findings accumulation
    success: bool = False        # Success flag
```

### Orchestration Engine Architecture

#### **Core Components:**
- **OrchestratorCore**: Main execution engine with `execute_with_context()` method
- **ToolManager**: Tool registry with validation and execution logic
- **ConfigManager**: Configuration and tool initialization
- **Context Utilities**: Context accumulation and management

#### **Execution Flow:**
1. **Tool Selection**: Orchestrator agent analyzes context and selects appropriate tool
2. **Parameter Generation**: Creates tool-specific input schemas
3. **Tool Execution**: ToolManager routes to appropriate tool
4. **Result Processing**: ContextAccumulator summarizes and merges findings
5. **Context Update**: Updated knowledge passed to next step

### RAG Tool Sub-Agent Architecture

#### **Components:**
- **RAGQueryAgent**: Converts user questions into semantic search queries
- **RAGQuestionAnsweringAgent**: Synthesizes retrieved chunks into answers
- **RAGContextProvider**: Manages retrieved document chunks
- **ChromaDBService**: Vector database operations

#### **Flow:**
```
User Query → RAGQueryAgent → Semantic Query → Vector Search → 
Retrieved Chunks → RAGContextProvider → QA Agent → Final Answer
```

### DeepResearch Tool Sub-Agent Architecture

#### **Components:**
- **QueryAgent**: Generates multiple diverse search queries
- **ChoiceAgent**: Decides if additional searches are needed
- **QuestionAnsweringAgent**: Synthesizes web content into answers
- **ScrapedContentContextProvider**: Manages scraped content with token limits
- **SearxNGSearchTool** + **WebpageScraperTool**: External data gathering

#### **Flow:**
```
Research Query → QueryAgent → Search Queries → SearxNG Search → 
URLs → WebpageScraper → Content → ScrapedContentContextProvider → 
ChoiceAgent (decision) → [Optional: Additional Search Loop] → 
QA Agent → Final Answer + Follow-ups
```

## Key Design Patterns

### **1. Schema-Driven Architecture**
All components communicate via Pydantic schemas ensuring type safety and validation throughout the system.

### **2. Separation of Concerns**
- **Controllers**: High-level decision making and planning
- **Orchestration Engine**: Reusable execution infrastructure  
- **Tools**: Specialized research capabilities

### **3. Context Management**
- `ExecutionContext` carries state between steps
- `ContextAccumulator` intelligently merges findings
- Knowledge builds incrementally across research steps

### **4. Single Entry Point**
```python
# Complete workflow in one function call
result = research_investment(
    query="Should I invest in AAPL for long-term growth?",
    context="AAPL recently launched new products. Market sentiment is mixed."
)
```

# Pydantic-AI Migration Plan

## Migration Philosophy: Trust Pydantic-AI's Natural Patterns

The key principle for this migration is to **trust pydantic-ai's built-in agent loop** rather than recreating complex orchestration patterns. Each agent should be an atomic unit following the natural pattern:

**Input → LLM Call → Tool Call → Tool Response → LLM Decision → Loop**

## Target Architecture (Following Pydantic-AI Best Practices)

### **Simplified Directory Structure**
```
agents/
├── __init__.py
├── planning_agent.py          # Pure planning logic
├── research_agent.py          # Execution with tools
└── dependencies.py           # Shared context and resources

tools/
├── __init__.py
├── vector_search.py          # RAG search functions
├── web_search.py            # SearxNG integration
├── web_scraper.py           # BeautifulSoup scraping
└── calculator.py            # Financial calculations

models/
├── __init__.py
└── schemas.py               # Clean Pydantic models
```

### **Core Principle: Leverage Pydantic-AI's Natural Tool Loop**

**Current Pattern (Complex):**
```
RAG Tool: Query Agent → Search → QA Agent
DeepResearch: Query Agent → Search → Choice Agent → QA Agent  
```

**Pydantic-AI Pattern (Natural):**
```python
from pydantic_ai import Agent, RunContext

# Dependencies for type-safe context sharing
class ResearchDependencies(BaseModel):
    vector_db: ChromaDB
    searxng_client: SearxNGClient
    knowledge_base: KnowledgeBase

@research_agent.tool
async def search_internal_docs(
    ctx: RunContext[ResearchDependencies], 
    query: str
) -> str:
    """Search internal investment documents and SEC filings."""
    results = await ctx.deps.vector_db.query(query, n_results=5)
    return format_rag_results(results)

@research_agent.tool
async def search_web(
    ctx: RunContext[ResearchDependencies],
    query: str
) -> str:
    """Search web for current market information and news."""
    results = await ctx.deps.searxng_client.search(query)
    # Let the LLM decide if it needs to scrape specific pages
    return format_search_results(results)

@research_agent.tool
async def scrape_webpage(
    ctx: RunContext[ResearchDependencies],
    url: str
) -> str:
    """Scrape specific webpage content using BeautifulSoup."""
    soup = await fetch_and_parse(url)
    return extract_relevant_content(soup)
```

## Migration Strategy

### **Phase 1: Dependencies and Context Setup**

#### **1.1 Shared Dependencies (Pydantic-AI Pattern)**
```python
# agents/dependencies.py
from pydantic import BaseModel
from typing import Optional

class ResearchDependencies(BaseModel):
    """Shared context for investment research agents."""
    vector_db: ChromaDB
    searxng_client: SearxNGClient
    current_query: str
    research_context: str = ""
    accumulated_findings: str = ""
    
    class Config:
        arbitrary_types_allowed = True
```

#### **1.2 Planning Agent (Structured Output)**
```python
# agents/planning_agent.py
from pydantic_ai import Agent
from pydantic import BaseModel
from typing import List

class ResearchStep(BaseModel):
    description: str
    focus_area: str
    expected_outcome: str

class ResearchPlan(BaseModel):
    steps: List[ResearchStep]
    reasoning: str
    priority_areas: List[str]

planning_agent = Agent(
    'gpt-4',
    result_type=ResearchPlan,
    system_prompt="""You are an expert investment research planner.
    Create 2-4 logical research steps following investment methodology:
    1. Data gathering (financials, market position)
    2. Analysis (competitive landscape, growth drivers)  
    3. Valuation (metrics, comparisons)
    4. Investment recommendation
    
    Consider the client's context and risk tolerance."""
)

# Usage
async def create_research_plan(query: str, context: str = "") -> ResearchPlan:
    return await planning_agent.run(f"Investment Query: {query}\nContext: {context}")
```

### **Phase 2: Research Agent with Natural Tool Loop**

#### **2.1 Main Research Agent**
```python
# agents/research_agent.py
from pydantic_ai import Agent, RunContext
from .dependencies import ResearchDependencies

class InvestmentFindings(BaseModel):
    summary: str
    key_insights: List[str]
    financial_metrics: Dict[str, float]
    risk_factors: List[str]
    sources: List[str]
    confidence_score: float

research_agent = Agent(
    'gpt-4',
    deps_type=ResearchDependencies,
    result_type=InvestmentFindings,
    system_prompt="""You are an expert investment researcher.
    
    Use available tools to gather comprehensive information:
    - search_internal_docs: For SEC filings, earnings reports, analyst reports
    - search_web: For current market news and trends  
    - scrape_webpage: For specific article content
    - calculate_metrics: For financial analysis
    
    You decide when to use each tool and when you have enough information.
    Build comprehensive analysis through multiple tool calls as needed."""
)
```

#### **2.2 Tool Functions (Simple and Focused)**
```python
@research_agent.tool
async def search_internal_docs(
    ctx: RunContext[ResearchDependencies], 
    query: str,
    doc_type: str = "all"
) -> str:
    """Search internal investment documents (SEC filings, earnings, analyst reports).
    
    Args:
        query: Search query for documents
        doc_type: Type of document (10k, 10q, earnings, analyst, all)
    """
    results = await ctx.deps.vector_db.query(
        query, 
        filters={"doc_type": doc_type} if doc_type != "all" else None,
        n_results=5
    )
    return format_document_results(results)

@research_agent.tool
async def search_web(
    ctx: RunContext[ResearchDependencies],
    query: str,
    focus: str = "news"
) -> str:
    """Search web using SearxNG for current market information.
    
    Args:
        query: Search query
        focus: Search focus (news, analysis, general)
    """
    search_params = {
        "q": query,
        "categories": "news" if focus == "news" else "general",
        "engines": "google,bing,yahoo" if focus == "general" else "google news,bing news"
    }
    results = await ctx.deps.searxng_client.search(**search_params)
    return format_web_results(results)

@research_agent.tool
async def scrape_webpage(
    ctx: RunContext[ResearchDependencies],
    url: str,
    content_type: str = "article"
) -> str:
    """Scrape webpage content using BeautifulSoup.
    
    Args:
        url: URL to scrape
        content_type: Type of content to extract (article, table, full)
    """
    soup = await fetch_with_beautifulsoup(url)
    if content_type == "article":
        content = extract_article_content(soup)
    elif content_type == "table":
        content = extract_tables(soup)
    else:
        content = extract_main_content(soup)
    
    return f"Content from {url}:\n{content}"

@research_agent.tool
async def calculate_financial_metrics(
    ctx: RunContext[ResearchDependencies],
    financial_data: str,
    metrics: List[str]
) -> str:
    """Calculate financial ratios and metrics.
    
    Args:
        financial_data: Raw financial data or statements
        metrics: List of metrics to calculate (pe_ratio, debt_ratio, roe, etc.)
    """
    return perform_financial_calculations(financial_data, metrics)
```

### **Phase 3: Simplified Orchestration**

#### **3.1 Main Entry Point (Clean Integration)**
```python
# main.py
async def research_investment(
    query: str, 
    context: str = "",
    model: str = "gpt-4"
) -> InvestmentAnalysis:
    """Complete investment research workflow using pydantic-ai agents."""
    
    # Initialize dependencies
    deps = ResearchDependencies(
        vector_db=await init_chroma_db(),
        searxng_client=init_searxng_client(),
        current_query=query,
        research_context=context
    )
    
    # Step 1: Create research plan
    plan = await create_research_plan(query, context)
    
    # Step 2: Execute research with natural tool looping
    # The agent will automatically use tools as needed
    findings = await research_agent.run(
        f"Research Plan: {plan.model_dump()}\n"
        f"Investment Query: {query}\n"
        f"Context: {context}",
        deps=deps
    )
    
    return InvestmentAnalysis(
        query=query,
        context=context,
        plan=plan,
        findings=findings,
        recommendation=synthesize_recommendation(plan, findings)
    )
```

#### **3.2 Tool Implementation Details**

**SearxNG Integration:**
```python
# tools/web_search.py
import aiohttp
from typing import Dict, List

class SearxNGClient:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
    
    async def search(self, q: str, **params) -> Dict:
        async with aiohttp.ClientSession() as session:
            params.update({"q": q, "format": "json"})
            async with session.get(f"{self.base_url}/search", params=params) as resp:
                return await resp.json()
```

**BeautifulSoup Scraping:**
```python
# tools/web_scraper.py
import aiohttp
from bs4 import BeautifulSoup
from typing import Optional

async def fetch_with_beautifulsoup(url: str) -> BeautifulSoup:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
            return BeautifulSoup(html, 'html.parser')

def extract_article_content(soup: BeautifulSoup) -> str:
    # Extract main article content
    selectors = ['article', '.article-content', '.post-content', 'main']
    for selector in selectors:
        content = soup.select_one(selector)
        if content:
            return content.get_text(strip=True)
    return soup.get_text(strip=True)[:5000]  # Fallback with limit
```

## Key Simplifications Using Pydantic-AI

### **1. Natural Agent Loops**
- No complex orchestration needed
- Agent decides when to call tools
- Agent manages conversation context
- Agent determines when research is complete

### **2. Type-Safe Dependencies**
```python
# Shared context across tools
class ResearchDependencies(BaseModel):
    vector_db: ChromaDB
    searxng_client: SearxNGClient
    current_findings: str = ""
```

### **3. Eliminate Sub-Agent Complexity**
**Before:** Separate agents for query generation, choice making, synthesis
**After:** Single agent with natural tool calls and decision making

### **4. Clean Tool Definitions**
```python
@agent.tool
async def search_tool(ctx: RunContext[Deps], query: str) -> str:
    """Clear docstring for LLM understanding."""
    # Simple, focused function
    return perform_search(query)
```

## Implementation Steps

### **Step 1: Setup Dependencies**
1. Add pydantic-ai to requirements
2. Create dependencies module
3. Setup SearxNG and BeautifulSoup integrations

### **Step 2: Planning Agent**
1. Create simple planning agent
2. Test with investment queries
3. Verify structured output generation

### **Step 3: Research Agent with Tools**
1. Create research agent with tools
2. Test natural tool selection
3. Verify multi-tool usage patterns

### **Step 4: Integration**
1. Connect planning → research
2. Test complete workflows
3. Compare with current system

## Benefits of Pydantic-AI Approach

### **1. Natural Agent Behavior**
- Agents decide tool usage organically
- No forced orchestration patterns
- Natural conversation flows

### **2. Type Safety**
- RunContext with typed dependencies
- Pydantic validation throughout
- Clear tool contracts

### **3. Simplified Architecture**
- 4-5 files instead of 15+
- Clear separation of concerns
- Standard pydantic-ai patterns

### **4. Enhanced Capabilities**
- SearxNG for comprehensive web search
- BeautifulSoup for content extraction
- Natural multi-tool research workflows

The migration leverages pydantic-ai's strengths: natural agent loops, type-safe dependencies, and clean tool integration while adding robust web search and scraping capabilities.
