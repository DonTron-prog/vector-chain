"""Alpha Vantage financial data API integration."""

import os
from typing import Dict, Any, Optional, List
import aiohttp
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
import json

from config import (
    get_alpha_vantage_api_key,
    ALPHA_VANTAGE_BASE_URL,
    ALPHA_VANTAGE_RATE_LIMIT,
    ALPHA_VANTAGE_CACHE_TTL
)


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, calls_per_minute: int):
        self.calls_per_minute = calls_per_minute
        self.calls = defaultdict(list)
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old calls
        self.calls['api'] = [call_time for call_time in self.calls['api'] if call_time > minute_ago]
        
        # Check if we need to wait
        if len(self.calls['api']) >= self.calls_per_minute:
            oldest_call = self.calls['api'][0]
            wait_time = (oldest_call + timedelta(minutes=1) - now).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        # Record new call
        self.calls['api'].append(now)


class AlphaVantageCache:
    """Simple in-memory cache for API responses."""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached value if not expired."""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl):
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Dict[str, Any]):
        """Cache a value with timestamp."""
        self.cache[key] = (value, datetime.now())


# Global instances
rate_limiter = RateLimiter(ALPHA_VANTAGE_RATE_LIMIT)
cache = AlphaVantageCache(ALPHA_VANTAGE_CACHE_TTL)


async def make_alpha_vantage_request(
    function: str,
    symbol: str,
    api_key: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Make a request to Alpha Vantage API with rate limiting and caching.
    
    Args:
        function: API function to call (e.g., 'GLOBAL_QUOTE', 'TIME_SERIES_DAILY')
        symbol: Stock symbol
        api_key: API key (optional, will use env var if not provided)
        **kwargs: Additional parameters for the API call
        
    Returns:
        API response as dictionary
        
    Raises:
        Exception: If API request fails
    """
    # Get API key
    api_key = api_key or get_alpha_vantage_api_key()
    
    # Build cache key
    cache_key = f"{function}:{symbol}:{json.dumps(kwargs, sort_keys=True)}"
    
    # Check cache
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # Rate limit
    await rate_limiter.wait_if_needed()
    
    # Build request parameters
    params = {
        'function': function,
        'symbol': symbol,
        'apikey': api_key,
        **kwargs
    }
    
    # Make request
    async with aiohttp.ClientSession() as session:
        async with session.get(ALPHA_VANTAGE_BASE_URL, params=params) as response:
            if response.status == 200:
                data = await response.json()
                
                # Check for API errors
                if 'Error Message' in data:
                    raise Exception(f"Alpha Vantage API error: {data['Error Message']}")
                if 'Note' in data and 'API call frequency' in data['Note']:
                    raise Exception("Alpha Vantage API rate limit exceeded")
                
                # Cache successful response
                cache.set(cache_key, data)
                return data
            else:
                raise Exception(f"Alpha Vantage API request failed with status {response.status}")


async def get_quote(symbol: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Get real-time stock quote.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        api_key: API key (optional)
        
    Returns:
        Dictionary with quote data including price, volume, change
    """
    try:
        data = await make_alpha_vantage_request('GLOBAL_QUOTE', symbol, api_key)
        
        if 'Global Quote' not in data:
            return {'error': 'No quote data available'}
        
        quote = data['Global Quote']
        return {
            'symbol': quote.get('01. symbol', symbol),
            'price': float(quote.get('05. price', 0)),
            'change': float(quote.get('09. change', 0)),
            'change_percent': quote.get('10. change percent', '0%'),
            'volume': int(quote.get('06. volume', 0)),
            'latest_trading_day': quote.get('07. latest trading day'),
            'previous_close': float(quote.get('08. previous close', 0)),
            'open': float(quote.get('02. open', 0)),
            'high': float(quote.get('03. high', 0)),
            'low': float(quote.get('04. low', 0))
        }
    except Exception as e:
        return {'error': str(e)}


async def get_company_overview(symbol: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Get company fundamental data and overview.
    
    Args:
        symbol: Stock symbol
        api_key: API key (optional)
        
    Returns:
        Dictionary with company overview including metrics
    """
    try:
        data = await make_alpha_vantage_request('OVERVIEW', symbol, api_key)
        
        if not data or 'Symbol' not in data:
            return {'error': 'No company overview data available'}
        
        # Extract key metrics
        return {
            'symbol': data.get('Symbol', symbol),
            'name': data.get('Name', ''),
            'description': data.get('Description', ''),
            'sector': data.get('Sector', ''),
            'industry': data.get('Industry', ''),
            'market_cap': float(data.get('MarketCapitalization', 0)),
            'pe_ratio': float(data.get('PERatio', 0)) if data.get('PERatio') != 'None' else None,
            'peg_ratio': float(data.get('PEGRatio', 0)) if data.get('PEGRatio') != 'None' else None,
            'book_value': float(data.get('BookValue', 0)) if data.get('BookValue') != 'None' else None,
            'dividend_yield': float(data.get('DividendYield', 0)) if data.get('DividendYield') != 'None' else None,
            'eps': float(data.get('EPS', 0)) if data.get('EPS') != 'None' else None,
            'revenue_per_share': float(data.get('RevenuePerShareTTM', 0)) if data.get('RevenuePerShareTTM') != 'None' else None,
            'profit_margin': float(data.get('ProfitMargin', 0)) if data.get('ProfitMargin') != 'None' else None,
            'operating_margin': float(data.get('OperatingMarginTTM', 0)) if data.get('OperatingMarginTTM') != 'None' else None,
            'return_on_assets': float(data.get('ReturnOnAssetsTTM', 0)) if data.get('ReturnOnAssetsTTM') != 'None' else None,
            'return_on_equity': float(data.get('ReturnOnEquityTTM', 0)) if data.get('ReturnOnEquityTTM') != 'None' else None,
            'revenue': float(data.get('RevenueTTM', 0)) if data.get('RevenueTTM') != 'None' else None,
            'gross_profit': float(data.get('GrossProfitTTM', 0)) if data.get('GrossProfitTTM') != 'None' else None,
            'diluted_eps': float(data.get('DilutedEPSTTM', 0)) if data.get('DilutedEPSTTM') != 'None' else None,
            'quarterly_earnings_growth': float(data.get('QuarterlyEarningsGrowthYOY', 0)) if data.get('QuarterlyEarningsGrowthYOY') != 'None' else None,
            'quarterly_revenue_growth': float(data.get('QuarterlyRevenueGrowthYOY', 0)) if data.get('QuarterlyRevenueGrowthYOY') != 'None' else None,
            'analyst_target_price': float(data.get('AnalystTargetPrice', 0)) if data.get('AnalystTargetPrice') != 'None' else None,
            'trailing_pe': float(data.get('TrailingPE', 0)) if data.get('TrailingPE') != 'None' else None,
            'forward_pe': float(data.get('ForwardPE', 0)) if data.get('ForwardPE') != 'None' else None,
            'price_to_sales': float(data.get('PriceToSalesRatioTTM', 0)) if data.get('PriceToSalesRatioTTM') != 'None' else None,
            'price_to_book': float(data.get('PriceToBookRatio', 0)) if data.get('PriceToBookRatio') != 'None' else None,
            'beta': float(data.get('Beta', 0)) if data.get('Beta') != 'None' else None,
            '52_week_high': float(data.get('52WeekHigh', 0)) if data.get('52WeekHigh') != 'None' else None,
            '52_week_low': float(data.get('52WeekLow', 0)) if data.get('52WeekLow') != 'None' else None,
            'shares_outstanding': float(data.get('SharesOutstanding', 0)) if data.get('SharesOutstanding') != 'None' else None,
            'dividend_date': data.get('DividendDate'),
            'ex_dividend_date': data.get('ExDividendDate')
        }
    except Exception as e:
        return {'error': str(e)}


async def get_earnings(symbol: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Get earnings history and estimates.
    
    Args:
        symbol: Stock symbol
        api_key: API key (optional)
        
    Returns:
        Dictionary with earnings data
    """
    try:
        data = await make_alpha_vantage_request('EARNINGS', symbol, api_key)
        
        if 'quarterlyEarnings' not in data:
            return {'error': 'No earnings data available'}
        
        quarterly_earnings = data.get('quarterlyEarnings', [])
        annual_earnings = data.get('annualEarnings', [])
        
        # Process quarterly earnings (most recent first)
        recent_quarters = []
        for quarter in quarterly_earnings[:8]:  # Last 8 quarters
            recent_quarters.append({
                'date': quarter.get('fiscalDateEnding'),
                'reported_eps': float(quarter.get('reportedEPS', 0)) if quarter.get('reportedEPS') != 'None' else None,
                'estimated_eps': float(quarter.get('estimatedEPS', 0)) if quarter.get('estimatedEPS') != 'None' else None,
                'surprise': float(quarter.get('surprise', 0)) if quarter.get('surprise') != 'None' else None,
                'surprise_percentage': float(quarter.get('surprisePercentage', 0)) if quarter.get('surprisePercentage') != 'None' else None
            })
        
        # Process annual earnings
        recent_annual = []
        for year in annual_earnings[:3]:  # Last 3 years
            recent_annual.append({
                'year': year.get('fiscalDateEnding'),
                'reported_eps': float(year.get('reportedEPS', 0)) if year.get('reportedEPS') != 'None' else None
            })
        
        return {
            'symbol': symbol,
            'quarterly_earnings': recent_quarters,
            'annual_earnings': recent_annual
        }
    except Exception as e:
        return {'error': str(e)}


async def get_income_statement(symbol: str, api_key: Optional[str] = None, annual: bool = True) -> Dict[str, Any]:
    """Get income statement data.
    
    Args:
        symbol: Stock symbol
        api_key: API key (optional)
        annual: True for annual data, False for quarterly
        
    Returns:
        Dictionary with income statement data
    """
    try:
        function = 'INCOME_STATEMENT'
        data = await make_alpha_vantage_request(function, symbol, api_key)
        
        if annual:
            reports = data.get('annualReports', [])
        else:
            reports = data.get('quarterlyReports', [])
        
        if not reports:
            return {'error': 'No income statement data available'}
        
        # Process most recent reports
        processed_reports = []
        for report in reports[:4]:  # Last 4 periods
            processed_reports.append({
                'date': report.get('fiscalDateEnding'),
                'revenue': float(report.get('totalRevenue', 0)) if report.get('totalRevenue') != 'None' else None,
                'gross_profit': float(report.get('grossProfit', 0)) if report.get('grossProfit') != 'None' else None,
                'operating_income': float(report.get('operatingIncome', 0)) if report.get('operatingIncome') != 'None' else None,
                'net_income': float(report.get('netIncome', 0)) if report.get('netIncome') != 'None' else None,
                'ebitda': float(report.get('ebitda', 0)) if report.get('ebitda') != 'None' else None,
                'ebit': float(report.get('ebit', 0)) if report.get('ebit') != 'None' else None
            })
        
        return {
            'symbol': symbol,
            'period': 'annual' if annual else 'quarterly',
            'reports': processed_reports
        }
    except Exception as e:
        return {'error': str(e)}


async def get_balance_sheet(symbol: str, api_key: Optional[str] = None, annual: bool = True) -> Dict[str, Any]:
    """Get balance sheet data.
    
    Args:
        symbol: Stock symbol
        api_key: API key (optional)
        annual: True for annual data, False for quarterly
        
    Returns:
        Dictionary with balance sheet data
    """
    try:
        function = 'BALANCE_SHEET'
        data = await make_alpha_vantage_request(function, symbol, api_key)
        
        if annual:
            reports = data.get('annualReports', [])
        else:
            reports = data.get('quarterlyReports', [])
        
        if not reports:
            return {'error': 'No balance sheet data available'}
        
        # Process most recent reports
        processed_reports = []
        for report in reports[:4]:  # Last 4 periods
            processed_reports.append({
                'date': report.get('fiscalDateEnding'),
                'total_assets': float(report.get('totalAssets', 0)) if report.get('totalAssets') != 'None' else None,
                'total_liabilities': float(report.get('totalLiabilities', 0)) if report.get('totalLiabilities') != 'None' else None,
                'total_equity': float(report.get('totalShareholderEquity', 0)) if report.get('totalShareholderEquity') != 'None' else None,
                'cash': float(report.get('cashAndCashEquivalentsAtCarryingValue', 0)) if report.get('cashAndCashEquivalentsAtCarryingValue') != 'None' else None,
                'current_assets': float(report.get('totalCurrentAssets', 0)) if report.get('totalCurrentAssets') != 'None' else None,
                'current_liabilities': float(report.get('totalCurrentLiabilities', 0)) if report.get('totalCurrentLiabilities') != 'None' else None,
                'long_term_debt': float(report.get('longTermDebt', 0)) if report.get('longTermDebt') != 'None' else None,
                'short_term_debt': float(report.get('shortTermDebt', 0)) if report.get('shortTermDebt') != 'None' else None
            })
        
        return {
            'symbol': symbol,
            'period': 'annual' if annual else 'quarterly',
            'reports': processed_reports
        }
    except Exception as e:
        return {'error': str(e)}


async def get_cash_flow(symbol: str, api_key: Optional[str] = None, annual: bool = True) -> Dict[str, Any]:
    """Get cash flow statement data.
    
    Args:
        symbol: Stock symbol
        api_key: API key (optional)
        annual: True for annual data, False for quarterly
        
    Returns:
        Dictionary with cash flow data
    """
    try:
        function = 'CASH_FLOW'
        data = await make_alpha_vantage_request(function, symbol, api_key)
        
        if annual:
            reports = data.get('annualReports', [])
        else:
            reports = data.get('quarterlyReports', [])
        
        if not reports:
            return {'error': 'No cash flow data available'}
        
        # Process most recent reports
        processed_reports = []
        for report in reports[:4]:  # Last 4 periods
            processed_reports.append({
                'date': report.get('fiscalDateEnding'),
                'operating_cash_flow': float(report.get('operatingCashflow', 0)) if report.get('operatingCashflow') != 'None' else None,
                'free_cash_flow': float(report.get('freeCashFlow', 0)) if report.get('freeCashFlow') != 'None' else None,
                'capital_expenditures': float(report.get('capitalExpenditures', 0)) if report.get('capitalExpenditures') != 'None' else None,
                'dividend_payout': float(report.get('dividendPayout', 0)) if report.get('dividendPayout') != 'None' else None
            })
        
        return {
            'symbol': symbol,
            'period': 'annual' if annual else 'quarterly',
            'reports': processed_reports
        }
    except Exception as e:
        return {'error': str(e)}


async def get_time_series_daily(symbol: str, api_key: Optional[str] = None, outputsize: str = 'compact') -> Dict[str, Any]:
    """Get daily time series data (historical prices).
    
    Args:
        symbol: Stock symbol
        api_key: API key (optional)
        outputsize: 'compact' for last 100 days, 'full' for 20+ years
        
    Returns:
        Dictionary with time series data
    """
    try:
        data = await make_alpha_vantage_request('TIME_SERIES_DAILY', symbol, api_key, outputsize=outputsize)
        
        if 'Time Series (Daily)' not in data:
            return {'error': 'No time series data available'}
        
        time_series = data['Time Series (Daily)']
        
        # Convert to list format
        daily_prices = []
        for date, values in sorted(time_series.items(), reverse=True)[:100]:  # Most recent 100 days
            daily_prices.append({
                'date': date,
                'open': float(values['1. open']),
                'high': float(values['2. high']),
                'low': float(values['3. low']),
                'close': float(values['4. close']),
                'volume': int(values['5. volume'])
            })
        
        return {
            'symbol': symbol,
            'daily_prices': daily_prices
        }
    except Exception as e:
        return {'error': str(e)}


def format_quote_results(quote_data: Dict[str, Any]) -> str:
    """Format quote data for LLM consumption."""
    if 'error' in quote_data:
        return f"Error fetching quote: {quote_data['error']}"
    
    return f"""Real-Time Quote for {quote_data['symbol']}:
- Current Price: ${quote_data['price']:.2f}
- Change: ${quote_data['change']:.2f} ({quote_data['change_percent']})
- Volume: {quote_data['volume']:,}
- Day Range: ${quote_data['low']:.2f} - ${quote_data['high']:.2f}
- Previous Close: ${quote_data['previous_close']:.2f}
- Last Updated: {quote_data['latest_trading_day']}"""


def format_company_overview(overview_data: Dict[str, Any]) -> str:
    """Format company overview for LLM consumption."""
    if 'error' in overview_data:
        return f"Error fetching company overview: {overview_data['error']}"
    
    output = [f"Company Overview for {overview_data['symbol']} - {overview_data['name']}:"]
    output.append(f"Sector: {overview_data['sector']} | Industry: {overview_data['industry']}")
    output.append("")
    
    # Key metrics
    output.append("Valuation Metrics:")
    if overview_data['market_cap']:
        output.append(f"- Market Cap: ${overview_data['market_cap']:,.0f}")
    if overview_data['pe_ratio']:
        output.append(f"- P/E Ratio: {overview_data['pe_ratio']:.2f}")
    if overview_data['forward_pe']:
        output.append(f"- Forward P/E: {overview_data['forward_pe']:.2f}")
    if overview_data['peg_ratio']:
        output.append(f"- PEG Ratio: {overview_data['peg_ratio']:.2f}")
    if overview_data['price_to_book']:
        output.append(f"- Price to Book: {overview_data['price_to_book']:.2f}")
    if overview_data['price_to_sales']:
        output.append(f"- Price to Sales: {overview_data['price_to_sales']:.2f}")
    
    output.append("\nProfitability:")
    if overview_data['profit_margin']:
        output.append(f"- Profit Margin: {overview_data['profit_margin']:.2%}")
    if overview_data['operating_margin']:
        output.append(f"- Operating Margin: {overview_data['operating_margin']:.2%}")
    if overview_data['return_on_equity']:
        output.append(f"- ROE: {overview_data['return_on_equity']:.2%}")
    if overview_data['return_on_assets']:
        output.append(f"- ROA: {overview_data['return_on_assets']:.2%}")
    
    output.append("\nGrowth:")
    if overview_data['quarterly_earnings_growth']:
        output.append(f"- Quarterly Earnings Growth YoY: {overview_data['quarterly_earnings_growth']:.2%}")
    if overview_data['quarterly_revenue_growth']:
        output.append(f"- Quarterly Revenue Growth YoY: {overview_data['quarterly_revenue_growth']:.2%}")
    
    if overview_data['dividend_yield']:
        output.append(f"\nDividend Yield: {overview_data['dividend_yield']:.2%}")
    
    if overview_data['analyst_target_price']:
        output.append(f"\nAnalyst Target Price: ${overview_data['analyst_target_price']:.2f}")
    
    output.append(f"\n52-Week Range: ${overview_data['52_week_low']:.2f} - ${overview_data['52_week_high']:.2f}")
    
    return "\n".join(output)


def format_earnings_results(earnings_data: Dict[str, Any]) -> str:
    """Format earnings data for LLM consumption."""
    if 'error' in earnings_data:
        return f"Error fetching earnings: {earnings_data['error']}"
    
    output = [f"Earnings History for {earnings_data['symbol']}:"]
    
    output.append("\nRecent Quarterly Earnings:")
    for quarter in earnings_data['quarterly_earnings'][:4]:
        surprise_text = ""
        if quarter['surprise_percentage']:
            surprise_text = f" | Surprise: {quarter['surprise_percentage']:.2f}%"
        output.append(f"- {quarter['date']}: EPS ${quarter['reported_eps']:.2f} (Est: ${quarter['estimated_eps']:.2f}){surprise_text}")
    
    if earnings_data['annual_earnings']:
        output.append("\nAnnual Earnings:")
        for year in earnings_data['annual_earnings']:
            output.append(f"- {year['year']}: EPS ${year['reported_eps']:.2f}")
    
    return "\n".join(output)


def format_financial_statements(statement_data: Dict[str, Any], statement_type: str) -> str:
    """Format financial statement data for LLM consumption."""
    if 'error' in statement_data:
        return f"Error fetching {statement_type}: {statement_data['error']}"
    
    output = [f"{statement_type} for {statement_data['symbol']} ({statement_data['period']}):"]
    
    for report in statement_data['reports'][:2]:  # Show last 2 periods
        output.append(f"\nPeriod ending {report['date']}:")
        
        if statement_type == "Income Statement":
            if report['revenue']:
                output.append(f"- Revenue: ${report['revenue']:,.0f}")
            if report['gross_profit']:
                output.append(f"- Gross Profit: ${report['gross_profit']:,.0f}")
            if report['operating_income']:
                output.append(f"- Operating Income: ${report['operating_income']:,.0f}")
            if report['net_income']:
                output.append(f"- Net Income: ${report['net_income']:,.0f}")
        
        elif statement_type == "Balance Sheet":
            if report['total_assets']:
                output.append(f"- Total Assets: ${report['total_assets']:,.0f}")
            if report['total_liabilities']:
                output.append(f"- Total Liabilities: ${report['total_liabilities']:,.0f}")
            if report['total_equity']:
                output.append(f"- Total Equity: ${report['total_equity']:,.0f}")
            if report['cash']:
                output.append(f"- Cash: ${report['cash']:,.0f}")
        
        elif statement_type == "Cash Flow":
            if report['operating_cash_flow']:
                output.append(f"- Operating Cash Flow: ${report['operating_cash_flow']:,.0f}")
            if report['free_cash_flow']:
                output.append(f"- Free Cash Flow: ${report['free_cash_flow']:,.0f}")
            if report['capital_expenditures']:
                output.append(f"- CapEx: ${abs(report['capital_expenditures']):,.0f}")
    
    return "\n".join(output)