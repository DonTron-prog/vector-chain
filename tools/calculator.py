"""Financial calculation tools."""

from typing import Dict, List, Any, Optional
import re
from models.schemas import FinancialMetrics


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
        "total_equity": r"(?:total equity|shareholders.equity).*?\$?([\d,\.]+\s*(?:[BMK]|billion|million|thousand)?)",
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