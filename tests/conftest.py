"""
Shared pytest configuration and fixtures for the investment research system.
"""
import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from chromadb import PersistentClient
from pydantic_ai import Agent

from models.schemas import (
    FinancialMetrics,
    InvestmentAnalysis,
    InvestmentFindings,
    ResearchPlan,
    ResearchStep
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    test_env = {
        "OPENROUTER_API_KEY": "test-openrouter-key",
        "OPENAI_API_KEY": "test-openai-key",
        "SEARXNG_URL": "http://localhost:8080",
        "CHROMA_DB_PATH": "./test_chroma_db"
    }
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
    return test_env


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing agents."""
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock()
    return mock_client


@pytest.fixture
def mock_chroma_client(temp_dir):
    """Mock ChromaDB client for testing."""
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    mock_collection.query.return_value = {
        "documents": [["Sample investment document content"]],
        "metadatas": [[{"company": "AAPL", "document_type": "10K"}]],
        "distances": [[0.1]]
    }
    return mock_client


@pytest.fixture
def mock_searxng_client():
    """Mock SearxNG client for testing."""
    mock_client = AsyncMock()
    mock_client.search = AsyncMock(return_value={
        "results": [
            {
                "title": "Sample Investment News",
                "url": "https://example.com/news",
                "content": "Sample investment news content"
            }
        ]
    })
    return mock_client


@pytest.fixture
def sample_research_plan():
    """Sample research plan for testing."""
    return ResearchPlan(
        steps=[
            ResearchStep(
                description="Search for recent financial performance",
                reasoning="Need current financial data",
                priority="high"
            ),
            ResearchStep(
                description="Analyze competitive position",
                reasoning="Understand market dynamics",
                priority="medium"
            )
        ],
        reasoning="Comprehensive analysis approach"
    )


@pytest.fixture
def sample_financial_metrics():
    """Sample financial metrics for testing."""
    return FinancialMetrics(
        pe_ratio=25.5,
        debt_to_equity=0.3,
        roe=0.18,
        revenue_growth=0.12,
        profit_margin=0.22,
        current_ratio=1.5
    )


@pytest.fixture
def sample_investment_findings():
    """Sample investment findings for testing."""
    return InvestmentFindings(
        summary="Strong financial performance with growth potential",
        key_insights=[
            "Revenue growth accelerating",
            "Strong market position",
            "Reasonable valuation"
        ],
        risk_factors=[
            "Market volatility",
            "Regulatory changes"
        ],
        recommendation="BUY",
        confidence_score=0.75
    )


@pytest.fixture
def sample_investment_analysis(sample_financial_metrics, sample_investment_findings):
    """Sample complete investment analysis for testing."""
    return InvestmentAnalysis(
        query="Should I invest in AAPL?",
        context="Long-term growth investment",
        financial_metrics=sample_financial_metrics,
        findings=sample_investment_findings
    )


@pytest.fixture
def mock_web_content():
    """Mock web content for scraping tests."""
    return """
    <html>
        <head><title>Investment News</title></head>
        <body>
            <article>
                <h1>Company Shows Strong Q3 Results</h1>
                <p>The company reported revenue of $50B, up 15% year-over-year.</p>
                <p>Earnings per share increased to $2.50, beating estimates.</p>
            </article>
        </body>
    </html>
    """


@pytest.fixture
def knowledge_base_files(temp_dir):
    """Create sample knowledge base files for testing."""
    # Create company directories
    aapl_dir = temp_dir / "AAPL"
    msft_dir = temp_dir / "MSFT"
    aapl_dir.mkdir()
    msft_dir.mkdir()
    
    # Create sample documents
    (aapl_dir / "AAPL_10K_2023.txt").write_text(
        "Apple Inc. 10-K Filing 2023\n"
        "Revenue: $394.3 billion\n"
        "Net Income: $97.0 billion\n"
        "Strong iPhone sales growth"
    )
    
    (msft_dir / "MSFT_10K_2023.txt").write_text(
        "Microsoft Corporation 10-K Filing 2023\n"
        "Revenue: $211.9 billion\n"
        "Net Income: $72.4 billion\n"
        "Azure cloud growth continues"
    )
    
    return temp_dir


@pytest.fixture
async def mock_research_dependencies(
    mock_openai_client,
    mock_chroma_client,
    mock_searxng_client,
    knowledge_base_files
):
    """Mock dependencies for research agents."""
    from agents.dependencies import ResearchDependencies
    
    deps = ResearchDependencies(
        openai_client=mock_openai_client,
        chroma_client=mock_chroma_client,
        searxng_client=mock_searxng_client,
        knowledge_base_path=knowledge_base_files
    )
    return deps


class MockHTTPResponse:
    """Mock HTTP response for testing web scraping."""
    
    def __init__(self, content: str, status_code: int = 200):
        self.content = content
        self.status_code = status_code
        self.headers = {"content-type": "text/html"}
    
    async def text(self):
        return self.content
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_http_session():
    """Mock aiohttp session for testing."""
    session = AsyncMock()
    return session


# Markers for different test categories
pytestmark = [
    pytest.mark.asyncio,
]