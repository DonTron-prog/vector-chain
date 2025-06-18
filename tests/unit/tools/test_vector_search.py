"""
Unit tests for vector search tool.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from models.schemas import DocumentSearchResult
from tools.vector_search import (
    search_internal_docs,
    format_document_results,
    extract_financial_data
)


class TestSearchInternalDocs:
    """Test vector database search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_with_results(self):
        """Test successful search with results."""
        # Mock vector database
        mock_db = AsyncMock()
        mock_db.query.return_value = {
            "documents": [["Apple Inc. Q3 2023 revenue was $81.8 billion."]],
            "metadatas": [[{"company": "AAPL", "doc_type": "10Q"}]],
            "distances": [[0.2]]
        }
        
        results = await search_internal_docs(
            mock_db,
            "Apple revenue Q3 2023",
            doc_type="10Q",
            n_results=1
        )
        
        assert len(results) == 1
        assert isinstance(results[0], DocumentSearchResult)
        assert results[0].content == "Apple Inc. Q3 2023 revenue was $81.8 billion."
        assert results[0].metadata["company"] == "AAPL"
        assert results[0].score == 0.8  # 1.0 - 0.2
    
    @pytest.mark.asyncio
    async def test_search_no_results(self):
        """Test search with no results."""
        mock_db = AsyncMock()
        mock_db.query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }
        
        results = await search_internal_docs(mock_db, "nonexistent query")
        
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self):
        """Test search with document type filters."""
        mock_db = AsyncMock()
        mock_db.query.return_value = {
            "documents": [["Earnings call transcript..."]],
            "metadatas": [[{"company": "MSFT", "doc_type": "earnings"}]],
            "distances": [[0.1]]
        }
        
        await search_internal_docs(
            mock_db,
            "Microsoft earnings",
            doc_type="earnings"
        )
        
        # Verify filters were applied
        mock_db.query.assert_called_once()
        call_args = mock_db.query.call_args
        assert call_args[1]["filters"]["doc_type"] == "earnings"
    
    @pytest.mark.asyncio
    async def test_search_database_error(self):
        """Test handling database errors."""
        mock_db = AsyncMock()
        mock_db.query.side_effect = Exception("Database connection failed")
        
        results = await search_internal_docs(mock_db, "test query")
        
        assert len(results) == 0


class TestFormatDocumentResults:
    """Test document results formatting."""
    
    def test_format_with_results(self):
        """Test formatting results for LLM consumption."""
        results = [
            DocumentSearchResult(
                content="Apple Inc. reported record revenue of $81.8 billion in Q3.",
                metadata={"company": "AAPL", "doc_type": "10Q"},
                score=0.9
            ),
            DocumentSearchResult(
                content="Microsoft Azure revenue grew 27% year-over-year.",
                metadata={"company": "MSFT", "doc_type": "earnings"},
                score=0.8
            )
        ]
        
        formatted = format_document_results(results)
        
        assert "Internal Document Search Results:" in formatted
        assert "Score: 0.90" in formatted
        assert "Source: AAPL - 10Q" in formatted
        assert "Content: Apple Inc. reported record revenue" in formatted
        assert "Source: MSFT - earnings" in formatted
    
    def test_format_no_results(self):
        """Test formatting when no results found."""
        formatted = format_document_results([])
        
        assert formatted == "No internal documents found matching the query."
    
    def test_format_long_content(self):
        """Test formatting with long content (should be truncated)."""
        long_content = "A" * 1000  # 1000 character string
        
        result = DocumentSearchResult(
            content=long_content,
            metadata={"company": "TEST"},
            score=0.7
        )
        
        formatted = format_document_results([result])
        
        # Should be truncated to 800 chars + "..."
        assert "A" * 800 + "..." in formatted
        assert len(formatted.split("Content: ")[1].split("\n")[0]) <= 804


class TestExtractFinancialData:
    """Test financial data extraction from documents."""
    
    def test_extract_revenue_data(self):
        """Test extracting revenue information."""
        content = """
        Company Performance Summary:
        Total revenue for the quarter was $3.2 billion, up from $2.8 billion 
        in the prior year. Net income reached $450 million.
        """
        
        data = extract_financial_data(content)
        
        assert "revenue" in data
        assert data["revenue"]["raw"] == "$3.2 billion"
        assert data["revenue"]["parsed"] == 3200000000
    
    def test_extract_multiple_metrics(self):
        """Test extracting multiple financial metrics."""
        content = """
        Financial Highlights:
        - Revenue: $5.7B
        - Net income: $890M  
        - P/E ratio: 18.5
        - Market cap: $45.2 billion
        """
        
        data = extract_financial_data(content)
        
        assert "revenue" in data
        assert "net_income" in data
        assert "pe_ratio" in data
        assert "market_cap" in data
        
        assert data["revenue"]["parsed"] == 5700000000
        assert data["net_income"]["parsed"] == 890000000
        assert data["pe_ratio"]["parsed"] == 18.5
    
    def test_extract_no_financial_data(self):
        """Test when no financial data is found."""
        content = "This is just general text about the company's strategy."
        
        data = extract_financial_data(content)
        
        assert len(data) == 0
    
    def test_extract_mixed_formats(self):
        """Test extraction with different value formats."""
        content = """
        Q3 Results:
        Revenue was $2.3B, while net income totaled $340 million.
        The company's market cap stands at $12.5 billion.
        """
        
        data = extract_financial_data(content)
        
        assert data["revenue"]["parsed"] == 2300000000
        assert data["net_income"]["parsed"] == 340000000
        assert data["market_cap"]["parsed"] == 12500000000


class TestVectorSearchIntegration:
    """Integration tests for vector search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_and_format_workflow(self):
        """Test complete search and format workflow."""
        # Mock successful search
        mock_db = AsyncMock()
        mock_db.query.return_value = {
            "documents": [["Apple revenue $81.8B, net income $19.9B"]],
            "metadatas": [[{"company": "AAPL", "doc_type": "10Q"}]],
            "distances": [[0.15]]
        }
        
        # Search and format
        results = await search_internal_docs(mock_db, "Apple financial performance")
        formatted = format_document_results(results)
        
        assert len(results) == 1
        assert "AAPL - 10Q" in formatted
        assert "Score: 0.85" in formatted
        assert "$81.8B" in formatted
    
    def test_extract_and_parse_workflow(self):
        """Test document content extraction and parsing."""
        content = """
        Apple Inc. Q3 2023 Financial Results
        
        Revenue: $81.8 billion (up 1% YoY)
        Net income: $19.9 billion  
        Earnings per share: $1.26
        P/E ratio: 28.7
        
        The company maintains a strong balance sheet with minimal debt.
        """
        
        # Extract financial data
        data = extract_financial_data(content)
        
        # Should find multiple metrics
        assert len(data) >= 2
        assert "revenue" in data
        assert "net_income" in data
        
        # Values should be parsed correctly
        assert data["revenue"]["parsed"] == 81800000000
        assert data["net_income"]["parsed"] == 19900000000