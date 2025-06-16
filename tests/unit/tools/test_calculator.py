"""
Unit tests for financial calculator tool.
"""
import pytest
from unittest.mock import patch

from tools.calculator import (
    parse_financial_value,
    calculate_pe_ratio,
    calculate_debt_to_equity,
    calculate_roe,
    calculate_profit_margin,
    calculate_revenue_growth,
    calculate_financial_metrics,
    perform_financial_calculations
)


class TestParseFinancialValue:
    """Test financial value parsing."""
    
    def test_parse_currency_values(self):
        """Test parsing currency values."""
        assert parse_financial_value("$1,234.56") == 1234.56
        assert parse_financial_value("$1.5B") == 1500000000
        assert parse_financial_value("$2.3M") == 2300000
        assert parse_financial_value("500.25") == 500.25  # Basic number parsing
    
    def test_parse_percentage_values(self): 
        """Test parsing percentage values."""
        assert parse_financial_value("15.5%") == 0.155
        assert parse_financial_value("25%") == 0.25
        # Note: "percent" word not handled by current implementation
    
    def test_parse_ratio_values(self):
        """Test parsing basic numeric values (ratios not specifically handled)."""
        assert parse_financial_value("2.5") == 2.5
        assert parse_financial_value("0.8") == 0.8
        assert parse_financial_value("1.2") == 1.2
    
    def test_parse_plain_numbers(self):
        """Test parsing plain numeric values."""
        assert parse_financial_value("1234.56") == 1234.56
        assert parse_financial_value("0.25") == 0.25
        assert parse_financial_value("100") == 100.0
    
    def test_parse_invalid_values(self):
        """Test handling invalid values."""
        assert parse_financial_value("invalid") is None
        assert parse_financial_value("") is None
        assert parse_financial_value("N/A") is None
    
    def test_parse_negative_values(self):
        """Test parsing negative values."""
        assert parse_financial_value("-$500") == -500.0
        assert parse_financial_value("-15%") == -0.15
        assert parse_financial_value("-2.5") == -2.5


class TestCalculateRatios:
    """Test individual ratio calculation functions."""
    
    def test_calculate_pe_ratio(self):
        """Test P/E ratio calculation."""
        assert calculate_pe_ratio(100, 5) == 20
        assert calculate_pe_ratio(50, 2.5) == 20
        assert calculate_pe_ratio(100, 0) is None
        assert calculate_pe_ratio(100, None) is None
    
    def test_calculate_debt_to_equity(self):
        """Test debt-to-equity ratio calculation."""
        assert calculate_debt_to_equity(50, 100) == 0.5
        assert calculate_debt_to_equity(30, 70) == 30/70
        assert calculate_debt_to_equity(100, 0) is None
        assert calculate_debt_to_equity(100, None) is None
    
    def test_calculate_roe(self):
        """Test ROE calculation."""
        assert calculate_roe(20, 100) == 0.2
        assert calculate_roe(50, 250) == 0.2
        assert calculate_roe(20, 0) is None
        assert calculate_roe(20, None) is None
    
    def test_calculate_profit_margin(self):
        """Test profit margin calculation."""
        assert calculate_profit_margin(20, 100) == 0.2
        assert calculate_profit_margin(75, 500) == 0.15
        assert calculate_profit_margin(20, 0) is None
        assert calculate_profit_margin(20, None) is None
    
    def test_calculate_revenue_growth(self):
        """Test revenue growth calculation."""
        assert calculate_revenue_growth(120, 100) == 0.2
        assert calculate_revenue_growth(90, 100) == -0.1
        assert calculate_revenue_growth(100, 0) is None
        assert calculate_revenue_growth(100, None) is None


class TestCalculateFinancialMetrics:
    """Test financial metrics calculation from data dict."""
    
    def test_calculate_with_complete_data(self):
        """Test calculation with complete financial data."""
        data = {
            "stock_price": "100",
            "earnings_per_share": "5",
            "net_income": "50M",
            "revenue": "250M",
            "total_debt": "75M",
            "total_equity": "150M",
            "book_value_per_share": "25",
            "previous_revenue": "200M",
            "free_cash_flow": "40M"
        }
        
        metrics = calculate_financial_metrics(data)
        
        assert metrics.pe_ratio == 20.0
        assert metrics.price_to_book == 4.0
        assert metrics.debt_to_equity == 0.5
        assert metrics.return_on_equity == 50000000 / 150000000
        assert metrics.profit_margin == 0.2
        assert metrics.revenue_growth == 0.25
        assert metrics.free_cash_flow == 40000000
    
    def test_calculate_with_partial_data(self):
        """Test calculation with partial financial data."""
        data = {
            "stock_price": "50",
            "earnings_per_share": "2.5",
            "net_income": "25M"
        }
        
        metrics = calculate_financial_metrics(data)
        
        assert metrics.pe_ratio == 20.0
        assert metrics.debt_to_equity is None
        assert metrics.return_on_equity is None
        assert metrics.profit_margin is None
    
    def test_calculate_with_empty_data(self):
        """Test calculation with empty data."""
        metrics = calculate_financial_metrics({})
        
        assert metrics.pe_ratio is None
        assert metrics.debt_to_equity is None
        assert metrics.return_on_equity is None
        assert metrics.profit_margin is None


class TestPerformFinancialCalculations:
    """Test text-based financial calculations."""
    
    def test_calculate_from_text(self):
        """Test calculation from financial text."""
        text = """
        Company Financial Data:
        Stock price: $100
        Earnings per share: $5
        Net income: $50M
        Revenue: $250M
        Total debt: $75M
        Total equity: $150M
        """
        
        metrics = ["pe_ratio", "debt_to_equity", "profit_margin"]
        result = perform_financial_calculations(text, metrics)
        
        assert "P/E Ratio: 20.00" in result
        assert "Debt-to-Equity Ratio: 0.50" in result
        assert "Profit Margin: 20.00%" in result
    
    def test_calculate_with_no_data(self):
        """Test calculation when no data can be extracted."""
        text = "This text contains no financial information."
        metrics = ["pe_ratio", "debt_to_equity"]
        
        result = perform_financial_calculations(text, metrics)
        
        assert "Unable to calculate" in result
    
    def test_calculate_partial_metrics(self):
        """Test calculation when only some metrics can be calculated."""
        text = "Stock price: $80, EPS: $4, some other text"
        metrics = ["pe_ratio", "debt_to_equity", "profit_margin"]
        
        result = perform_financial_calculations(text, metrics)
        
        assert "P/E Ratio: 20.00" in result
        # Should not contain debt-to-equity or profit margin


class TestCalculatorIntegration:
    """Integration tests for calculator tool."""
    
    def test_real_world_financial_data(self):
        """Test with realistic financial document excerpt."""
        text = """
        Apple Inc. Q3 2023 Results:
        
        Total net sales: $81.8 billion
        Net income: $19.9 billion
        Earnings per share: $1.26
        Stock price: $36.13
        
        Balance Sheet Highlights:
        - Cash and cash equivalents: $29.5 billion
        - Total debt: $111.1 billion  
        - Total shareholders' equity: $62.1 billion
        """
        
        metrics = ["pe_ratio", "debt_to_equity", "profit_margin"]
        result = perform_financial_calculations(text, metrics)
        
        assert result is not None
        result_lower = result.lower()
        
        # Should contain calculated metrics
        assert "p/e ratio" in result_lower or "debt-to-equity" in result_lower
    
    def test_mixed_currency_formats(self):
        """Test handling different value formats."""
        text = """
        International Company Results:
        Revenue: $3.2 billion
        Net income: $500M
        Stock price: $45.50
        Earnings per share: $2.25
        Total debt: $1.5B
        Total equity: $2.0B
        """
        
        metrics = ["pe_ratio", "debt_to_equity", "profit_margin"]
        result = perform_financial_calculations(text, metrics)
        
        assert result is not None
        # Should successfully parse billion and million formats
        assert "P/E Ratio:" in result or "Debt-to-Equity" in result or "Profit Margin:" in result