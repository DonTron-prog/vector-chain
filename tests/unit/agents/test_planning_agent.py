"""
Unit tests for planning agent.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from models.schemas import ResearchPlan, ResearchStep
from agents.planning_agent import create_research_plan, planning_agent


class TestPlanningAgent:
    """Test planning agent functionality."""
    
    @pytest.mark.asyncio
    async def test_create_basic_research_plan(self):
        """Test creating a basic research plan."""
        print("DEBUG: Creating ResearchPlan mock - checking required fields")
        try:
            mock_result = Mock()
            mock_result.data = ResearchPlan(
                steps=[
                    ResearchStep(
                        description="Analyze company fundamentals and recent financial performance",
                        focus_area="financial_analysis",
                        expected_outcome="Understanding of revenue trends, profitability, and key metrics"
                    ),
                    ResearchStep(
                        description="Evaluate competitive position and market dynamics",
                        focus_area="market_analysis",
                        expected_outcome="Assessment of competitive advantages and market share"
                    )
                ],
                reasoning="This plan focuses on fundamental analysis followed by competitive positioning to provide a comprehensive investment assessment.",
                priority_areas=["financial_analysis", "market_analysis"]  # DEBUG: Adding missing required field
            )
            print("DEBUG: ResearchPlan created successfully with priority_areas")
        except Exception as e:
            print(f"DEBUG: ResearchPlan creation failed: {e}")
            raise
        
        with patch.object(planning_agent, 'run', return_value=mock_result) as mock_run:
            plan = await create_research_plan(
                "Should I invest in AAPL for long-term growth?",
                "Looking for 5-year investment horizon"
            )
            
            assert isinstance(plan, ResearchPlan)
            assert len(plan.steps) == 2
            assert plan.steps[0].focus_area == "financial_analysis"
            assert plan.steps[1].focus_area == "market_analysis"
            assert "fundamental analysis" in plan.reasoning
            
            # Verify agent was called with correct prompt
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "Should I invest in AAPL" in call_args
            assert "5-year investment horizon" in call_args
    
    @pytest.mark.asyncio
    async def test_create_plan_with_no_context(self):
        """Test creating plan without additional context."""
        mock_result = Mock()
        mock_result.data = ResearchPlan(
            steps=[
                ResearchStep(
                    description="Research company financial performance",
                    focus_area="fundamentals",
                    expected_outcome="Financial health assessment"
                ),
                ResearchStep(
                    description="Analyze market position and competition",
                    focus_area="analysis",
                    expected_outcome="Competitive landscape understanding"
                )
            ],
            reasoning="Basic financial analysis approach.",
            priority_areas=["Financial Performance", "Market Position"]
        )
        
        with patch.object(planning_agent, 'run', return_value=mock_result):
            plan = await create_research_plan("Is MSFT a good investment?")
            
            assert len(plan.steps) == 2
            assert "financial performance" in plan.steps[0].description
    
    @pytest.mark.asyncio
    async def test_create_plan_value_investment_query(self):
        """Test plan creation for value investment query."""
        mock_result = Mock()
        mock_result.data = ResearchPlan(
            steps=[
                ResearchStep(
                    description="Analyze current valuation metrics and compare to historical ranges",
                    focus_area="valuation_analysis",
                    expected_outcome="Determination if stock is undervalued relative to intrinsic value"
                ),
                ResearchStep(
                    description="Examine financial strength and balance sheet quality",
                    focus_area="financial_health",
                    expected_outcome="Assessment of financial stability and debt levels"
                ),
                ResearchStep(
                    description="Investigate business model sustainability and competitive moats",
                    focus_area="business_quality",
                    expected_outcome="Understanding of long-term competitive advantages"
                )
            ],
            reasoning="Value investment approach requires thorough valuation analysis, financial health check, and business quality assessment.",
            priority_areas=["Valuation Analysis", "Financial Health", "Business Quality"]
        )
        
        with patch.object(planning_agent, 'run', return_value=mock_result):
            plan = await create_research_plan(
                "Is Apple undervalued and worth buying for value investing?",
                "Value investor with focus on margin of safety and long-term holdings"
            )
            
            assert len(plan.steps) == 3
            assert any("valuation" in step.focus_area for step in plan.steps)
            assert any("financial_health" in step.focus_area for step in plan.steps)
            assert any("business_quality" in step.focus_area for step in plan.steps)
            assert "margin of safety" in plan.reasoning or "Value investment" in plan.reasoning
    
    @pytest.mark.asyncio 
    async def test_create_plan_growth_investment_query(self):
        """Test plan creation for growth investment query."""
        mock_result = Mock()
        mock_result.data = ResearchPlan(
            steps=[
                ResearchStep(
                    description="Analyze revenue growth trends and market expansion opportunities",
                    focus_area="growth_analysis",
                    expected_outcome="Understanding of historical and projected growth rates"
                ),
                ResearchStep(
                    description="Evaluate innovation pipeline and R&D investments",
                    focus_area="innovation_assessment",
                    expected_outcome="Assessment of future growth drivers and competitive positioning"
                ),
                ResearchStep(
                    description="Examine market size and addressable opportunities",
                    focus_area="market_opportunity",
                    expected_outcome="Evaluation of total addressable market and expansion potential"
                )
            ],
            reasoning="Growth investment strategy requires focus on revenue expansion, innovation capabilities, and market opportunities.",
            priority_areas=["Growth Analysis", "Innovation Assessment", "Market Opportunity"]
        )
        
        with patch.object(planning_agent, 'run', return_value=mock_result):
            plan = await create_research_plan(
                "Should I buy Microsoft for growth potential?",
                "Growth investor looking for 20%+ annual returns over next 3 years"
            )
            
            assert len(plan.steps) == 3
            assert any("growth" in step.focus_area for step in plan.steps)
            assert any("innovation" in step.focus_area for step in plan.steps)
            assert any("market" in step.focus_area for step in plan.steps)
    
    @pytest.mark.asyncio
    async def test_create_plan_risk_assessment_focus(self):
        """Test plan creation with risk assessment focus."""
        mock_result = Mock()
        mock_result.data = ResearchPlan(
            steps=[
                ResearchStep(
                    description="Identify key business and operational risks",
                    focus_area="risk_identification",
                    expected_outcome="Comprehensive list of potential threats to business performance"
                ),
                ResearchStep(
                    description="Analyze financial risks including debt levels and cash flow stability",
                    focus_area="financial_risk",
                    expected_outcome="Assessment of financial stability and liquidity risks"
                ),
                ResearchStep(
                    description="Evaluate market and competitive risks",
                    focus_area="market_risk",
                    expected_outcome="Understanding of external threats and competitive pressures"
                ),
                ResearchStep(
                    description="Determine risk-adjusted return potential",
                    focus_area="risk_return_analysis",
                    expected_outcome="Investment recommendation based on risk-return profile"
                )
            ],
            reasoning="Conservative investment approach requires comprehensive risk assessment across business, financial, and market dimensions.",
            priority_areas=["Risk Identification", "Financial Risk", "Market Risk", "Risk-Return Analysis"]
        )
        
        with patch.object(planning_agent, 'run', return_value=mock_result):
            plan = await create_research_plan(
                "What are the main risks of investing in Apple?",
                "Conservative investor concerned about downside protection"
            )
            
            assert len(plan.steps) == 4
            assert any("risk" in step.focus_area for step in plan.steps)
            assert "risk assessment" in plan.reasoning.lower()


class TestPlanningAgentEdgeCases:
    """Test edge cases and error scenarios."""
    
    @pytest.mark.asyncio
    async def test_create_plan_agent_error(self):
        """Test handling of agent execution errors."""
        with patch.object(planning_agent, 'run', side_effect=Exception("AI model unavailable")):
            with pytest.raises(Exception) as exc_info:
                await create_research_plan("Test query")
            
            assert "AI model unavailable" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_plan_empty_query(self):
        """Test plan creation with empty query."""
        mock_result = Mock()
        mock_result.data = ResearchPlan(
            steps=[
                ResearchStep(
                    description="Please provide a specific investment question",
                    focus_area="clarification_needed",
                    expected_outcome="Clear investment objective"
                ),
                ResearchStep(
                    description="Conduct general market analysis",
                    focus_area="market_overview",
                    expected_outcome="Market context and opportunities"
                )
            ],
            reasoning="Query lacks specific investment focus.",
            priority_areas=["Clarification", "Market Overview"]
        )
        
        with patch.object(planning_agent, 'run', return_value=mock_result):
            plan = await create_research_plan("")
            
            assert len(plan.steps) >= 1
            assert "clarification" in plan.steps[0].focus_area.lower()
    
    @pytest.mark.asyncio
    async def test_create_plan_complex_multi_stock_query(self):
        """Test plan creation for complex multi-stock comparison."""
        mock_result = Mock()
        mock_result.data = ResearchPlan(
            steps=[
                ResearchStep(
                    description="Analyze financial performance of Apple Inc",
                    focus_area="aapl_analysis",
                    expected_outcome="Understanding of Apple's financial health and growth prospects"
                ),
                ResearchStep(
                    description="Analyze financial performance of Microsoft Corp",
                    focus_area="msft_analysis",
                    expected_outcome="Understanding of Microsoft's financial health and growth prospects"
                ),
                ResearchStep(
                    description="Compare valuation metrics and competitive positioning",
                    focus_area="comparative_analysis",
                    expected_outcome="Relative assessment of investment attractiveness"
                ),
                ResearchStep(
                    description="Make investment recommendation based on risk-return profiles",
                    focus_area="investment_decision",
                    expected_outcome="Clear recommendation on which stock to prioritize"
                )
            ],
            reasoning="Multi-stock comparison requires individual analysis of each company followed by comparative assessment to determine the superior investment opportunity.",
            priority_areas=["AAPL Analysis", "MSFT Analysis", "Comparative Analysis", "Investment Decision"]
        )
        
        with patch.object(planning_agent, 'run', return_value=mock_result):
            plan = await create_research_plan(
                "Should I invest in Apple or Microsoft for the best returns?",
                "Looking to invest $10,000 in one of these tech giants"
            )
            
            assert len(plan.steps) == 4
            assert any("aapl" in step.focus_area.lower() for step in plan.steps)
            assert any("msft" in step.focus_area.lower() for step in plan.steps)
            assert any("comparative" in step.focus_area.lower() for step in plan.steps)


class TestPlanningAgentIntegration:
    """Integration tests for planning agent."""
    
    @pytest.mark.asyncio
    async def test_realistic_investment_planning_workflow(self):
        """Test realistic investment planning workflow."""
        # Simulate realistic planning agent response
        mock_result = Mock()
        mock_result.data = ResearchPlan(
            steps=[
                ResearchStep(
                    description="Gather and analyze Apple's recent financial statements including 10-K, 10-Q, and earnings reports",
                    focus_area="fundamental_analysis",
                    expected_outcome="Clear picture of Apple's revenue trends, profitability, and balance sheet strength"
                ),
                ResearchStep(
                    description="Research current market conditions, analyst opinions, and recent news affecting Apple",
                    focus_area="market_sentiment",
                    expected_outcome="Understanding of market perception and external factors impacting stock price"
                ),
                ResearchStep(
                    description="Calculate and compare key valuation metrics (P/E, P/S, PEG) against historical ranges and peers",
                    focus_area="valuation_assessment",
                    expected_outcome="Determination of whether Apple is fairly valued, undervalued, or overvalued"
                ),
                ResearchStep(
                    description="Formulate investment recommendation considering long-term growth prospects and risk factors",
                    focus_area="investment_recommendation",
                    expected_outcome="Clear buy/hold/sell recommendation with supporting rationale"
                )
            ],
            reasoning="This comprehensive approach combines fundamental analysis with market research and valuation assessment to provide a well-rounded investment recommendation for Apple stock based on the client's long-term growth objectives.",
            priority_areas=["Fundamental Analysis", "Market Sentiment", "Valuation Assessment", "Investment Recommendation"]
        )
        
        with patch.object(planning_agent, 'run', return_value=mock_result):
            plan = await create_research_plan(
                "Should I invest in Apple stock for long-term growth?",
                "I'm looking for investments that can grow 10-15% annually over 5+ years. I have moderate risk tolerance and prefer established companies."
            )
            
            # Verify plan structure
            assert isinstance(plan, ResearchPlan)
            assert len(plan.steps) == 4
            
            # Verify logical flow of steps
            step_areas = [step.focus_area for step in plan.steps]
            assert "fundamental_analysis" in step_areas
            assert "market_sentiment" in step_areas  
            assert "valuation_assessment" in step_areas
            assert "investment_recommendation" in step_areas
            
            # Verify comprehensive reasoning
            assert len(plan.reasoning) > 50  # Should be substantial
            assert "comprehensive" in plan.reasoning.lower()
            assert "apple" in plan.reasoning.lower()
            
            # Verify each step has proper structure
            for step in plan.steps:
                assert len(step.description) > 20  # Detailed descriptions
                assert len(step.expected_outcome) > 15  # Clear outcomes
                assert step.focus_area  # Non-empty focus area
    
    @pytest.mark.asyncio
    async def test_plan_prompting_format(self):
        """Test that the planning agent receives properly formatted prompts."""
        with patch.object(planning_agent, 'run') as mock_run:
            mock_result = Mock()
            mock_result.data = ResearchPlan(
                steps=[
                    ResearchStep(
                        description="Basic research step",
                        focus_area="test",
                        expected_outcome="Test outcome"
                    ),
                    ResearchStep(
                        description="Second research step",
                        focus_area="test",
                        expected_outcome="Test outcome 2"
                    )
                ],
                reasoning="test",
                priority_areas=["Test Area"]
            )
            mock_run.return_value = mock_result
            
            await create_research_plan(
                "Test investment query",
                "Test context information"
            )
            
            # Verify prompt format
            call_args = mock_run.call_args[0][0]
            assert "Investment Query: Test investment query" in call_args
            assert "Context: Test context information" in call_args
            assert "Create a research plan" in call_args