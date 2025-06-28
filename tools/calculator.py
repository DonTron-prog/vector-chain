"""Financial calculation tools."""

from typing import Dict, List, Any, Optional
import re
import os
import asyncio
from models.schemas import FinancialMetrics
from tools.financial_data import get_real_time_quote, get_financial_fundamentals


def parse_financial_value(value_str: str) -> Optional[float]:
    """Parse financial value string to float.
    
    Args:
        value_str: String like "$123.4M", "45.2B", "12.5%"
        
    Returns:
        Parsed float value or None if parsing fails
    """
    if not value_str or not isinstance(value_str, str):
        return None
    
    # Clean the string
    clean_str = value_str.strip().replace('$', '').replace(',', '')
    
    # Handle percentages
    if '%' in clean_str:
        try:
            return float(clean_str.replace('%', '')) / 100
        except ValueError:
            return None
    
    # Handle millions/billions
    multiplier = 1
    if 'B' in clean_str.upper() or 'billion' in clean_str.lower():
        multiplier = 1_000_000_000
        clean_str = re.sub(r'[Bb]illion|[Bb]', '', clean_str)
    elif 'M' in clean_str.upper() or 'million' in clean_str.lower():
        multiplier = 1_000_000
        clean_str = re.sub(r'[Mm]illion|[Mm]', '', clean_str)
    elif 'K' in clean_str.upper() or 'thousand' in clean_str.lower():
        multiplier = 1_000
        clean_str = re.sub(r'[Kk]|thousand', '', clean_str)
    
    try:
        return float(clean_str.strip()) * multiplier
    except ValueError:
        return None


def calculate_pe_ratio(price: float, earnings_per_share: float) -> Optional[float]:
    """Calculate P/E ratio.
    
    Args:
        price: Stock price
        earnings_per_share: EPS
        
    Returns:
        P/E ratio or None if calculation fails
    """
    if earnings_per_share and earnings_per_share != 0:
        return price / earnings_per_share
    return None


def calculate_debt_to_equity(total_debt: float, total_equity: float) -> Optional[float]:
    """Calculate debt-to-equity ratio.
    
    Args:
        total_debt: Total debt
        total_equity: Total equity
        
    Returns:
        Debt-to-equity ratio or None if calculation fails
    """
    if total_equity and total_equity != 0:
        return total_debt / total_equity
    return None


def calculate_roe(net_income: float, shareholders_equity: float) -> Optional[float]:
    """Calculate Return on Equity.
    
    Args:
        net_income: Net income
        shareholders_equity: Shareholders' equity
        
    Returns:
        ROE as decimal or None if calculation fails
    """
    if shareholders_equity and shareholders_equity != 0:
        return net_income / shareholders_equity
    return None


def calculate_profit_margin(net_income: float, revenue: float) -> Optional[float]:
    """Calculate profit margin.
    
    Args:
        net_income: Net income
        revenue: Total revenue
        
    Returns:
        Profit margin as decimal or None if calculation fails
    """
    if revenue and revenue != 0:
        return net_income / revenue
    return None


def calculate_revenue_growth(current_revenue: float, previous_revenue: float) -> Optional[float]:
    """Calculate revenue growth rate.
    
    Args:
        current_revenue: Current period revenue
        previous_revenue: Previous period revenue
        
    Returns:
        Growth rate as decimal or None if calculation fails
    """
    if previous_revenue and previous_revenue != 0:
        return (current_revenue - previous_revenue) / previous_revenue
    return None


def calculate_financial_metrics(financial_data: Dict[str, Any]) -> FinancialMetrics:
    """Calculate various financial metrics from raw data.
    
    Args:
        financial_data: Dictionary containing financial data
        
    Returns:
        FinancialMetrics object with calculated ratios
    """
    metrics = FinancialMetrics()
    
    # Parse values from strings if needed
    price = parse_financial_value(financial_data.get("stock_price"))
    eps = parse_financial_value(financial_data.get("earnings_per_share"))
    net_income = parse_financial_value(financial_data.get("net_income"))
    revenue = parse_financial_value(financial_data.get("revenue"))
    total_debt = parse_financial_value(financial_data.get("total_debt"))
    total_equity = parse_financial_value(financial_data.get("total_equity"))
    book_value_per_share = parse_financial_value(financial_data.get("book_value_per_share"))
    previous_revenue = parse_financial_value(financial_data.get("previous_revenue"))
    free_cash_flow = parse_financial_value(financial_data.get("free_cash_flow"))
    
    # Calculate ratios
    if price and eps:
        metrics.pe_ratio = calculate_pe_ratio(price, eps)
    
    if price and book_value_per_share:
        metrics.price_to_book = price / book_value_per_share if book_value_per_share != 0 else None
    
    if total_debt and total_equity:
        metrics.debt_to_equity = calculate_debt_to_equity(total_debt, total_equity)
    
    if net_income and total_equity:
        metrics.return_on_equity = calculate_roe(net_income, total_equity)
    
    if net_income and revenue:
        metrics.profit_margin = calculate_profit_margin(net_income, revenue)
    
    if revenue and previous_revenue:
        metrics.revenue_growth = calculate_revenue_growth(revenue, previous_revenue)
    
    if free_cash_flow:
        metrics.free_cash_flow = free_cash_flow
    
    return metrics


def perform_financial_calculations(
    financial_data_text: str,
    requested_metrics: List[str]
) -> str:
    """Perform financial calculations from text data.
    
    Args:
        financial_data_text: Text containing financial data
        requested_metrics: List of metrics to calculate
        
    Returns:
        Formatted string with calculated metrics
    """
    # Extract financial data from text using regex patterns
    patterns = {
        "stock_price": r"stock price.*?\$?([\d,\.]+)",
        "earnings_per_share": r"(?:eps|earnings per share).*?\$?([\d,\.]+)",
        "net_income": r"net income.*?\$?([\d,\.]+\s*(?:[BMK]|billion|million|thousand)?)",
        "revenue": r"revenue.*?\$?([\d,\.]+\s*(?:[BMK]|billion|million|thousand)?)",
        "total_debt": r"total debt.*?\$?([\d,\.]+\s*(?:[BMK]|billion|million|thousand)?)",
        "total_equity": r"(?:total equity|shareholders.?\s*equity|equity).*?\$?([\d,\.]+\s*(?:[BMK]|billion|million|thousand)?)",
        "book_value_per_share": r"book value per share.*?\$?([\d,\.]+)",
    }
    
    extracted_data = {}
    for metric, pattern in patterns.items():
        match = re.search(pattern, financial_data_text, re.IGNORECASE)
        if match:
            extracted_data[metric] = match.group(1)
    
    # Calculate metrics
    metrics = calculate_financial_metrics(extracted_data)
    
    # Format results
    results = ["Financial Metrics Calculation Results:\n"]
    
    if "pe_ratio" in requested_metrics and metrics.pe_ratio:
        results.append(f"P/E Ratio: {metrics.pe_ratio:.2f}")
    
    if "price_to_book" in requested_metrics and metrics.price_to_book:
        results.append(f"Price-to-Book Ratio: {metrics.price_to_book:.2f}")
    
    if "debt_to_equity" in requested_metrics and metrics.debt_to_equity:
        results.append(f"Debt-to-Equity Ratio: {metrics.debt_to_equity:.2f}")
    
    if "return_on_equity" in requested_metrics and metrics.return_on_equity:
        results.append(f"Return on Equity: {metrics.return_on_equity:.2%}")
    
    if "profit_margin" in requested_metrics and metrics.profit_margin:
        results.append(f"Profit Margin: {metrics.profit_margin:.2%}")
    
    if "revenue_growth" in requested_metrics and metrics.revenue_growth:
        results.append(f"Revenue Growth: {metrics.revenue_growth:.2%}")
    
    if not results[1:]:  # Only header exists
        results.append("Unable to calculate requested metrics from provided data.")
    
    return "\n".join(results)


async def calculate_live_metrics(symbol: str) -> str:
    """Calculate financial metrics using live market data.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        Formatted string with live financial metrics
    """
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        return "Error: ALPHA_VANTAGE_API_KEY environment variable not set"
    
    try:
        # Get real-time quote and fundamentals
        quote_task = asyncio.create_task(get_real_time_quote(symbol))
        fundamentals_task = asyncio.create_task(get_financial_fundamentals(symbol))
        
        quote_result, fundamentals_result = await asyncio.gather(
            quote_task, fundamentals_task, return_exceptions=True
        )
        
        if isinstance(quote_result, Exception):
            return f"Error getting quote for {symbol}: {str(quote_result)}"
        
        if isinstance(fundamentals_result, Exception):
            return f"Error getting fundamentals for {symbol}: {str(fundamentals_result)}"
        
        # Extract current price from quote
        price_line = [line for line in quote_result.split('\n') if 'Price:' in line]
        current_price = None
        if price_line:
            price_str = price_line[0].split('$')[1].split()[0]
            current_price = float(price_str)
        
        # Extract EPS from fundamentals
        eps_line = [line for line in fundamentals_result.split('\n') if 'Reported EPS:' in line]
        eps = None
        if eps_line:
            eps_str = eps_line[0].split('$')[1]
            try:
                eps = float(eps_str)
            except ValueError:
                eps = None
        
        # Calculate live P/E ratio
        results = [f"Live Financial Metrics for {symbol}:"]
        results.append(f"Current Price: ${current_price:.2f}" if current_price else "Current Price: N/A")
        
        if current_price and eps and eps != 0:
            pe_ratio = current_price / eps
            results.append(f"Live P/E Ratio: {pe_ratio:.2f}")
        else:
            results.append("Live P/E Ratio: N/A (insufficient data)")
        
        results.append("\n--- Real-time Quote ---")
        results.append(quote_result)
        
        results.append("\n--- Financial Fundamentals ---")
        results.append(fundamentals_result)
        
        return "\n".join(results)
        
    except Exception as e:
        return f"Error calculating live metrics for {symbol}: {str(e)}"


def calculate_valuation_metrics(
    current_price: float,
    eps: float,
    book_value_per_share: float,
    free_cash_flow_per_share: float,
    revenue_growth_rate: float,
    industry_avg_pe: float = 20.0
) -> str:
    """Calculate comprehensive valuation metrics.
    
    Args:
        current_price: Current stock price
        eps: Earnings per share
        book_value_per_share: Book value per share
        free_cash_flow_per_share: Free cash flow per share
        revenue_growth_rate: Revenue growth rate (as decimal)
        industry_avg_pe: Industry average P/E ratio
        
    Returns:
        Formatted string with valuation analysis
    """
    results = ["Valuation Analysis:"]
    
    # P/E Ratio Analysis
    if eps and eps != 0:
        pe_ratio = current_price / eps
        results.append(f"P/E Ratio: {pe_ratio:.2f}")
        
        premium_discount = ((pe_ratio - industry_avg_pe) / industry_avg_pe) * 100
        if premium_discount > 0:
            results.append(f"Trading at {premium_discount:.1f}% premium to industry average ({industry_avg_pe:.1f})")
        else:
            results.append(f"Trading at {abs(premium_discount):.1f}% discount to industry average ({industry_avg_pe:.1f})")
    
    # Price-to-Book Ratio
    if book_value_per_share and book_value_per_share != 0:
        pb_ratio = current_price / book_value_per_share
        results.append(f"Price-to-Book Ratio: {pb_ratio:.2f}")
        
        if pb_ratio < 1:
            results.append("• Trading below book value (potentially undervalued)")
        elif pb_ratio > 3:
            results.append("• Trading at high premium to book value")
    
    # Price-to-Free Cash Flow
    if free_cash_flow_per_share and free_cash_flow_per_share != 0:
        pfcf_ratio = current_price / free_cash_flow_per_share
        results.append(f"Price-to-Free Cash Flow: {pfcf_ratio:.2f}")
    
    # PEG Ratio (Price/Earnings to Growth)
    if eps and eps != 0 and revenue_growth_rate > 0:
        pe_ratio = current_price / eps
        growth_rate_percent = revenue_growth_rate * 100
        peg_ratio = pe_ratio / growth_rate_percent
        results.append(f"PEG Ratio: {peg_ratio:.2f}")
        
        if peg_ratio < 1:
            results.append("• PEG < 1 suggests potentially undervalued relative to growth")
        elif peg_ratio > 1.5:
            results.append("• PEG > 1.5 suggests potentially overvalued relative to growth")
    
    # Valuation Summary
    results.append("\nValuation Summary:")
    if eps and eps != 0:
        pe_ratio = current_price / eps
        if pe_ratio < 15:
            results.append("• Low P/E suggests value opportunity or declining business")
        elif pe_ratio > 25:
            results.append("• High P/E suggests growth expectations or overvaluation")
        else:
            results.append("• Moderate P/E suggests fair valuation")
    
    return "\n".join(results)


async def comprehensive_financial_analysis(symbol: str) -> str:
    """Perform comprehensive financial analysis combining live data and calculations.
    
    Args:
        symbol: Stock symbol to analyze
        
    Returns:
        Complete financial analysis report
    """
    try:
        # Get live metrics first
        live_metrics = await calculate_live_metrics(symbol)
        
        # Parse some values for additional calculations
        results = [f"=== Comprehensive Financial Analysis for {symbol} ===\n"]
        results.append(live_metrics)
        
        # Add investment considerations
        results.append("\n=== Investment Considerations ===")
        results.append("• Review quarterly earnings trends for consistency")
        results.append("• Compare metrics to industry peers and sector averages")
        results.append("• Consider macroeconomic factors affecting the sector")
        results.append("• Evaluate management guidance and forward-looking statements")
        results.append("• Assess competitive position and market share trends")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"Error in comprehensive analysis for {symbol}: {str(e)}"