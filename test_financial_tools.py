#!/usr/bin/env python3
"""Test script for financial data tools integration with research agent."""

import asyncio
import os
from dotenv import load_dotenv
from rich import print as rprint
from agents.dependencies import initialize_dependencies
from agents.research_agent import research_agent
from pydantic_ai import RunContext

# Load environment variables
load_dotenv()


async def test_financial_tools():
    """Test the financial data tools through the research agent."""
    
    # Check if API key is available
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        rprint("[yellow]Warning: ALPHA_VANTAGE_API_KEY not set. Financial data tools will not work.[/yellow]")
        rprint("[info]Get a free API key at: https://www.alphavantage.co/support/#api-key[/info]")
        return
    
    # Initialize dependencies
    deps = initialize_dependencies(
        query="Test financial data tools for AAPL",
        context="Testing real-time data integration"
    )
    
    rprint("[green]Testing Financial Data Tools Integration[/green]\n")
    
    # Test 1: Get stock quote
    rprint("[bold]Test 1: Getting real-time stock quote for AAPL[/bold]")
    prompt = "Use the get_stock_quote tool to get the current price for AAPL"
    
    try:
        result = await research_agent.run(prompt, deps=deps)
        rprint("[green]✓ Stock quote retrieved successfully[/green]")
        rprint(f"Result: {result.data}")
    except Exception as e:
        rprint(f"[red]✗ Failed to get stock quote: {e}[/red]")
    
    # Test 2: Get historical data
    rprint("\n[bold]Test 2: Getting historical price analysis for MSFT[/bold]")
    prompt = "Use the get_stock_history tool to analyze MSFT's daily price trends"
    
    try:
        result = await research_agent.run(prompt, deps=deps)
        rprint("[green]✓ Historical data retrieved successfully[/green]")
        rprint(f"Result: {result.data}")
    except Exception as e:
        rprint(f"[red]✗ Failed to get historical data: {e}[/red]")
    
    # Test 3: Get financial fundamentals
    rprint("\n[bold]Test 3: Getting financial fundamentals for GOOGL[/bold]")
    prompt = "Use the get_stock_fundamentals tool to get the latest financial statement data for GOOGL"
    
    try:
        result = await research_agent.run(prompt, deps=deps)
        rprint("[green]✓ Financial fundamentals retrieved successfully[/green]")
        rprint(f"Result: {result.data}")
    except Exception as e:
        rprint(f"[red]✗ Failed to get financial fundamentals: {e}[/red]")
    
    # Test 4: Combined analysis
    rprint("\n[bold]Test 4: Comprehensive analysis using multiple tools[/bold]")
    prompt = """Analyze AAPL as an investment opportunity using:
    1. Real-time stock quote
    2. Historical price trends (weekly)
    3. Financial fundamentals
    Provide a brief investment summary based on the data."""
    
    try:
        result = await research_agent.run(prompt, deps=deps)
        rprint("[green]✓ Comprehensive analysis completed successfully[/green]")
        rprint(f"\nAnalysis Summary:\n{result.data}")
    except Exception as e:
        rprint(f"[red]✗ Failed comprehensive analysis: {e}[/red]")


if __name__ == "__main__":
    rprint("\n[bold cyan]Financial Data Tools Integration Test[/bold cyan]")
    rprint("=" * 50)
    asyncio.run(test_financial_tools())
    rprint("\n[green]Test completed![/green]")