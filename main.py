"""Main entry point for pydantic-ai investment research system."""

import os
import asyncio
from agents.dependencies import initialize_dependencies
from agents.planning_agent import create_research_plan
from agents.research_agent import conduct_research
from models.schemas import InvestmentAnalysis
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


async def research_investment(
    query: str, 
    context: str = "",
    searxng_url: str = "http://localhost:8080",
    chroma_path: str = "./investment_chroma_db",
    knowledge_path: str = "./knowledge_base"
) -> InvestmentAnalysis:
    """Complete investment research workflow using pydantic-ai agents.
    
    Args:
        query: Investment question to research
        context: Additional context about the client or situation
        searxng_url: SearxNG instance URL
        chroma_path: ChromaDB persistence path
        knowledge_path: Knowledge base path
        
    Returns:
        Complete investment analysis
    """
    console = Console()
    console.print(f"🔍 [bold blue]Starting investment research for:[/bold blue] {query}")
    
    try:
        # Initialize dependencies
        deps = initialize_dependencies(
            query=query,
            context=context,
            searxng_url=searxng_url,
            chroma_path=chroma_path,
            knowledge_path=knowledge_path
        )
        
        # Step 1: Create research plan
        console.print("📋 [yellow]Creating research plan...[/yellow]")
        plan = await create_research_plan(query, context)
        
        console.print(f"✅ [green]Plan created with {len(plan.steps)} steps:[/green]")
        for i, step in enumerate(plan.steps, 1):
            console.print(f"  {i}. [cyan]{step.description}[/cyan]")
            console.print(f"     Focus: [dim]{step.focus_area}[/dim]")
        
        # Step 2: Conduct research with natural tool looping
        console.print("\\n🔬 [yellow]Conducting research...[/yellow]")
        research_plan_text = f"Steps: {[step.model_dump() for step in plan.steps]}\\nReasoning: {plan.reasoning}"
        
        findings = await conduct_research(
            query=query,
            research_plan=research_plan_text,
            deps=deps
        )
        
        # Step 3: Create final analysis
        analysis = InvestmentAnalysis(
            query=query,
            context=context,
            plan=plan,
            findings=findings
        )
        
        console.print("\\n🎯 [bold green]Research completed successfully![/bold green]")
        return analysis
        
    except Exception as e:
        console.print(f"❌ [bold red]Research failed:[/bold red] {str(e)}")
        raise


def display_analysis_summary(analysis: InvestmentAnalysis):
    """Display formatted analysis summary."""
    console = Console()
    
    # Create summary panel
    summary_panel = Panel(
        analysis.findings.summary,
        title="📊 Investment Analysis Summary",
        border_style="blue"
    )
    console.print(summary_panel)
    
    # Create metrics table if available
    if any([
        analysis.findings.financial_metrics.pe_ratio,
        analysis.findings.financial_metrics.debt_to_equity,
        analysis.findings.financial_metrics.return_on_equity
    ]):
        table = Table(title="💰 Financial Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        metrics = analysis.findings.financial_metrics
        if metrics.pe_ratio:
            table.add_row("P/E Ratio", f"{metrics.pe_ratio:.2f}")
        if metrics.debt_to_equity:
            table.add_row("Debt/Equity", f"{metrics.debt_to_equity:.2f}")
        if metrics.return_on_equity:
            table.add_row("ROE", f"{metrics.return_on_equity:.2%}")
        if metrics.profit_margin:
            table.add_row("Profit Margin", f"{metrics.profit_margin:.2%}")
        
        console.print(table)
    
    # Key insights
    if analysis.findings.key_insights:
        console.print("\\n🔑 [bold yellow]Key Insights:[/bold yellow]")
        for insight in analysis.findings.key_insights:
            console.print(f"  • {insight}")
    
    # Risk factors
    if analysis.findings.risk_factors:
        console.print("\\n⚠️  [bold red]Risk Factors:[/bold red]")
        for risk in analysis.findings.risk_factors:
            console.print(f"  • {risk}")
    
    # Recommendation
    recommendation_panel = Panel(
        analysis.findings.recommendation,
        title="🎯 Investment Recommendation",
        border_style="green"
    )
    console.print(recommendation_panel)
    
    # Confidence and sources
    console.print(f"\\n📈 [bold]Confidence Score:[/bold] {analysis.findings.confidence_score:.1%}")
    console.print(f"📚 [bold]Sources Used:[/bold] {len(analysis.findings.sources)}")


async def main():
    """Main function for testing the investment research system."""
    console = Console()
    
    # Test scenarios - simplified for comparison
    test_queries = [
        {
            "query": "Should I invest in AAPL for long-term growth?",
            "context": "Looking for a 3-5 year investment horizon. Risk tolerance is moderate."
        }
    ]
    
    for i, scenario in enumerate(test_queries, 1):
        console.print(f"\\n{'='*50}")
        console.print(f"[bold blue]Test Scenario {i}[/bold blue]")
        console.print(f"Query: {scenario['query']}")
        console.print(f"Context: {scenario['context']}")
        console.print('='*50)
        
        try:
            analysis = await research_investment(
                query=scenario["query"],
                context=scenario["context"]
            )
            
            display_analysis_summary(analysis)
            
        except Exception as e:
            console.print(f"❌ [bold red]Test failed:[/bold red] {str(e)}")
        
        console.print("\\n" + "="*50)


if __name__ == "__main__":
    # Ensure required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable is required")
        exit(1)
    
    asyncio.run(main())