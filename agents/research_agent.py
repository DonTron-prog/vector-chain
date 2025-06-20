"""Investment research agent with natural tool loops using pydantic-ai."""

from pydantic_ai import Agent, RunContext
from agents.dependencies import ResearchDependencies
from models.schemas import InvestmentFindings, ExecutionFeedback
from config import get_openai_model
from .memory_processors import filter_research_responses

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

TOOL USAGE EFFICIENCY:
- Batch similar tool calls together when possible (e.g., multiple financial_metrics calculations)
- Use comprehensive searches rather than incremental ones
- Avoid repetitive calls to the same tool with similar parameters
- Aim for 3-5 tool calls per step maximum for efficiency

You decide when to use each tool and when you have sufficient information.
Build your analysis through targeted, comprehensive tool usage.
Focus on actionable insights and clear risk/return assessment.
Always provide a confidence score based on data quality and comprehensiveness."""
)


feedback_agent = Agent(
    openai_model,
    deps_type=ResearchDependencies,
    result_type=ExecutionFeedback,
    system_prompt="""You are a research execution evaluator that generates feedback for adaptive planning.

Your role is to assess the quality and completeness of research findings from a completed step and provide structured feedback to help improve the overall research plan.

EVALUATION CRITERIA:
- Findings Quality (0-1): How comprehensive and useful are the findings?
- Data Gaps: What important information is missing or unclear?
- Unexpected Findings: What valuable discoveries weren't anticipated?
- Confidence Level (0-1): How confident are you in the research direction?

FEEDBACK GUIDELINES:
- Be specific about data gaps and their impact
- Highlight unexpected findings that could change strategy
- Suggest concrete plan adjustments
- Assess whether current approach will achieve objectives
- Consider time and resource constraints

Your feedback helps the planning agent decide whether to adapt the research strategy."""
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


async def generate_execution_feedback(
    step_description: str,
    findings: InvestmentFindings,
    original_expectations: str,
    deps: ResearchDependencies
) -> ExecutionFeedback:
    """Generate structured feedback about research execution for adaptive planning.
    
    Args:
        step_description: Description of the completed research step
        findings: Research findings from the step
        original_expectations: What was expected from this step
        deps: Research dependencies
        
    Returns:
        ExecutionFeedback: Structured feedback for planning agent
    """
    prompt = f"""RESEARCH STEP EVALUATION

Completed Step: {step_description}
Original Expectations: {original_expectations}

FINDINGS SUMMARY:
- Key Insights: {findings.key_insights}
- Risk Factors: {findings.risk_factors}
- Opportunities: {findings.opportunities}
- Confidence Score: {findings.confidence_score}
- Sources Used: {len(findings.sources)}

RESEARCH CONTEXT: {deps.research_context}

Evaluate this research step execution and provide structured feedback:

1. How well did the findings meet expectations? (findings_quality: 0-1)
2. What important data is still missing? (data_gaps)
3. What unexpected valuable discoveries were made? (unexpected_findings)
4. How confident are you in the current research direction? (confidence_level: 0-1)
5. What adjustments would improve the remaining research? (suggested_adjustments)

Consider data quality, completeness, and strategic value of findings."""

    result = await feedback_agent.run(prompt, deps=deps)
    return result.data