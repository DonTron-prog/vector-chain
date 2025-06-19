"""Investment research agent with natural tool loops using pydantic-ai."""

from pydantic_ai import Agent, RunContext
from agents.dependencies import ResearchDependencies
from models.schemas import InvestmentFindings
from config import get_openai_model

# Configure OpenRouter
openai_model = get_openai_model()
from tools.vector_search import search_internal_docs as _search_internal_docs, format_document_results, search_with_query_enhancement
from tools.web_search import search_web as _search_web, format_search_results  
from tools.web_scraper import scrape_webpage as _scrape_webpage
from tools.calculator import perform_financial_calculations


research_agent = Agent(
    openai_model,
    deps_type=ResearchDependencies,
    result_type=InvestmentFindings,
    system_prompt="""You are an expert investment researcher with access to comprehensive research tools.

Use available tools to gather information and build a complete investment analysis:

- search_internal_docs: Search SEC filings, earnings reports, analyst reports in vector database
- search_web: Search current market news, trends, and analysis 
- scrape_webpage: Extract detailed content from specific web pages
- calculate_financial_metrics: Calculate financial ratios and metrics

RESEARCH APPROACH:
1. Start by understanding the investment query and research plan
2. Search internal documents for fundamental company data (financials, business model, risks)
3. Search web for current market sentiment, news, and trends
4. Scrape specific pages for detailed analysis when needed
5. Calculate relevant financial metrics from gathered data
6. Synthesize findings into comprehensive investment analysis

You decide when to use each tool and when you have sufficient information.
Build your analysis through multiple tool calls as needed.
Focus on actionable insights and clear risk/return assessment.
Always provide a confidence score based on data quality and comprehensiveness."""
)


@research_agent.tool
async def search_internal_docs(
    ctx: RunContext[ResearchDependencies], 
    query: str,
    doc_type: str = "all",
    enhance_query: bool = True
) -> str:
    """Search internal investment documents (SEC filings, earnings, analyst reports) with enhanced query processing.
    
    Args:
        query: Search query for documents
        doc_type: Type of document (10k, 10q, earnings, analyst, all)
        enhance_query: Whether to enhance query for better retrieval
    """
    if enhance_query and ctx.deps.research_context:
        results, enhanced_query = await search_with_query_enhancement(
            ctx.deps.vector_db,
            query,
            doc_type=doc_type,
            n_results=5,
            research_context=ctx.deps.research_context
        )
        return f"Query Enhanced: '{enhanced_query}'\n\n{format_document_results(results)}"
    else:
        results = await _search_internal_docs(
            ctx.deps.vector_db,
            query,
            doc_type=doc_type,
            n_results=5,
            enhance_query=enhance_query
        )
        return format_document_results(results)


@research_agent.tool
async def search_web(
    ctx: RunContext[ResearchDependencies],
    query: str,
    category: str = "general"
) -> str:
    """Search web for current market information and news.
    
    Args:
        query: Search query
        category: Search category (general, news, social_media)
    """
    results = await _search_web(
        ctx.deps.searxng_client,
        query,
        category=category,
        max_results=8
    )
    return format_search_results(results)


@research_agent.tool
async def scrape_webpage(
    ctx: RunContext[ResearchDependencies],
    url: str,
    content_type: str = "article"
) -> str:
    """Scrape specific webpage content for detailed analysis.
    
    Args:
        url: URL to scrape
        content_type: Type of content to extract (article, table, full)
    """
    content = await _scrape_webpage(url, content_type)
    return content


@research_agent.tool
async def calculate_financial_metrics(
    ctx: RunContext[ResearchDependencies],
    financial_data: str,
    metrics: list[str]
) -> str:
    """Calculate financial ratios and metrics from data.
    
    Args:
        financial_data: Raw financial data or statements
        metrics: List of metrics to calculate (pe_ratio, debt_ratio, roe, profit_margin, etc.)
    """
    return perform_financial_calculations(financial_data, metrics)


async def conduct_research(
    query: str,
    research_plan: str,
    deps: ResearchDependencies
) -> InvestmentFindings:
    """Conduct comprehensive investment research using natural tool loops.
    
    Args:
        query: Investment query
        research_plan: Research plan from planning agent
        deps: Research dependencies
        
    Returns:
        Complete investment findings
    """
    prompt = f"""Investment Query: {query}

Research Plan: {research_plan}

Current Context: {deps.research_context}

Conduct comprehensive investment research following the plan. Use all available tools to gather data, analyze the investment opportunity, and provide actionable insights."""

    result = await research_agent.run(prompt, deps=deps)
    return result.data