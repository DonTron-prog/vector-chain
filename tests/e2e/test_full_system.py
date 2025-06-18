"""
End-to-end tests for the complete investment research system.
"""
import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from models.schemas import InvestmentAnalysis


@pytest.mark.e2e
@pytest.mark.slow
class TestFullSystemE2E:
    """End-to-end tests requiring full system setup."""
    
    @pytest.mark.skipif(
        not os.getenv("OPENROUTER_API_KEY"),
        reason="API key required for E2E tests"
    )
    @pytest.mark.asyncio
    async def test_real_investment_analysis(self, temp_dir, knowledge_base_files):
        """Test complete system with real API calls (when API key available)."""
        # Only run if API keys are available
        query = "Should I invest in technology stocks for long-term growth?"
        context = "Conservative investor, 10-year horizon, moderate risk tolerance"
        
        # Set up temporary knowledge base
        os.environ["KNOWLEDGE_BASE_PATH"] = str(knowledge_base_files)
        os.environ["CHROMA_DB_PATH"] = str(temp_dir / "test_chroma")
        
        try:
            from main import research_investment
            
            result = await research_investment(query, context)
            
            # Verify complete analysis structure
            assert isinstance(result, InvestmentAnalysis)
            assert result.query == query
            assert result.context == context
            assert result.created_at is not None
            
            # Verify financial metrics
            assert result.financial_metrics is not None
            
            # Verify findings
            assert result.findings is not None
            assert len(result.findings.summary) > 0
            assert len(result.findings.key_insights) > 0
            assert len(result.findings.risk_factors) > 0
            assert result.findings.recommendation in ["BUY", "SELL", "HOLD"]
            assert 0.0 <= result.findings.confidence_score <= 1.0
            
        finally:
            # Clean up environment
            if "KNOWLEDGE_BASE_PATH" in os.environ:
                del os.environ["KNOWLEDGE_BASE_PATH"]
            if "CHROMA_DB_PATH" in os.environ:
                del os.environ["CHROMA_DB_PATH"]
    
    @pytest.mark.asyncio
    async def test_system_with_mocked_externals(self, temp_dir, knowledge_base_files):
        """Test full system with mocked external services."""
        query = "Analyze AAPL for value investing"
        context = "Value investor looking for undervalued opportunities"
        
        # Mock external services
        with patch('aiohttp.ClientSession.get') as mock_get, \
             patch('openai.OpenAI') as mock_openai, \
             patch('chromadb.PersistentClient') as mock_chroma:
            
            # Mock web responses
            mock_response = MagicMock()
            mock_response.text.return_value = """
            <html><body>
            <h1>Apple Q3 2023 Results</h1>
            <p>Revenue: $81.8 billion</p>
            <p>Net Income: $19.9 billion</p>
            <p>P/E Ratio: 28.7</p>
            </body></html>
            """
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Mock OpenAI responses
            mock_openai_client = MagicMock()
            mock_completion = MagicMock()
            mock_completion.choices[0].message.content = '''
            {
                "steps": [
                    {
                        "description": "Research AAPL financial statements",
                        "reasoning": "Need current financial data",
                        "priority": "high"
                    },
                    {
                        "description": "Analyze valuation metrics",
                        "reasoning": "Determine if undervalued",
                        "priority": "high"
                    }
                ],
                "reasoning": "Systematic value analysis approach"
            }
            '''
            mock_openai_client.chat.completions.create.return_value = mock_completion
            mock_openai.return_value = mock_openai_client
            
            # Mock ChromaDB
            mock_chroma_client = MagicMock()
            mock_collection = MagicMock()
            mock_collection.query.return_value = {
                "documents": [["AAPL 10-K filing with financial data"]],
                "metadatas": [[{"company": "AAPL", "document_type": "10K"}]],
                "distances": [[0.1]]
            }
            mock_chroma_client.get_or_create_collection.return_value = mock_collection
            mock_chroma.return_value = mock_chroma_client
            
            # Set up environment
            os.environ["KNOWLEDGE_BASE_PATH"] = str(knowledge_base_files)
            os.environ["CHROMA_DB_PATH"] = str(temp_dir / "test_chroma")
            
            try:
                from main import research_investment
                
                result = await research_investment(query, context)
                
                # Verify system executed successfully
                assert isinstance(result, InvestmentAnalysis)
                assert result.query == query
                assert result.context == context
                
                # Verify external services were called
                assert mock_get.called
                assert mock_openai_client.chat.completions.create.called
                assert mock_collection.query.called
                
            finally:
                # Clean up environment
                if "KNOWLEDGE_BASE_PATH" in os.environ:
                    del os.environ["KNOWLEDGE_BASE_PATH"]
                if "CHROMA_DB_PATH" in os.environ:
                    del os.environ["CHROMA_DB_PATH"]
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, temp_dir, knowledge_base_files):
        """Test system behavior with partial failures."""
        query = "Test error recovery"
        context = "Testing resilience"
        
        # Test with SearxNG unavailable
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock SearxNG failure
            mock_get.side_effect = Exception("SearxNG unavailable")
            
            # System should still work with other data sources
            from main import research_investment
            
            # Should not crash, but might have limited analysis
            result = await research_investment(query, context)
            assert isinstance(result, InvestmentAnalysis)
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests(self, temp_dir, knowledge_base_files):
        """Test system under concurrent load."""
        import asyncio
        
        queries = [
            ("Analyze AAPL", "Long-term growth"),
            ("Research MSFT", "Dividend income"),
            ("Evaluate GOOGL", "Value investing")
        ]
        
        # Mock external services for consistency
        with patch('aiohttp.ClientSession.get') as mock_get, \
             patch('openai.OpenAI') as mock_openai, \
             patch('chromadb.PersistentClient') as mock_chroma:
            
            # Set up mocks (simplified)
            mock_response = MagicMock()
            mock_response.text.return_value = "<html><body>Mock data</body></html>"
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response
            
            mock_openai_client = MagicMock()
            mock_completion = MagicMock()
            mock_completion.choices[0].message.content = '{"steps": [], "reasoning": "test"}'
            mock_openai_client.chat.completions.create.return_value = mock_completion
            mock_openai.return_value = mock_openai_client
            
            mock_chroma_client = MagicMock()
            mock_collection = MagicMock()
            mock_collection.query.return_value = {"documents": [[]], "metadatas": [[]], "distances": [[]]}
            mock_chroma_client.get_or_create_collection.return_value = mock_collection
            mock_chroma.return_value = mock_chroma_client
            
            # Set up environment
            os.environ["KNOWLEDGE_BASE_PATH"] = str(knowledge_base_files)
            os.environ["CHROMA_DB_PATH"] = str(temp_dir / "test_chroma")
            
            try:
                from main import research_investment
                
                # Run concurrent requests
                tasks = [
                    research_investment(query, context)
                    for query, context in queries
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Verify all requests completed
                assert len(results) == len(queries)
                
                # Verify no exceptions
                for result in results:
                    assert not isinstance(result, Exception)
                    assert isinstance(result, InvestmentAnalysis)
                
            finally:
                # Clean up environment
                if "KNOWLEDGE_BASE_PATH" in os.environ:
                    del os.environ["KNOWLEDGE_BASE_PATH"]
                if "CHROMA_DB_PATH" in os.environ:
                    del os.environ["CHROMA_DB_PATH"]


@pytest.mark.e2e
class TestSystemConfiguration:
    """Test system configuration and environment setup."""
    
    def test_environment_variable_handling(self, monkeypatch):
        """Test proper handling of environment variables."""
        # Test with missing required variables
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        
        # System should handle gracefully or raise appropriate errors
        from agents.dependencies import ResearchDependencies
        
        # Should either work with defaults or raise clear error
        try:
            from agents.dependencies import initialize_dependencies
            deps = initialize_dependencies("Test query")
            # If it works, dependencies should be initialized
            assert deps is not None
        except Exception as e:
            # If it fails, should be clear about missing config or required fields
            error_msg = str(e).lower()
            assert "api" in error_msg or "key" in error_msg or "field required" in error_msg
    
    def test_knowledge_base_setup(self, knowledge_base_files):
        """Test knowledge base initialization."""
        from agents.dependencies import initialize_dependencies
        
        # Mock environment for initialization
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            deps = initialize_dependencies(
                "test query",
                knowledge_base_path=str(knowledge_base_files)
            )
        
        # Verify knowledge base is accessible
        assert knowledge_base_files.exists()
        assert (knowledge_base_files / "AAPL").exists()
        assert (knowledge_base_files / "MSFT").exists()
    
    def test_database_persistence(self, temp_dir):
        """Test ChromaDB persistence across sessions."""
        from agents.dependencies import initialize_dependencies
        
        db_path = temp_dir / "test_persistence"
        
        # Mock environment for initialization
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            # Create first session
            deps1 = initialize_dependencies(
                "test query 1",
                chroma_db_path=str(db_path)
            )
            
            # Create second session (should reuse existing database)
            deps2 = initialize_dependencies(
                "test query 2",
                chroma_db_path=str(db_path)
            )
        
        # Both should work
        assert deps1.vector_db is not None
        assert deps2.vector_db is not None


@pytest.mark.e2e
@pytest.mark.network
class TestExternalServiceIntegration:
    """Test integration with external services (when available)."""
    
    @pytest.mark.skipif(
        not os.getenv("TEST_EXTERNAL_SERVICES"),
        reason="External service tests disabled"
    )
    @pytest.mark.asyncio
    async def test_searxng_integration(self):
        """Test SearxNG integration (when service is available)."""
        from tools.web_search import search_web
        
        # Test basic search
        result = await search_web("AAPL stock price", "general")
        
        assert result is not None
        assert len(result) > 0
        assert "apple" in result.lower() or "aapl" in result.lower()
    
    @pytest.mark.skipif(
        not os.getenv("TEST_EXTERNAL_SERVICES"),
        reason="External service tests disabled"
    )
    @pytest.mark.asyncio
    async def test_web_scraping_integration(self):
        """Test web scraping with real websites."""
        from tools.web_scraper import scrape_webpage
        
        # Test scraping a financial news site
        url = "https://finance.yahoo.com"  # Example - replace with appropriate test URL
        
        result = await scrape_webpage(url, "article")
        
        assert result is not None
        assert len(result) > 0
        # Should contain financial content
        assert any(term in result.lower() for term in ["stock", "market", "financial", "price"])