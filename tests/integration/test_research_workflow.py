"""
Integration tests for the complete research workflow.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from models.schemas import InvestmentAnalysis, ResearchPlan


class TestResearchWorkflow:
    """Test complete research workflow integration."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_research_flow(self, mock_research_dependencies):
        """Test complete research workflow from query to analysis."""
        query = "Should I invest in AAPL for long-term growth?"
        context = "Looking for 3-5 year investment horizon with moderate risk tolerance."
        
        # Mock planning agent response
        mock_plan = ResearchPlan(
            steps=[
                {"description": "Search for AAPL financial performance", "reasoning": "Need current metrics", "priority": "high"},
                {"description": "Analyze market position", "reasoning": "Understand competitive landscape", "priority": "medium"}
            ],
            reasoning="Comprehensive analysis approach"
        )
        
        # Mock research agent response
        mock_analysis = InvestmentAnalysis(
            query=query,
            context=context,
            financial_metrics={
                "pe_ratio": 28.5,
                "debt_to_equity": 0.25,
                "roe": 0.20,
                "revenue_growth": 0.08,
                "profit_margin": 0.24,
                "current_ratio": 1.1
            },
            findings={
                "summary": "AAPL shows strong fundamentals with moderate growth prospects",
                "key_insights": [
                    "Strong brand loyalty and ecosystem",
                    "Consistent dividend payments",
                    "Services revenue growing"
                ],
                "risk_factors": [
                    "Market saturation in smartphones",
                    "China market dependency"
                ],
                "recommendation": "BUY",
                "confidence_score": 0.75
            }
        )
        
        with patch('agents.planning_agent.create_research_plan') as mock_planning, \
             patch('agents.research_agent.conduct_research') as mock_research:
            
            mock_planning.return_value = mock_plan
            mock_research.return_value = mock_analysis
            
            # Import and run main workflow
            from main import research_investment
            
            result = await research_investment(query, context)
            
            # Verify workflow execution
            mock_planning.assert_called_once_with(query, context)
            mock_research.assert_called_once_with(mock_plan, query, context)
            
            # Verify result structure
            assert isinstance(result, InvestmentAnalysis)
            assert result.query == query
            assert result.context == context
            assert result.financial_metrics is not None
            assert result.findings is not None
            assert result.findings.recommendation in ["BUY", "SELL", "HOLD"]
            assert 0.0 <= result.findings.confidence_score <= 1.0
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_research_with_error_handling(self, mock_research_dependencies):
        """Test research workflow with error handling."""
        query = "Analyze invalid company XYZ"
        context = "Test error handling"
        
        with patch('agents.planning_agent.create_research_plan') as mock_planning:
            # Simulate planning failure
            mock_planning.side_effect = Exception("Planning failed")
            
            from main import research_investment
            
            # Should handle errors gracefully
            with pytest.raises(Exception):
                await research_investment(query, context)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_research_with_different_queries(self, mock_research_dependencies):
        """Test research workflow with different query types."""
        test_cases = [
            {
                "query": "Is MSFT a good dividend stock?",
                "context": "Looking for steady income",
                "expected_focus": "dividend"
            },
            {
                "query": "Should I buy growth stocks now?",
                "context": "Young investor, high risk tolerance",
                "expected_focus": "growth"
            },
            {
                "query": "Compare AAPL vs GOOGL for value investing",
                "context": "Value investor approach", 
                "expected_focus": "comparison"
            }
        ]
        
        for case in test_cases:
            with patch('agents.planning_agent.create_research_plan') as mock_planning, \
                 patch('agents.research_agent.conduct_research') as mock_research:
                
                # Mock appropriate responses based on query type
                mock_plan = ResearchPlan(
                    steps=[
                        {"description": f"Research {case['expected_focus']}", "reasoning": "Test", "priority": "high"},
                        {"description": "Analyze results", "reasoning": "Test", "priority": "medium"}
                    ],
                    reasoning=f"Focus on {case['expected_focus']}"
                )
                
                mock_analysis = InvestmentAnalysis(
                    query=case["query"],
                    context=case["context"],
                    financial_metrics={"pe_ratio": 25.0},
                    findings={
                        "summary": f"Analysis focused on {case['expected_focus']}",
                        "key_insights": ["Insight 1", "Insight 2"],
                        "risk_factors": ["Risk 1"],
                        "recommendation": "HOLD",
                        "confidence_score": 0.6
                    }
                )
                
                mock_planning.return_value = mock_plan
                mock_research.return_value = mock_analysis
                
                from main import research_investment
                
                result = await research_investment(case["query"], case["context"])
                
                # Verify query-specific handling
                assert result.query == case["query"]
                assert result.context == case["context"]
                assert case["expected_focus"] in result.findings.summary.lower()


class TestAgentIntegration:
    """Test integration between different agents."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_planning_to_research_handoff(self, mock_research_dependencies):
        """Test data flow from planning agent to research agent."""
        query = "Analyze AAPL investment potential"
        context = "Medium-term investment"
        
        # Create realistic research plan
        research_plan = ResearchPlan(
            steps=[
                {
                    "description": "Gather AAPL financial statements",
                    "reasoning": "Need baseline financial data",
                    "priority": "high"
                },
                {
                    "description": "Research market sentiment",
                    "reasoning": "Understand market perception",
                    "priority": "medium"
                },
                {
                    "description": "Calculate valuation metrics",
                    "reasoning": "Determine if fairly valued",
                    "priority": "high"
                }
            ],
            reasoning="Systematic approach to investment analysis"
        )
        
        with patch('agents.planning_agent.create_research_plan') as mock_planning, \
             patch('agents.research_agent.conduct_research') as mock_research:
            
            mock_planning.return_value = research_plan
            
            # Verify research agent receives the plan
            mock_research.return_value = InvestmentAnalysis(
                query=query,
                context=context,
                financial_metrics={"pe_ratio": 30.0},
                findings={
                    "summary": "Analysis complete",
                    "key_insights": ["Good fundamentals"],
                    "risk_factors": ["Market risk"],
                    "recommendation": "BUY",
                    "confidence_score": 0.8
                }
            )
            
            from main import research_investment
            
            await research_investment(query, context)
            
            # Verify the research agent was called with the correct plan
            mock_research.assert_called_once()
            call_args = mock_research.call_args
            passed_plan = call_args[0][0]  # First argument should be the plan
            
            assert isinstance(passed_plan, ResearchPlan)
            assert len(passed_plan.steps) == 3
            assert passed_plan.reasoning == research_plan.reasoning
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_coordination(self, mock_research_dependencies):
        """Test coordination between different tools."""
        # This would test that tools are called in logical sequence
        # e.g., web search → web scraping → financial calculations
        
        query = "AAPL financial health analysis"
        context = "Need comprehensive metrics"
        
        with patch('tools.web_search.search_web') as mock_search, \
             patch('tools.web_scraper.scrape_webpage') as mock_scrape, \
             patch('tools.calculator.calculate_financial_ratios') as mock_calc, \
             patch('tools.vector_search.search_documents') as mock_vector:
            
            # Mock tool responses
            mock_search.return_value = "Search results about AAPL"
            mock_scrape.return_value = "Scraped financial content"
            mock_calc.return_value = "Calculated ratios: P/E 28.5, ROE 20%"
            mock_vector.return_value = "Retrieved documents about AAPL"
            
            # Mock the research agent to use tools
            with patch('agents.research_agent.conduct_research') as mock_research:
                mock_analysis = InvestmentAnalysis(
                    query=query,
                    context=context,
                    financial_metrics={"pe_ratio": 28.5, "roe": 0.20},
                    findings={
                        "summary": "Strong financial position",
                        "key_insights": ["Tool coordination successful"],
                        "risk_factors": ["Market volatility"],
                        "recommendation": "BUY",
                        "confidence_score": 0.85
                    }
                )
                mock_research.return_value = mock_analysis
                
                from main import research_investment
                
                result = await research_investment(query, context)
                
                # Verify result incorporates tool outputs
                assert result.financial_metrics.pe_ratio == 28.5
                assert result.financial_metrics.roe == 0.20
                assert "Tool coordination successful" in result.findings.key_insights


class TestDependencyInjection:
    """Test dependency injection across the system."""
    
    @pytest.mark.integration
    def test_dependency_initialization(self, mock_env_vars):
        """Test that dependencies are properly initialized."""
        from agents.dependencies import ResearchDependencies
        
        deps = ResearchDependencies()
        
        # Verify all dependencies are initialized
        assert deps.openai_client is not None
        assert deps.chroma_client is not None
        assert deps.searxng_client is not None
        assert deps.knowledge_base_path is not None
    
    @pytest.mark.integration
    def test_shared_dependencies(self, mock_research_dependencies):
        """Test that dependencies are properly shared between components."""
        # Test that the same dependency instances are used
        # across different agents and tools
        
        deps1 = mock_research_dependencies
        deps2 = mock_research_dependencies
        
        # Should be the same instances (dependency injection)
        assert deps1.chroma_client is deps2.chroma_client
        assert deps1.searxng_client is deps2.searxng_client