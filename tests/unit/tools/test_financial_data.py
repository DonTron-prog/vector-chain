"""Unit tests for financial data tools."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from tools.financial_data import (
    AlphaVantageClient, RateLimiter, FinancialDataService,
    get_real_time_quote, get_historical_analysis, get_financial_fundamentals
)
from models.schemas import StockQuote, HistoricalData, FinancialStatement


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_basic(self):
        """Test basic rate limiting."""
        limiter = RateLimiter(calls_per_minute=2)
        
        # First call should go through immediately
        await limiter.acquire()
        assert len(limiter.calls) == 1
        
        # Second call should also go through
        await limiter.acquire()
        assert len(limiter.calls) == 2
    
    @pytest.mark.asyncio 
    async def test_rate_limiter_with_delay(self):
        """Test rate limiting with artificial delay."""
        limiter = RateLimiter(calls_per_minute=1)
        
        # Add old call to simulate rate limit
        import time
        limiter.calls.append(time.time() - 30)  # 30 seconds ago
        
        # This should go through quickly
        await limiter.acquire()
        assert len(limiter.calls) == 2


class TestAlphaVantageClient:
    """Test Alpha Vantage API client."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return AlphaVantageClient("test_api_key")
    
    @pytest.fixture
    def mock_quote_response(self):
        """Mock quote API response."""
        return {
            "Global Quote": {
                "01. symbol": "AAPL",
                "02. open": "150.00",
                "03. high": "155.00", 
                "04. low": "149.00",
                "05. price": "152.50",
                "06. volume": "50000000",
                "07. latest trading day": "2024-01-15",
                "08. previous close": "151.00",
                "09. change": "1.50",
                "10. change percent": "0.99%"
            }
        }
    
    @pytest.fixture
    def mock_historical_response(self):
        """Mock historical data API response."""
        return {
            "Meta Data": {
                "1. Information": "Daily Prices",
                "2. Symbol": "AAPL"
            },
            "Time Series (Daily)": {
                "2024-01-15": {
                    "1. open": "150.00",
                    "2. high": "155.00",
                    "3. low": "149.00", 
                    "4. close": "152.50",
                    "5. volume": "50000000"
                },
                "2024-01-14": {
                    "1. open": "148.00",
                    "2. high": "151.00",
                    "3. low": "147.00",
                    "4. close": "151.00", 
                    "5. volume": "45000000"
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_get_quote_success(self, client, mock_quote_response):
        """Test successful quote retrieval."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            # Create proper async mock for session
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_quote_response)
            
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            async with client:
                quote = await client.get_quote("AAPL")
                
            assert isinstance(quote, StockQuote)
            assert quote.symbol == "AAPL"
            assert quote.price == 152.50
            assert quote.change == 1.50
            assert quote.volume == 50000000
    
    @pytest.mark.asyncio
    async def test_get_quote_api_error(self, client):
        """Test quote retrieval with API error."""
        error_response = {"Error Message": "Invalid API call"}
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=error_response)
            
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            async with client:
                with pytest.raises(Exception, match="Alpha Vantage API error"):
                    await client.get_quote("INVALID")
    
    @pytest.mark.asyncio
    async def test_get_historical_data_success(self, client, mock_historical_response):
        """Test successful historical data retrieval."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_historical_response)
            
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            async with client:
                historical = await client.get_historical_data("AAPL")
                
            assert isinstance(historical, HistoricalData)
            assert historical.symbol == "AAPL"
            assert historical.interval == "daily"
            assert len(historical.prices) == 2
            assert historical.prices[0]["close"] == 152.50
    
    @pytest.mark.asyncio
    async def test_get_financial_statement_success(self, client):
        """Test successful financial statement retrieval."""
        mock_response_data = {
            "symbol": "AAPL",
            "annualReports": [
                {
                    "fiscalDateEnding": "2023-09-30",
                    "totalRevenue": "383285000000",
                    "netIncome": "96995000000"
                }
            ],
            "quarterlyReports": []
        }
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            async with client:
                statement = await client.get_financial_statement("AAPL", "income")
                
            assert isinstance(statement, FinancialStatement)
            assert statement.symbol == "AAPL"
            assert statement.statement_type == "income"
            assert len(statement.annual_reports) == 1


class TestFinancialDataService:
    """Test high-level financial data service."""
    
    @pytest.fixture
    def service(self):
        """Create test service."""
        return FinancialDataService("test_api_key")
    
    @pytest.mark.asyncio
    async def test_get_stock_overview_success(self, service):
        """Test successful stock overview retrieval."""
        with patch.object(AlphaVantageClient, 'get_quote') as mock_quote, \
             patch.object(AlphaVantageClient, 'get_historical_data') as mock_historical, \
             patch.object(AlphaVantageClient, 'get_financial_statement') as mock_statement:
            
            # Mock successful responses
            mock_quote.return_value = StockQuote(
                symbol="AAPL", price=152.50, change=1.50, change_percent="0.99%",
                volume=50000000, previous_close=151.00, open_price=150.00,
                high=155.00, low=149.00, latest_trading_day="2024-01-15"
            )
            
            mock_historical.return_value = HistoricalData(
                symbol="AAPL", interval="daily", prices=[]
            )
            
            mock_statement.return_value = FinancialStatement(
                symbol="AAPL", statement_type="income", annual_reports=[], quarterly_reports=[]
            )
            
            response = await service.get_stock_overview("AAPL")
            
            assert response.success is True
            assert response.symbol == "AAPL"
            assert response.quote is not None
            assert response.historical_data is not None
            assert len(response.financial_statements) == 1


class TestFinancialToolFunctions:
    """Test tool functions for pydantic-ai agents."""
    
    @pytest.mark.asyncio
    async def test_get_real_time_quote_success(self):
        """Test successful real-time quote tool."""
        mock_quote = StockQuote(
            symbol="AAPL", price=152.50, change=1.50, change_percent="0.99%",
            volume=50000000, previous_close=151.00, open_price=150.00,
            high=155.00, low=149.00, latest_trading_day="2024-01-15"
        )
        
        with patch.dict('os.environ', {'ALPHA_VANTAGE_API_KEY': 'test_key'}), \
             patch.object(AlphaVantageClient, 'get_quote', return_value=mock_quote):
            
            result = await get_real_time_quote("AAPL")
            
            assert "AAPL" in result
            assert "$152.50" in result
            assert "$1.50" in result
            assert "50,000,000" in result
    
    @pytest.mark.asyncio 
    async def test_get_real_time_quote_no_api_key(self):
        """Test real-time quote without API key."""
        with patch.dict('os.environ', {}, clear=True):
            result = await get_real_time_quote("AAPL")
            
            assert "Error: ALPHA_VANTAGE_API_KEY environment variable not set" in result
    
    @pytest.mark.asyncio
    async def test_get_historical_analysis_success(self):
        """Test successful historical analysis tool."""
        mock_historical = HistoricalData(
            symbol="AAPL",
            interval="daily", 
            prices=[
                {"date": "2024-01-15", "close": 152.50, "volume": 50000000, "high": 155.00, "low": 149.00},
                {"date": "2024-01-14", "close": 151.00, "volume": 45000000, "high": 151.50, "low": 147.00}
            ]
        )
        
        with patch.dict('os.environ', {'ALPHA_VANTAGE_API_KEY': 'test_key'}), \
             patch.object(AlphaVantageClient, 'get_historical_data', return_value=mock_historical):
            
            result = await get_historical_analysis("AAPL")
            
            assert "AAPL" in result
            assert "Performance: +0.99%" in result
            assert "$152.50" in result
    
    @pytest.mark.asyncio
    async def test_get_financial_fundamentals_success(self):
        """Test successful financial fundamentals tool."""
        mock_statement = FinancialStatement(
            symbol="AAPL",
            statement_type="income",
            annual_reports=[{
                "fiscalDateEnding": "2023-09-30",
                "totalRevenue": "383285000000",
                "netIncome": "96995000000",
                "reportedEPS": "6.13"
            }],
            quarterly_reports=[]
        )
        
        with patch.dict('os.environ', {'ALPHA_VANTAGE_API_KEY': 'test_key'}), \
             patch.object(AlphaVantageClient, 'get_financial_statement', return_value=mock_statement):
            
            result = await get_financial_fundamentals("AAPL")
            
            assert "AAPL" in result
            assert "2023-09-30" in result
            assert "383,285,000,000" in result
            assert "$6.13" in result
    
    @pytest.mark.asyncio
    async def test_tool_error_handling(self):
        """Test tool error handling."""
        with patch.dict('os.environ', {'ALPHA_VANTAGE_API_KEY': 'test_key'}), \
             patch.object(AlphaVantageClient, 'get_quote', side_effect=Exception("API Error")):
            
            result = await get_real_time_quote("AAPL")
            
            assert "Error getting quote for AAPL: API Error" in result


if __name__ == "__main__":
    pytest.main([__file__])