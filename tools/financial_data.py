"""Financial data API integration using Alpha Vantage."""

import aiohttp
import asyncio
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time
import logfire
from models.schemas import (
    StockQuote, HistoricalData, FinancialStatement, 
    TechnicalIndicators, MarketData, FinancialDataResponse
)


class AlphaVantageClient:
    """Async client for Alpha Vantage financial data API."""
    
    def __init__(self, api_key: str, base_url: str = "https://www.alphavantage.co/query"):
        self.api_key = api_key
        self.base_url = base_url
        self._session = None
        self._rate_limiter = RateLimiter(calls_per_minute=5)  # Free tier limit
        
    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
    
    async def _make_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Make rate-limited API request."""
        await self._rate_limiter.acquire()
        
        params.update({"apikey": self.api_key})
        
        try:
            if not self._session:
                self._session = aiohttp.ClientSession()
                
            async with self._session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for API errors
                    if "Error Message" in data:
                        raise Exception(f"Alpha Vantage API error: {data['Error Message']}")
                    if "Note" in data:
                        raise Exception(f"Alpha Vantage rate limit: {data['Note']}")
                    
                    logfire.info("Alpha Vantage API call successful", 
                               function=params.get("function"), 
                               symbol=params.get("symbol"))
                    return data
                else:
                    raise Exception(f"API request failed with status {response.status}")
                    
        except Exception as e:
            logfire.error("Alpha Vantage API call failed", 
                         function=params.get("function"), 
                         symbol=params.get("symbol"), 
                         error=str(e))
            raise
    
    async def get_quote(self, symbol: str) -> StockQuote:
        """Get real-time stock quote."""
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol
        }
        
        data = await self._make_request(params)
        quote_data = data.get("Global Quote", {})
        
        return StockQuote(
            symbol=quote_data.get("01. symbol", symbol),
            price=float(quote_data.get("05. price", 0)),
            change=float(quote_data.get("09. change", 0)),
            change_percent=quote_data.get("10. change percent", "0%").rstrip('%'),
            volume=int(quote_data.get("06. volume", 0)),
            previous_close=float(quote_data.get("08. previous close", 0)),
            open_price=float(quote_data.get("02. open", 0)),
            high=float(quote_data.get("03. high", 0)),
            low=float(quote_data.get("04. low", 0)),
            latest_trading_day=quote_data.get("07. latest trading day", ""),
            timestamp=datetime.now()
        )
    
    async def get_historical_data(
        self, 
        symbol: str, 
        interval: str = "daily", 
        outputsize: str = "compact"
    ) -> HistoricalData:
        """Get historical price data."""
        function_map = {
            "daily": "TIME_SERIES_DAILY",
            "weekly": "TIME_SERIES_WEEKLY", 
            "monthly": "TIME_SERIES_MONTHLY"
        }
        
        params = {
            "function": function_map.get(interval, "TIME_SERIES_DAILY"),
            "symbol": symbol,
            "outputsize": outputsize
        }
        
        data = await self._make_request(params)
        
        # Extract time series data
        time_series_key = f"Time Series ({interval.title()})" if interval == "daily" else f"{interval.title()} Time Series"
        time_series = data.get(time_series_key, {})
        
        prices = []
        for date_str, values in time_series.items():
            prices.append({
                "date": date_str,
                "open": float(values.get("1. open", 0)),
                "high": float(values.get("2. high", 0)),
                "low": float(values.get("3. low", 0)),
                "close": float(values.get("4. close", 0)),
                "volume": int(values.get("5. volume", 0))
            })
        
        return HistoricalData(
            symbol=symbol,
            interval=interval,
            prices=prices,
            metadata=data.get("Meta Data", {}),
            timestamp=datetime.now()
        )
    
    async def get_financial_statement(
        self, 
        symbol: str, 
        statement_type: str = "income"
    ) -> FinancialStatement:
        """Get financial statement data."""
        function_map = {
            "income": "INCOME_STATEMENT",
            "balance": "BALANCE_SHEET",
            "cash": "CASH_FLOW"
        }
        
        params = {
            "function": function_map.get(statement_type, "INCOME_STATEMENT"),
            "symbol": symbol
        }
        
        data = await self._make_request(params)
        
        # Extract annual and quarterly reports
        annual_reports = data.get("annualReports", [])
        quarterly_reports = data.get("quarterlyReports", [])
        
        return FinancialStatement(
            symbol=symbol,
            statement_type=statement_type,
            annual_reports=annual_reports,
            quarterly_reports=quarterly_reports,
            timestamp=datetime.now()
        )
    
    async def get_technical_indicators(
        self, 
        symbol: str, 
        indicator: str = "SMA",
        interval: str = "daily",
        time_period: int = 20
    ) -> TechnicalIndicators:
        """Get technical indicator data."""
        params = {
            "function": indicator,
            "symbol": symbol,
            "interval": interval,
            "time_period": str(time_period),
            "series_type": "close"
        }
        
        data = await self._make_request(params)
        
        # Extract technical analysis data
        tech_key = f"Technical Analysis: {indicator}"
        tech_data = data.get(tech_key, {})
        
        return TechnicalIndicators(
            symbol=symbol,
            indicator=indicator,
            interval=interval,
            time_period=time_period,
            data=tech_data,
            metadata=data.get("Meta Data", {}),
            timestamp=datetime.now()
        )


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, calls_per_minute: int):
        self.calls_per_minute = calls_per_minute
        self.calls = []
    
    async def acquire(self):
        """Acquire permission to make an API call."""
        now = time.time()
        
        # Remove calls older than 1 minute
        self.calls = [call_time for call_time in self.calls if now - call_time < 60]
        
        # If we're at the limit, wait
        if len(self.calls) >= self.calls_per_minute:
            sleep_time = 60 - (now - self.calls[0]) + 1
            logfire.info("Rate limiting API calls", sleep_time=sleep_time)
            await asyncio.sleep(sleep_time)
        
        self.calls.append(now)


class FinancialDataService:
    """High-level service for financial data operations."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None
    
    async def get_client(self) -> AlphaVantageClient:
        """Get or create client instance."""
        if not self._client:
            self._client = AlphaVantageClient(self.api_key)
        return self._client
    
    async def get_stock_overview(self, symbol: str) -> FinancialDataResponse:
        """Get comprehensive stock overview with quote and basic financials."""
        async with AlphaVantageClient(self.api_key) as client:
            try:
                # Get current quote
                quote = await client.get_quote(symbol)
                
                # Get recent historical data
                historical = await client.get_historical_data(symbol, "daily", "compact")
                
                # Get latest income statement
                income_statement = await client.get_financial_statement(symbol, "income")
                
                return FinancialDataResponse(
                    symbol=symbol,
                    quote=quote,
                    historical_data=historical,
                    financial_statements=[income_statement],
                    technical_indicators=[],
                    market_data=None,
                    success=True,
                    error_message=None,
                    timestamp=datetime.now()
                )
                
            except Exception as e:
                logfire.error("Financial data overview failed", symbol=symbol, error=str(e))
                return FinancialDataResponse(
                    symbol=symbol,
                    quote=None,
                    historical_data=None,
                    financial_statements=[],
                    technical_indicators=[],
                    market_data=None,
                    success=False,
                    error_message=str(e),
                    timestamp=datetime.now()
                )
    
    async def get_technical_analysis(
        self, 
        symbol: str, 
        indicators: List[str] = None
    ) -> List[TechnicalIndicators]:
        """Get multiple technical indicators for analysis."""
        if indicators is None:
            indicators = ["SMA", "EMA", "RSI", "MACD"]
        
        results = []
        async with AlphaVantageClient(self.api_key) as client:
            for indicator in indicators:
                try:
                    tech_data = await client.get_technical_indicators(symbol, indicator)
                    results.append(tech_data)
                except Exception as e:
                    logfire.error("Technical indicator failed", 
                                 symbol=symbol, 
                                 indicator=indicator, 
                                 error=str(e))
        
        return results


# Tool functions for pydantic-ai agents
async def get_real_time_quote(symbol: str) -> str:
    """Get real-time stock quote for investment analysis.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        Formatted string with current stock information
    """
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        return "Error: ALPHA_VANTAGE_API_KEY environment variable not set"
    
    service = FinancialDataService(api_key)
    
    try:
        async with AlphaVantageClient(api_key) as client:
            quote = await client.get_quote(symbol)
            
            return f"""
Real-time Quote for {quote.symbol}:
Price: ${quote.price:.2f}
Change: ${quote.change:.2f} ({quote.change_percent}%)
Volume: {quote.volume:,}
Previous Close: ${quote.previous_close:.2f}
Day Range: ${quote.low:.2f} - ${quote.high:.2f}
Open: ${quote.open_price:.2f}
Last Updated: {quote.latest_trading_day}
            """.strip()
            
    except Exception as e:
        logfire.error("Real-time quote failed", symbol=symbol, error=str(e))
        return f"Error getting quote for {symbol}: {str(e)}"


async def get_historical_analysis(symbol: str, period: str = "daily") -> str:
    """Get historical price analysis for trend identification.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
        period: Time period ('daily', 'weekly', 'monthly')
        
    Returns:
        Formatted string with historical analysis
    """
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        return "Error: ALPHA_VANTAGE_API_KEY environment variable not set"
    
    try:
        async with AlphaVantageClient(api_key) as client:
            historical = await client.get_historical_data(symbol, period, "compact")
            
            if not historical.prices:
                return f"No historical data available for {symbol}"
            
            # Basic analysis
            recent_prices = historical.prices[:10]  # Last 10 periods
            latest_price = recent_prices[0]["close"]
            oldest_price = recent_prices[-1]["close"]
            price_change = ((latest_price - oldest_price) / oldest_price) * 100
            
            avg_volume = sum(p["volume"] for p in recent_prices) / len(recent_prices)
            
            return f"""
Historical Analysis for {symbol} ({period}):
Recent {len(recent_prices)}-{period} Performance: {price_change:+.2f}%
Current Price: ${latest_price:.2f}
Average Volume: {avg_volume:,.0f}
Price Range: ${min(p["low"] for p in recent_prices):.2f} - ${max(p["high"] for p in recent_prices):.2f}
Data Points: {len(historical.prices)} {period} periods
            """.strip()
            
    except Exception as e:
        logfire.error("Historical analysis failed", symbol=symbol, error=str(e))
        return f"Error getting historical data for {symbol}: {str(e)}"


async def get_financial_fundamentals(symbol: str) -> str:
    """Get fundamental financial data for valuation analysis.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        Formatted string with fundamental financial metrics
    """
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        return "Error: ALPHA_VANTAGE_API_KEY environment variable not set"
    
    try:
        async with AlphaVantageClient(api_key) as client:
            income_stmt = await client.get_financial_statement(symbol, "income")
            
            if not income_stmt.annual_reports:
                return f"No financial statement data available for {symbol}"
            
            # Get latest annual report
            latest_report = income_stmt.annual_reports[0]
            
            # Extract key metrics
            revenue = latest_report.get("totalRevenue", "N/A")
            net_income = latest_report.get("netIncome", "N/A")
            eps = latest_report.get("reportedEPS", "N/A")
            fiscal_year = latest_report.get("fiscalDateEnding", "N/A")
            
            return f"""
Financial Fundamentals for {symbol}:
Fiscal Year Ending: {fiscal_year}
Total Revenue: ${float(revenue):,.0f} if revenue != 'N/A' else revenue
Net Income: ${float(net_income):,.0f} if net_income != 'N/A' else net_income
Reported EPS: ${eps}
Operating Income: ${latest_report.get("operatingIncome", "N/A")}
Gross Profit: ${latest_report.get("grossProfit", "N/A")}
            """.strip()
            
    except Exception as e:
        logfire.error("Financial fundamentals failed", symbol=symbol, error=str(e))
        return f"Error getting financial data for {symbol}: {str(e)}"