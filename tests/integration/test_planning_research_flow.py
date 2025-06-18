"""
Integration tests for planning agent + research agent workflow.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from models.schemas import ResearchPlan, ResearchStep, InvestmentFindings, FinancialMetrics
from agents.dependencies import ResearchDependencies, ChromaDBClient, SearxNGClient, KnowledgeBase
from agents.planning_agent import create_research_plan, planning_agent
from agents.research_agent import conduct_research, research_agent


class TestPlanningResearchIntegration:
    """Test integration between planning and research agents."""
    
    @pytest.mark.asyncio
    async def test_complete_planning_to_research_workflow(self):
        """Test complete workflow from planning to research execution."""
        # Mock planning agent response
        plan = ResearchPlan(
            steps=[
                ResearchStep(
                    description="Analyze Apple's financial performance and fundamentals",
                    focus_area="financial_analysis",
                    expected_outcome="Understanding of revenue trends and profitability"
                ),
                ResearchStep(
                    description="Research current market sentiment and analyst opinions",
                    focus_area="market_analysis", 
                    expected_outcome="Current market perception and price targets"
                )
            ],
            reasoning="Fundamental analysis followed by market research provides comprehensive investment view",
            priority_areas=["Financial Performance", "Market Sentiment"]
        )
        
        # Mock research dependencies - using proper objects instead of Mock
        mock_deps = ResearchDependencies(
            vector_db=ChromaDBClient(),
            searxng_client=SearxNGClient(),
            knowledge_base=KnowledgeBase(),
            current_query="Should I invest in Apple for long-term growth?",
            research_context="5-year investment horizon, moderate risk tolerance",
            accumulated_findings=""
        )
        
        # Mock research agent response
        findings = InvestmentFindings(
            summary="Apple demonstrates strong fundamentals with consistent revenue growth and market leadership",
            key_insights=[
                "Revenue grew 8% YoY to $81.8B in Q3 2023",
                "Services segment shows robust 16% growth",
                "Strong balance sheet with $166B cash position"
            ],
            financial_metrics=FinancialMetrics(
                pe_ratio=28.7,
                debt_to_equity=0.31,
                profit_margin=0.24,
                return_on_equity=0.48
            ),
            risk_factors=[
                "Regulatory pressure in key markets",
                "Competition in smartphone market"
            ],
            opportunities=[
                "Growth in emerging markets",
                "Expansion of services ecosystem"
            ],
            sources=["10-K filing", "Q3 earnings report", "Analyst reports"],
            confidence_score=0.85,
            recommendation="BUY - Strong fundamentals support long-term growth thesis"
        )
        
        # Test workflow integration
        with patch.object(planning_agent, 'run') as mock_planning_run:
            with patch.object(research_agent, 'run') as mock_research_run:
                # Mock planning agent - using unit test pattern
                mock_plan_result = Mock()
                mock_plan_result.data = plan
                mock_planning_run.return_value = mock_plan_result
                
                # Mock research agent - using unit test pattern
                mock_research_result = Mock()
                mock_research_result.data = findings
                mock_research_run.return_value = mock_research_result
                
                # Execute planning phase
                created_plan = await create_research_plan(
                    "Should I invest in Apple for long-term growth?",
                    "5-year investment horizon, moderate risk tolerance"
                )
                
                # Verify plan structure
                assert isinstance(created_plan, ResearchPlan)
                assert len(created_plan.steps) == 2
                assert created_plan.steps[0].focus_area == "financial_analysis"
                assert created_plan.steps[1].focus_area == "market_analysis"
                
                # Execute research phase
                research_plan_text = f"Steps: {[step.model_dump() for step in created_plan.steps]}\nReasoning: {created_plan.reasoning}"
                
                research_findings = await conduct_research(
                    query="Should I invest in Apple for long-term growth?",
                    research_plan=research_plan_text,
                    deps=mock_deps
                )
                
                # Verify research results
                assert isinstance(research_findings, InvestmentFindings)
                assert research_findings.confidence_score == 0.85
                assert "BUY" in research_findings.recommendation
                assert len(research_findings.key_insights) == 3
                assert research_findings.financial_metrics.pe_ratio == 28.7
                
                # Verify agents were called with correct parameters
                mock_planning_run.assert_called_once()
                planning_call_args = mock_planning_run.call_args[0][0]
                assert "Should I invest in Apple" in planning_call_args
                assert "5-year investment horizon" in planning_call_args
                
                mock_research_run.assert_called_once()
                research_call_args = mock_research_run.call_args[0][0]
                assert "Should I invest in Apple" in research_call_args
                assert "financial_analysis" in research_call_args
                assert "market_analysis" in research_call_args
    
    @pytest.mark.asyncio
    async def test_plan_influences_research_focus(self):
        """Test that research plan properly influences research agent focus."""
        # Create focused valuation plan
        valuation_plan = ResearchPlan(
            steps=[
                ResearchStep(
                    description="Calculate key valuation metrics and ratios",
                    focus_area="valuation_metrics",
                    expected_outcome="P/E, P/B, DCF analysis"
                ),
                ResearchStep(
                    description="Compare valuation to historical ranges and peers",
                    focus_area="comparative_valuation",
                    expected_outcome="Relative valuation assessment"
                )
            ],
            reasoning="Focus on valuation to determine if stock is fairly priced",
            priority_areas=["Valuation Metrics", "Comparative Analysis"]
        )
        
        mock_deps = ResearchDependencies(
            vector_db=ChromaDBClient(),
            searxng_client=SearxNGClient(),
            knowledge_base=KnowledgeBase(),
            current_query="Is Apple undervalued at current prices?",
            research_context="Value investing approach",
            accumulated_findings=""
        )
        
        # Mock research findings focused on valuation
        valuation_findings = InvestmentFindings(
            summary="Apple appears fairly valued based on current metrics",
            key_insights=[
                "P/E ratio of 28.7x is near 5-year average of 27.2x",
                "Price-to-book ratio of 4.8x suggests premium valuation",
                "DCF analysis indicates fair value of $185-195 per share"
            ],
            financial_metrics=FinancialMetrics(
                pe_ratio=28.7,
                price_to_book=4.8,
                debt_to_equity=0.31
            ),
            risk_factors=["High valuation multiples limit upside"],
            opportunities=["Potential for multiple expansion with growth"],
            sources=["Financial statements", "Peer analysis"],
            confidence_score=0.78,
            recommendation="HOLD - Fairly valued with limited margin of safety"
        )
        
        with patch.object(research_agent, 'run') as mock_research_run:
            mock_research_result = Mock()
            mock_research_result.data = valuation_findings
            mock_research_run.return_value = mock_research_result
            
            # Execute research with valuation-focused plan
            research_plan_text = f"Steps: {[step.model_dump() for step in valuation_plan.steps]}\nReasoning: {valuation_plan.reasoning}"
            
            findings = await conduct_research(
                query="Is Apple undervalued at current prices?",
                research_plan=research_plan_text,
                deps=mock_deps
            )
            
            # Verify research was influenced by valuation focus
            assert "fairly valued" in findings.summary.lower()
            assert any("P/E ratio" in insight for insight in findings.key_insights)
            assert any("Price-to-book" in insight for insight in findings.key_insights)
            assert findings.financial_metrics.pe_ratio is not None
            assert findings.financial_metrics.price_to_book is not None
            assert "HOLD" in findings.recommendation
            
            # Verify research agent received valuation-focused plan
            research_call_args = mock_research_run.call_args[0][0]
            assert "valuation_metrics" in research_call_args
            assert "comparative_valuation" in research_call_args
            assert "fairly priced" in research_call_args
    
    @pytest.mark.asyncio
    async def test_growth_vs_value_research_approaches(self):
        """Test different research approaches based on plan focus."""
        
        # Growth-focused plan
        growth_plan = ResearchPlan(
            steps=[
                ResearchStep(
                    description="Analyze revenue growth trends and market expansion",
                    focus_area="growth_analysis",
                    expected_outcome="Understanding of growth trajectory"
                ),
                ResearchStep(
                    description="Evaluate innovation pipeline and competitive moats",
                    focus_area="innovation_assessment",
                    expected_outcome="Future growth driver identification"
                )
            ],
            reasoning="Growth investment requires focus on expansion and innovation",
            priority_areas=["Revenue Growth", "Innovation Pipeline"]
        )
        
        # Value-focused plan
        value_plan = ResearchPlan(
            steps=[
                ResearchStep(
                    description="Assess current valuation metrics vs intrinsic value",
                    focus_area="valuation_analysis",
                    expected_outcome="Margin of safety calculation"
                ),
                ResearchStep(
                    description="Analyze financial strength and balance sheet quality",
                    focus_area="financial_quality",
                    expected_outcome="Financial stability assessment"
                )
            ],
            reasoning="Value investment requires thorough valuation and quality analysis",
            priority_areas=["Valuation Analysis", "Financial Quality"]
        )
        
        mock_deps = ResearchDependencies(
            vector_db=ChromaDBClient(),
            searxng_client=SearxNGClient(),
            knowledge_base=KnowledgeBase(),
            current_query="Investment comparison",
            research_context="Growth vs Value analysis",
            accumulated_findings=""
        )
        
        with patch.object(research_agent, 'run') as mock_research_run:
            # Test growth-focused research
            mock_growth_result = Mock()
            mock_growth_result.data = InvestmentFindings(
                summary="Strong growth prospects with expanding addressable market",
                key_insights=["Revenue CAGR of 12% over 5 years", "TAM expansion in emerging markets"],
                financial_metrics=FinancialMetrics(revenue_growth=0.15),
                risk_factors=["Market saturation risk"],
                opportunities=["AI integration opportunities"],
                sources=["Market research"],
                confidence_score=0.82,
                recommendation="BUY - Strong growth trajectory supports premium valuation"
            )
            mock_research_run.return_value = mock_growth_result
            
            growth_plan_text = f"Steps: {[step.model_dump() for step in growth_plan.steps]}\nReasoning: {growth_plan.reasoning}"
            growth_findings = await conduct_research(
                query="Growth investment opportunity?",
                research_plan=growth_plan_text,
                deps=mock_deps
            )
            
            assert "growth" in growth_findings.summary.lower()
            assert "BUY" in growth_findings.recommendation
            
            # Test value-focused research
            mock_value_result = Mock()
            mock_value_result.data = InvestmentFindings(
                summary="Undervalued with strong balance sheet and margin of safety",
                key_insights=["Trading at 15x earnings vs 20x historical avg", "Debt-to-equity of 0.2"],
                financial_metrics=FinancialMetrics(pe_ratio=15.0, debt_to_equity=0.2),
                risk_factors=["Cyclical business model"],
                opportunities=["Multiple expansion potential"],
                sources=["Financial analysis"],
                confidence_score=0.88,
                recommendation="BUY - Significant margin of safety with quality business"
            )
            mock_research_run.return_value = mock_value_result
            
            value_plan_text = f"Steps: {[step.model_dump() for step in value_plan.steps]}\nReasoning: {value_plan.reasoning}"
            value_findings = await conduct_research(
                query="Value investment opportunity?",
                research_plan=value_plan_text,
                deps=mock_deps
            )
            
            assert "undervalued" in value_findings.summary.lower()
            assert "margin of safety" in value_findings.recommendation.lower()
            
            # Verify different research approaches were used
            assert mock_research_run.call_count == 2
            growth_call = mock_research_run.call_args_list[0][0][0]
            value_call = mock_research_run.call_args_list[1][0][0]
            
            assert "growth_analysis" in growth_call
            assert "innovation_assessment" in growth_call
            assert "valuation_analysis" in value_call
            assert "financial_quality" in value_call


class TestResearchDependenciesIntegration:
    """Test research dependencies integration with agents."""
    
    @pytest.mark.asyncio
    async def test_dependencies_properly_initialized(self):
        """Test that research dependencies are properly initialized and passed."""
        from agents.dependencies import initialize_dependencies
        
        # Test dependency initialization
        deps = initialize_dependencies(
            query="Test investment query",
            context="Test context",
            searxng_url="http://test:8080",
            chroma_path="./test_chroma",
            knowledge_path="./test_knowledge"
        )
        
        assert isinstance(deps, ResearchDependencies)
        assert deps.current_query == "Test investment query"
        assert deps.research_context == "Test context"
        assert isinstance(deps.vector_db, ChromaDBClient)
        assert isinstance(deps.searxng_client, SearxNGClient)
        assert isinstance(deps.knowledge_base, KnowledgeBase)
        assert deps.searxng_client.base_url == "http://test:8080"
    
    @pytest.mark.asyncio 
    async def test_dependencies_shared_across_research_calls(self):
        """Test that dependencies maintain state across research tool calls."""
        mock_deps = ResearchDependencies(
            vector_db=ChromaDBClient(),
            searxng_client=SearxNGClient(),
            knowledge_base=KnowledgeBase(),
            current_query="Apple investment analysis",
            research_context="Long-term growth focus",
            accumulated_findings=""
        )
        
        # Mock the research agent with dependency tracking
        with patch.object(research_agent, 'run') as mock_research_run:
            # Mock multiple tool calls that should share dependencies
            def mock_run_with_deps(prompt, deps=None):
                # Verify dependencies are passed correctly
                assert deps == mock_deps
                assert deps.current_query == "Apple investment analysis"
                assert deps.research_context == "Long-term growth focus"
                
                # Simulate tool usage that modifies accumulated findings
                deps.accumulated_findings += "Financial data gathered. "
                
                mock_result = Mock()
                mock_result.data = InvestmentFindings(
                    summary="Analysis based on accumulated research",
                    key_insights=["Insight from shared context"],
                    financial_metrics=FinancialMetrics(),
                    risk_factors=[],
                    opportunities=[],
                    sources=[],
                    confidence_score=0.8,
                    recommendation="Based on shared dependency context"
                )
                return mock_result
            
            mock_research_run.side_effect = mock_run_with_deps
            
            # Execute research that should use shared dependencies
            findings = await conduct_research(
                query="Apple investment analysis",
                research_plan="Test plan for dependency sharing",
                deps=mock_deps
            )
            
            # Verify dependencies were used and modified
            assert mock_deps.accumulated_findings == "Financial data gathered. "
            assert "shared dependency context" in findings.recommendation