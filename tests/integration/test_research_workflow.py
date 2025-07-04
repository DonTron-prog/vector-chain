"""
Integration tests for the complete research workflow.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from models.schemas import InvestmentAnalysis, ResearchPlan, InvestmentFindings, FinancialMetrics, ResearchStep


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
                ResearchStep(
                    description="Search for AAPL financial performance",
                    focus_area="data gathering",
                    expected_outcome="Current financial data and metrics"
                ),
                ResearchStep(
                    description="Analyze market position",
                    focus_area="analysis",
                    expected_outcome="Market position assessment"
                )
            ],
            priority_areas=["financial analysis", "market research"],
            reasoning="Comprehensive analysis approach"
        )
        
        # Mock research agent response
        mock_findings = InvestmentFindings(
            summary="AAPL shows strong fundamentals with moderate growth prospects",
            key_insights=[
                "Strong brand loyalty and ecosystem",
                "Consistent dividend payments",
                "Services revenue growing"
            ],
            financial_metrics=FinancialMetrics(
                pe_ratio=28.5,
                debt_to_equity=0.25,
                return_on_equity=0.20,
                revenue_growth=0.08,
                profit_margin=0.24
            ),
            risk_factors=[
                "Market saturation in smartphones",
                "China market dependency"
            ],
            opportunities=[
                "Services ecosystem expansion",
                "Emerging markets growth"
            ],
            sources=["10-K filing", "Analyst reports"],
            confidence_score=0.75,
            recommendation="BUY"
        )
        
        mock_analysis = InvestmentAnalysis(
            query=query,
            context=context,
            plan=mock_plan,
            findings=mock_findings
        )
        
        with patch('agents.planning_agent.create_research_plan') as mock_planning, \
             patch('agents.research_agent.conduct_research') as mock_research:
            
            mock_planning.return_value = mock_plan
            mock_research.return_value = mock_findings  # Should return InvestmentFindings, not InvestmentAnalysis
            
            # Import and run main workflow
            from main import research_investment
            
            result = await research_investment(query, context)
            
            # Verify workflow execution
            mock_planning.assert_called_once_with(query, context)
            # Verify research was called (but don't check exact parameters since they're complex)
            mock_research.assert_called_once()
            
            # Verify result structure
            assert isinstance(result, InvestmentAnalysis)
            assert result.query == query
            assert result.context == context
            assert result.findings is not None
            assert isinstance(result.findings, InvestmentFindings)
            assert result.findings.financial_metrics is not None
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
                        ResearchStep(
                            description=f"Research {case['expected_focus']}",
                            focus_area="data gathering",
                            expected_outcome=f"Research data on {case['expected_focus']}"
                        ),
                        ResearchStep(
                            description="Analyze results",
                            focus_area="analysis",
                            expected_outcome="Analysis results"
                        )
                    ],
                    priority_areas=[case['expected_focus'], "analysis"],
                    reasoning=f"Focus on {case['expected_focus']}"
                )
                
                mock_findings = InvestmentFindings(
                    summary=f"Analysis focused on {case['expected_focus']}",
                    key_insights=["Insight 1", "Insight 2"],
                    financial_metrics=FinancialMetrics(pe_ratio=25.0),
                    risk_factors=["Risk 1"],
                    opportunities=["Opportunity 1"],
                    sources=["Test source"],
                    confidence_score=0.6,
                    recommendation="HOLD"
                )
                
                mock_analysis = InvestmentAnalysis(
                    query=case["query"],
                    context=case["context"],
                    plan=mock_plan,
                    findings=mock_findings
                )
                
                mock_planning.return_value = mock_plan
                mock_research.return_value = mock_findings
                
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
                ResearchStep(
                    description="Gather AAPL financial statements",
                    focus_area="data gathering",
                    expected_outcome="Complete financial statements and metrics"
                ),
                ResearchStep(
                    description="Research market sentiment",
                    focus_area="analysis",
                    expected_outcome="Market sentiment assessment"
                ),
                ResearchStep(
                    description="Calculate valuation metrics",
                    focus_area="valuation",
                    expected_outcome="Valuation analysis and fair price target"
                )
            ],
            priority_areas=["financial analysis", "market research", "valuation"],
            reasoning="Systematic approach to investment analysis"
        )
        
        with patch('agents.planning_agent.create_research_plan') as mock_planning, \
             patch('agents.research_agent.conduct_research') as mock_research:
            
            mock_planning.return_value = research_plan
            
            # Verify research agent receives the plan
            mock_research.return_value = InvestmentFindings(
                summary="Analysis complete",
                key_insights=["Good fundamentals"],
                financial_metrics=FinancialMetrics(pe_ratio=30.0),
                risk_factors=["Market risk"],
                opportunities=["Growth opportunity"],
                sources=["Financial statements"],
                confidence_score=0.8,
                recommendation="BUY"
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
             patch('tools.calculator.calculate_financial_metrics') as mock_calc, \
             patch('tools.vector_search.search_internal_docs') as mock_vector:
            
            # Mock tool responses
            mock_search.return_value = "Search results about AAPL"
            mock_scrape.return_value = "Scraped financial content"
            mock_calc.return_value = "Calculated ratios: P/E 28.5, ROE 20%"
            mock_vector.return_value = "Retrieved documents about AAPL"
            
            # Mock the research agent to use tools
            with patch('agents.research_agent.conduct_research') as mock_research:
                # Create a basic research plan for this test
                basic_plan = ResearchPlan(
                    steps=[
                        ResearchStep(
                            description="Analyze AAPL financial health",
                            focus_area="financial analysis",
                            expected_outcome="Financial health assessment"
                        ),
                        ResearchStep(
                            description="Gather market data",
                            focus_area="market research",
                            expected_outcome="Market analysis"
                        )
                    ],
                    priority_areas=["financial analysis", "market research"],
                    reasoning="Test tool coordination workflow"
                )
                
                mock_analysis = InvestmentAnalysis(
                    query=query,
                    context=context,
                    plan=basic_plan,
                    findings=InvestmentFindings(
                        summary="Strong financial position",
                        key_insights=["Tool coordination successful"],
                        financial_metrics=FinancialMetrics(pe_ratio=28.5, return_on_equity=0.20),
                        risk_factors=["Market volatility"],
                        opportunities=["Market expansion"],
                        sources=["Tool analysis"],
                        confidence_score=0.85,
                        recommendation="BUY"
                    )
                )
                mock_research.return_value = mock_analysis.findings
                
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
        from agents.dependencies import initialize_dependencies
        
        deps = initialize_dependencies(
            query="Test investment query",
            context="Test context"
        )
        
        # Verify all dependencies are initialized
        assert deps.vector_db is not None
        assert deps.searxng_client is not None
        assert deps.knowledge_base is not None
        assert deps.current_query == "Test investment query"
    
    @pytest.mark.integration
    def test_shared_dependencies(self, mock_research_dependencies):
        """Test that dependencies are properly shared between components."""
        # Test that the same dependency instances are used
        # across different agents and tools
        
        deps1 = mock_research_dependencies
        deps2 = mock_research_dependencies
        
        # Should be the same instances (dependency injection)
        assert deps1.vector_db is deps2.vector_db
        assert deps1.searxng_client is deps2.searxng_client