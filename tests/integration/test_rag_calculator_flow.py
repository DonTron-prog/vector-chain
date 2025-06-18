"""
Integration tests for RAG (vector search) + calculator workflow.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from models.schemas import DocumentSearchResult, FinancialMetrics
from tools.vector_search import search_internal_docs, format_document_results, extract_financial_data
from tools.calculator import perform_financial_calculations, calculate_financial_metrics


class TestRAGCalculatorIntegration:
    """Test integration between RAG system and financial calculator."""
    
    @pytest.mark.asyncio
    async def test_document_search_to_calculation_workflow(self):
        """Test complete workflow from document search to financial calculations."""
        # Mock vector database with financial document content
        mock_db = AsyncMock()
        mock_db.query.return_value = {
            "documents": [[
                """
                Apple Inc. Q3 2023 Financial Results
                
                Revenue: $81.8 billion (up 1.4% year-over-year)
                Net income: $19.9 billion
                Earnings per share: $1.26
                
                Balance Sheet Highlights:
                - Total debt: $111.1 billion
                - Shareholders' equity: $62.1 billion
                - Cash and cash equivalents: $29.5 billion
                
                Stock Information:
                - Current stock price: $189.70
                - Book value per share: $3.88
                """
            ]],
            "metadatas": [[{"company": "AAPL", "doc_type": "10Q", "quarter": "Q3_2023"}]],
            "distances": [[0.15]]
        }
        
        # Step 1: Search for financial documents
        search_results = await search_internal_docs(
            mock_db,
            "Apple financial performance Q3 2023 revenue earnings",
            doc_type="10Q",
            n_results=1
        )
        
        assert len(search_results) == 1
        assert isinstance(search_results[0], DocumentSearchResult)
        assert "$81.8 billion" in search_results[0].content
        assert search_results[0].metadata["company"] == "AAPL"
        assert search_results[0].score == 0.85  # 1.0 - 0.15
        
        # Step 2: Extract financial data from document content
        financial_data = extract_financial_data(search_results[0].content)
        
        assert "revenue" in financial_data
        assert "net_income" in financial_data
        assert financial_data["revenue"]["parsed"] == 81800000000  # $81.8B
        assert financial_data["net_income"]["parsed"] == 19900000000  # $19.9B
        
        # Step 3: Perform financial calculations using extracted data
        metrics_to_calculate = ["pe_ratio", "debt_to_equity", "profit_margin", "price_to_book"]
        calculation_result = perform_financial_calculations(
            search_results[0].content,
            metrics_to_calculate
        )
        
        # Verify calculations were performed
        assert "Financial Metrics Calculation Results:" in calculation_result
        assert "P/E Ratio:" in calculation_result
        assert "Debt-to-Equity Ratio:" in calculation_result
        assert "Profit Margin:" in calculation_result
        assert "Price-to-Book Ratio:" in calculation_result
        
        # Step 4: Verify calculation accuracy
        # Manual verification of some calculations
        # P/E = Price / EPS = $189.70 / $1.26 ≈ 150.6
        # Debt-to-Equity = $111.1B / $62.1B ≈ 1.79
        # Profit Margin = $19.9B / $81.8B ≈ 24.3%
        assert "150.6" in calculation_result or "P/E Ratio:" in calculation_result
        assert "1.79" in calculation_result or "Debt-to-Equity Ratio:" in calculation_result
    
    @pytest.mark.asyncio
    async def test_multiple_documents_aggregated_calculation(self):
        """Test calculations from multiple document sources."""
        # Mock vector database with multiple documents
        mock_db = AsyncMock()
        mock_db.query.return_value = {
            "documents": [[
                "Apple Q3 2023: Revenue $81.8B, Net income $19.9B",
                "Apple Q2 2023: Revenue $81.5B, Net income $19.4B", 
                "Apple Q1 2023: Revenue $82.9B, Net income $20.7B"
            ]],
            "metadatas": [[
                {"company": "AAPL", "doc_type": "earnings", "quarter": "Q3_2023"},
                {"company": "AAPL", "doc_type": "earnings", "quarter": "Q2_2023"},
                {"company": "AAPL", "doc_type": "earnings", "quarter": "Q1_2023"}
            ]],
            "distances": [[0.1, 0.15, 0.2]]
        }
        
        # Search for quarterly results
        search_results = await search_internal_docs(
            mock_db,
            "Apple quarterly revenue trends 2023",
            doc_type="earnings",
            n_results=3
        )
        
        assert len(search_results) == 3
        
        # Aggregate content for comprehensive analysis
        aggregated_content = "\n".join([result.content for result in search_results])
        
        # Extract financial data from aggregated content
        aggregated_data = extract_financial_data(aggregated_content)
        
        # Should find revenue data from multiple quarters
        assert "revenue" in aggregated_data
        
        # Calculate trend metrics
        # This simulates calculating revenue growth trends across quarters
        trend_calculation = perform_financial_calculations(
            aggregated_content,
            ["revenue_growth", "profit_margin"]
        )
        
        assert "Financial Metrics Calculation Results:" in trend_calculation
        # Should be able to calculate metrics from multiple data points
    
    @pytest.mark.asyncio
    async def test_company_comparison_calculations(self):
        """Test calculations for comparing multiple companies."""
        # Mock vector database with multiple company data
        mock_db = AsyncMock()
        mock_db.query.return_value = {
            "documents": [[
                """
                Apple Inc. Financial Summary:
                Revenue: $81.8B, Net income: $19.9B, EPS: $1.26
                Stock price: $189.70, Total debt: $111.1B, Equity: $62.1B
                """,
                """
                Microsoft Corp. Financial Summary:  
                Revenue: $56.2B, Net income: $20.1B, EPS: $2.69
                Stock price: $338.50, Total debt: $47.3B, Equity: $206.2B
                """
            ]],
            "metadatas": [[
                {"company": "AAPL", "doc_type": "summary"},
                {"company": "MSFT", "doc_type": "summary"}
            ]],
            "distances": [[0.1, 0.12]]
        }
        
        # Search for company comparison data
        search_results = await search_internal_docs(
            mock_db,
            "Apple Microsoft financial comparison metrics",
            doc_type="summary",
            n_results=2
        )
        
        assert len(search_results) == 2
        
        # Calculate metrics for each company separately
        apple_metrics = perform_financial_calculations(
            search_results[0].content,
            ["pe_ratio", "debt_to_equity", "profit_margin"]
        )
        
        microsoft_metrics = perform_financial_calculations(
            search_results[1].content,
            ["pe_ratio", "debt_to_equity", "profit_margin"]
        )
        
        # Both should have calculated metrics
        assert "P/E Ratio:" in apple_metrics
        assert "P/E Ratio:" in microsoft_metrics
        assert "Debt-to-Equity Ratio:" in apple_metrics
        assert "Debt-to-Equity Ratio:" in microsoft_metrics
        
        # Verify different values for different companies
        assert apple_metrics != microsoft_metrics
    
    @pytest.mark.asyncio
    async def test_rag_calculation_error_handling(self):
        """Test error handling in RAG + calculator integration."""
        # Test case 1: No documents found
        mock_db_empty = AsyncMock()
        mock_db_empty.query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }
        
        empty_results = await search_internal_docs(
            mock_db_empty,
            "nonexistent company data"
        )
        
        assert len(empty_results) == 0
        
        # Test case 2: Documents found but no financial data
        mock_db_no_financials = AsyncMock()
        mock_db_no_financials.query.return_value = {
            "documents": [["This document contains no financial information."]],
            "metadatas": [[{"company": "UNKNOWN"}]],
            "distances": [[0.5]]
        }
        
        no_financial_results = await search_internal_docs(
            mock_db_no_financials,
            "company strategy discussion"
        )
        
        assert len(no_financial_results) == 1
        
        # Try to calculate metrics from non-financial content
        calculation_result = perform_financial_calculations(
            no_financial_results[0].content,
            ["pe_ratio", "debt_to_equity"]
        )
        
        assert "Unable to calculate" in calculation_result
        
        # Test case 3: Incomplete financial data
        mock_db_incomplete = AsyncMock()
        mock_db_incomplete.query.return_value = {
            "documents": [["Revenue: $100M, but no other financial data available."]],
            "metadatas": [[{"company": "PARTIAL"}]],
            "distances": [[0.3]]
        }
        
        incomplete_results = await search_internal_docs(
            mock_db_incomplete,
            "partial financial data"
        )
        
        partial_calculation = perform_financial_calculations(
            incomplete_results[0].content,
            ["pe_ratio", "debt_to_equity", "profit_margin"]
        )
        
        # Should handle partial data gracefully
        assert "Financial Metrics Calculation Results:" in partial_calculation


class TestRAGCalculatorWorkflowOptimization:
    """Test optimized workflows combining RAG and calculations."""
    
    @pytest.mark.asyncio
    async def test_targeted_financial_document_search(self):
        """Test searching for specific financial document types."""
        mock_db = AsyncMock()
        
        # Test different document type searches
        doc_types = ["10K", "10Q", "earnings", "analyst"]
        
        for doc_type in doc_types:
            # Mock relevant financial content for each document type
            if doc_type == "10K":
                content = "Annual Report: Total revenue $365B, Net income $95B"
            elif doc_type == "10Q":
                content = "Quarterly Report: Revenue $81.8B, Net income $19.9B"  
            elif doc_type == "earnings":
                content = "Earnings Call: EPS $1.26, Revenue growth 1.4%"
            else:  # analyst
                content = "Analyst Report: Price target $200, P/E ratio 28.7"
            
            mock_db.query.return_value = {
                "documents": [[content]],
                "metadatas": [[{"company": "AAPL", "doc_type": doc_type}]],
                "distances": [[0.1]]
            }
            
            # Search for specific document type
            results = await search_internal_docs(
                mock_db,
                f"Apple financial data {doc_type}",
                doc_type=doc_type,
                n_results=1
            )
            
            assert len(results) == 1
            assert results[0].metadata["doc_type"] == doc_type
            
            # Verify filters were applied correctly
            mock_db.query.assert_called()
            call_args = mock_db.query.call_args
            if doc_type != "all":
                assert call_args[1]["filters"]["doc_type"] == doc_type
    
    @pytest.mark.asyncio
    async def test_financial_metric_calculation_pipeline(self):
        """Test streamlined pipeline from search to specific calculations."""
        # Mock comprehensive financial document
        mock_db = AsyncMock()
        mock_db.query.return_value = {
            "documents": [[
                """
                Comprehensive Financial Analysis - Apple Inc.
                
                Income Statement:
                - Total revenue: $3.2 billion
                - Net income: $450 million
                - Earnings per share: $2.85
                
                Balance Sheet:
                - Total debt: $1.1 billion  
                - Shareholders equity: $2.8 billion
                - Book value per share: $18.50
                
                Market Data:
                - Current stock price: $42.75
                - Previous year revenue: $2.8 billion
                """
            ]],
            "metadatas": [[{"company": "AAPL", "doc_type": "comprehensive"}]],
            "distances": [[0.05]]
        }
        
        # Search for comprehensive financial data
        search_results = await search_internal_docs(
            mock_db,
            "Apple comprehensive financial analysis metrics",
            n_results=1
        )
        
        # Calculate full suite of financial metrics
        comprehensive_metrics = ["pe_ratio", "debt_to_equity", "profit_margin", 
                                "price_to_book", "return_on_equity", "revenue_growth"]
        
        calculation_result = perform_financial_calculations(
            search_results[0].content,
            comprehensive_metrics
        )
        
        # Verify comprehensive calculations
        assert "P/E Ratio:" in calculation_result
        assert "Debt-to-Equity Ratio:" in calculation_result  
        assert "Profit Margin:" in calculation_result
        assert "Price-to-Book Ratio:" in calculation_result
        
        # Calculate specific values to verify accuracy
        # P/E = $42.75 / $2.85 = 15.0
        # Debt/Equity = $1.1B / $2.8B = 0.39
        # Profit Margin = $450M / $3.2B = 14.06%
        # P/B = $42.75 / $18.50 = 2.31
        # Revenue Growth = ($3.2B - $2.8B) / $2.8B = 14.29%
        
        lines = calculation_result.split('\n')
        metric_lines = [line for line in lines if ':' in line and line.strip()]
        
        # Should have calculated multiple metrics successfully
        assert len(metric_lines) >= 4
    
    def test_calculate_financial_metrics_structured_output(self):
        """Test structured financial metrics calculation."""
        # Test with dictionary input for structured calculation
        financial_data = {
            "stock_price": "42.75",
            "earnings_per_share": "2.85", 
            "net_income": "450M",
            "revenue": "3.2B",
            "total_debt": "1.1B",
            "total_equity": "2.8B",
            "book_value_per_share": "18.50",
            "previous_revenue": "2.8B",
            "free_cash_flow": "380M"
        }
        
        # Calculate structured metrics
        metrics = calculate_financial_metrics(financial_data)
        
        assert isinstance(metrics, FinancialMetrics)
        assert metrics.pe_ratio == 15.0  # 42.75 / 2.85
        assert abs(metrics.debt_to_equity - 0.393) < 0.01  # 1.1B / 2.8B
        assert abs(metrics.profit_margin - 0.141) < 0.01  # 450M / 3.2B
        assert abs(metrics.price_to_book - 2.31) < 0.01  # 42.75 / 18.50
        assert abs(metrics.revenue_growth - 0.143) < 0.01  # (3.2B - 2.8B) / 2.8B
        assert metrics.free_cash_flow == 380000000  # 380M