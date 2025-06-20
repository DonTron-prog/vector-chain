"""Main entry point for pydantic-ai investment research system."""

import os
import asyncio
from agents.dependencies import initialize_dependencies
from agents.planning_agent import create_research_plan, evaluate_plan_update
from agents.research_agent import conduct_research, generate_execution_feedback
from models.schemas import InvestmentAnalysis, AdaptivePlan, PlanUpdateRequest, ExecutionFeedback
from pydantic_ai.messages import ModelMessage
from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from logfire_config import configure_logfire, create_logfire_span, log_research_start, log_research_complete, log_research_error

# Configure Logfire for observability
logfire = configure_logfire()


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
    
    # Log research start
    log_research_start(query, context)
    
    # Add Logfire tracing for the entire research workflow
    with create_logfire_span("investment_research", query=query, context=context):
        try:
            # Initialize dependencies
            with create_logfire_span("initialize_dependencies"):
                deps = initialize_dependencies(
                    query=query,
                    context=context,
                    searxng_url=searxng_url,
                    chroma_path=chroma_path,
                    knowledge_path=knowledge_path
                )
            
            # Step 1: Create research plan
            console.print("📋 [yellow]Creating research plan...[/yellow]")
            with create_logfire_span("create_research_plan"):
                plan = await create_research_plan(query, context)
            
            console.print(f"✅ [green]Plan created with {len(plan.steps)} steps:[/green]")
            for i, step in enumerate(plan.steps, 1):
                console.print(f"  {i}. [cyan]{step.description}[/cyan]")
                console.print(f"     Focus: [dim]{step.focus_area}[/dim]")
            
            # Step 2: Conduct research with natural tool looping
            console.print("\\n🔬 [yellow]Conducting research...[/yellow]")
            research_plan_text = f"Steps: {[step.model_dump() for step in plan.steps]}\\nReasoning: {plan.reasoning}"
            
            with create_logfire_span("conduct_research"):
                findings = await conduct_research(
                    query=query,
                    research_plan=research_plan_text,
                    deps=deps
                )
            
            # Step 3: Create final analysis
            with create_logfire_span("create_final_analysis"):
                analysis = InvestmentAnalysis(
                    query=query,
                    context=context,
                    plan=plan,
                    findings=findings
                )
            
            console.print("\\n🎯 [bold green]Research completed successfully![/bold green]")
            log_research_complete(query, analysis.findings.confidence_score, len(analysis.findings.sources))
            return analysis
            
        except Exception as e:
            console.print(f"❌ [bold red]Research failed:[/bold red] {str(e)}")
            log_research_error(query, str(e), "execution")
            raise


async def adaptive_research_investment(
    query: str, 
    context: str = "",
    searxng_url: str = "http://localhost:8080",
    chroma_path: str = "./investment_chroma_db",
    knowledge_path: str = "./knowledge_base",
    max_adaptations: int = 3
) -> InvestmentAnalysis:
    """Adaptive investment research workflow with memory and plan updates.
    
    Args:
        query: Investment question to research
        context: Additional context about the client or situation
        searxng_url: SearxNG instance URL
        chroma_path: ChromaDB persistence path
        knowledge_path: Knowledge base path
        max_adaptations: Maximum number of plan adaptations allowed
        
    Returns:
        Complete investment analysis with adaptive planning
    """
    console = Console()
    console.print(f"🧠 [bold blue]Starting adaptive investment research for:[/bold blue] {query}")
    
    # Log research start
    log_research_start(query, context)
    
    # Add Logfire tracing for the entire adaptive research workflow
    with create_logfire_span("adaptive_investment_research", query=query, context=context):
        try:
            # Initialize dependencies
            with create_logfire_span("initialize_dependencies"):
                deps = initialize_dependencies(
                    query=query,
                    context=context,
                    searxng_url=searxng_url,
                    chroma_path=chroma_path,
                    knowledge_path=knowledge_path
                )
            
            # Step 1: Create initial research plan
            console.print("📋 [yellow]Creating initial research plan...[/yellow]")
            with create_logfire_span("create_initial_plan"):
                initial_plan = await create_research_plan(query, context)
            
            # Initialize adaptive plan
            adaptive_plan = AdaptivePlan(
                original_plan=initial_plan,
                current_steps=initial_plan.steps.copy(),
                completed_steps=[],
                adaptation_history=[],
                total_adaptations=0,
                current_confidence=0.5
            )
            
            console.print(f"✅ [green]Initial plan created with {len(adaptive_plan.current_steps)} steps[/green]")
            
            # Planning agent memory
            planning_messages: Optional[List[ModelMessage]] = None
            all_findings = []
            
            # Adaptive research loop
            step_number = 1
            while adaptive_plan.current_steps and adaptive_plan.total_adaptations <= max_adaptations:
                current_step = adaptive_plan.current_steps[0]
                
                console.print(f"\n🔬 [yellow]Step {step_number}: {current_step.description}[/yellow]")
                console.print(f"Focus: [dim]{current_step.focus_area}[/dim]")
                
                # Execute current research step
                with create_logfire_span("execute_research_step", step=step_number):
                    step_findings = await conduct_research(
                        query=f"Step {step_number}: {current_step.description}",
                        research_plan=f"Focus: {current_step.focus_area}\nExpected: {current_step.expected_outcome}",
                        deps=deps
                    )
                
                all_findings.append(step_findings)
                
                # Generate execution feedback
                with create_logfire_span("generate_feedback", step=step_number):
                    feedback = await generate_execution_feedback(
                        step_description=current_step.description,
                        findings=step_findings,
                        original_expectations=current_step.expected_outcome,
                        deps=deps
                    )
                
                console.print(f"📊 [cyan]Step feedback - Quality: {feedback.findings_quality:.2f}, Confidence: {feedback.confidence_level:.2f}[/cyan]")
                
                # Mark current step as completed
                adaptive_plan.completed_steps.append(adaptive_plan.current_steps.pop(0))
                
                # Check if plan needs adaptation (only if there are remaining steps)
                if adaptive_plan.current_steps and (
                    feedback.findings_quality < 0.6 or 
                    feedback.confidence_level < 0.5 or 
                    feedback.suggested_adjustments
                ):
                    console.print("🔄 [yellow]Evaluating plan adaptation...[/yellow]")
                    
                    with create_logfire_span("evaluate_plan_update", step=step_number):
                        update_request = PlanUpdateRequest(
                            current_step=step_number,
                            feedback=feedback,
                            remaining_steps=adaptive_plan.current_steps
                        )
                        
                        update_response, planning_messages = await evaluate_plan_update(
                            update_request, 
                            message_history=planning_messages
                        )
                    
                    if update_response.should_update and update_response.updated_steps:
                        console.print(f"🔄 [green]Plan updated: {update_response.reasoning}[/green]")
                        
                        # Update the adaptive plan
                        adaptive_plan.current_steps = update_response.updated_steps
                        adaptive_plan.total_adaptations += 1
                        adaptive_plan.current_confidence = update_response.confidence
                        adaptive_plan.adaptation_history.append(
                            f"Step {step_number}: {update_response.reasoning}"
                        )
                    else:
                        console.print(f"➡️  [dim]Continuing with current plan: {update_response.reasoning}[/dim]")
                
                step_number += 1
            
            # Combine all findings into final analysis
            with create_logfire_span("create_final_analysis"):
                # Merge findings from all steps
                final_insights = []
                final_risks = []
                final_opportunities = []
                final_sources = []
                total_confidence = 0.0
                
                for findings in all_findings:
                    final_insights.extend(findings.key_insights)
                    final_risks.extend(findings.risk_factors)
                    final_opportunities.extend(findings.opportunities)
                    final_sources.extend(findings.sources)
                    total_confidence += findings.confidence_score
                
                # Use the last findings as the base and enhance with aggregated data
                if all_findings:
                    final_findings = all_findings[-1]
                    final_findings.key_insights = list(set(final_insights))
                    final_findings.risk_factors = list(set(final_risks))
                    final_findings.opportunities = list(set(final_opportunities))
                    final_findings.sources = list(set(final_sources))
                    final_findings.confidence_score = min(total_confidence / len(all_findings), 1.0)
                else:
                    raise ValueError("No research findings generated")
                
                # Create final analysis with adaptive plan info
                analysis = InvestmentAnalysis(
                    query=query,
                    context=context,
                    plan=adaptive_plan.original_plan,
                    findings=final_findings
                )
            
            console.print("\\n🎯 [bold green]Adaptive research completed successfully![/bold green]")
            console.print(f"📈 [cyan]Plan adaptations: {adaptive_plan.total_adaptations}[/cyan]")
            console.print(f"📊 [cyan]Steps completed: {len(adaptive_plan.completed_steps)}[/cyan]")
            
            log_research_complete(query, final_findings.confidence_score, len(final_findings.sources))
            return analysis
            
        except Exception as e:
            console.print(f"❌ [bold red]Adaptive research failed:[/bold red] {str(e)}")
            log_research_error(query, str(e), "adaptive_execution")
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
    """Main function for testing both regular and adaptive research systems."""
    console = Console()
    
    # Test scenario
    test_scenario = {
        "query": "Should I invest in AAPL for long-term growth?",
        "context": "Looking for a 3-5 year investment horizon. Risk tolerance is moderate."
    }
    
    console.print(f"\\n{'='*60}")
    console.print(f"[bold blue]Investment Research Comparison[/bold blue]")
    console.print(f"Query: {test_scenario['query']}")
    console.print(f"Context: {test_scenario['context']}")
    console.print('='*60)
    
    # Test 1: Regular research
    console.print("\\n[bold yellow]1. Regular Research (Static Planning)[/bold yellow]")
    try:
        regular_analysis = await research_investment(
            query=test_scenario["query"],
            context=test_scenario["context"]
        )
        console.print("✅ [green]Regular research completed[/green]")
        
    except Exception as e:
        console.print(f"❌ [bold red]Regular research failed:[/bold red] {str(e)}")
        regular_analysis = None
    
    # Test 2: Adaptive research
    console.print("\\n[bold yellow]2. Adaptive Research (Memory & Plan Updates)[/bold yellow]")
    try:
        adaptive_analysis = await adaptive_research_investment(
            query=test_scenario["query"],
            context=test_scenario["context"],
            max_adaptations=2
        )
        console.print("✅ [green]Adaptive research completed[/green]")
        
    except Exception as e:
        console.print(f"❌ [bold red]Adaptive research failed:[/bold red] {str(e)}")
        adaptive_analysis = None
    
    # Display results comparison
    console.print("\\n" + "="*60)
    console.print("[bold cyan]Results Comparison[/bold cyan]")
    console.print("="*60)
    
    if regular_analysis:
        console.print("\\n[bold]Regular Research Summary:[/bold]")
        display_analysis_summary(regular_analysis)
    
    if adaptive_analysis:
        console.print("\\n[bold]Adaptive Research Summary:[/bold]")
        display_analysis_summary(adaptive_analysis)
    
    console.print("\\n" + "="*60)


if __name__ == "__main__":
    # Ensure required environment variables
    try:
        from config import get_required_env_var
        get_required_env_var("OPENROUTER_API_KEY")
    except RuntimeError as e:
        print(f"❌ {e}")
        exit(1)
    
    asyncio.run(main())