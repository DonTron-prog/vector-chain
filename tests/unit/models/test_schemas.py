"""
Unit tests for Pydantic schemas and data models.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from models.schemas import (
    FinancialMetrics,
    InvestmentAnalysis, 
    InvestmentFindings,
    ResearchPlan,
    ResearchStep
)


class TestResearchStep:
    """Test ResearchStep model validation."""
    
    def test_valid_research_step(self):
        """Test creating a valid research step."""
        step = ResearchStep(
            description="Search for financial data",
            focus_area="data",
            expected_outcome="Current financial metrics"
        )
        assert step.description == "Search for financial data"
        assert step.focus_area == "data"
        assert step.expected_outcome == "Current financial metrics"
    
    def test_missing_fields(self):
        """Test validation fails with missing required fields."""
        with pytest.raises(ValidationError):
            ResearchStep(
                description="Search for data"
                # Missing focus_area and expected_outcome
            )
    
    def test_empty_description(self):
        """Test empty description is allowed."""
        step = ResearchStep(
            description="",
            focus_area="data",
            expected_outcome="Some outcome"
        )
        assert step.description == ""


class TestResearchPlan:
    """Test ResearchPlan model validation."""
    
    def test_valid_research_plan(self):
        """Test creating a valid research plan."""
        steps = [
            ResearchStep(
                description="Step 1",
                focus_area="data",
                expected_outcome="Financial data"
            ),
            ResearchStep(
                description="Step 2",
                focus_area="analysis", 
                expected_outcome="Market analysis"
            )
        ]
        plan = ResearchPlan(
            steps=steps,
            reasoning="Overall reasoning",
            priority_areas=["financial", "market"]
        )
        assert len(plan.steps) == 2
        assert plan.reasoning == "Overall reasoning"
        assert len(plan.priority_areas) == 2
    
    def test_step_count_validation(self):
        """Test step count must be between 2-4."""
        # Too few steps
        with pytest.raises(ValidationError):
            ResearchPlan(
                steps=[ResearchStep(
                    description="Only step",
                    focus_area="data",
                    expected_outcome="Some outcome"
                )],
                reasoning="Not enough steps",
                priority_areas=["test"]
            )
        
        # Too many steps
        steps = [
            ResearchStep(
                description=f"Step {i}",
                focus_area="data",
                expected_outcome=f"Outcome {i}"
            )
            for i in range(5)
        ]
        with pytest.raises(ValidationError):
            ResearchPlan(
                steps=steps,
                reasoning="Too many steps",
                priority_areas=["test"]
            )


class TestFinancialMetrics:
    """Test FinancialMetrics model validation."""
    
    def test_valid_metrics(self):
        """Test creating valid financial metrics."""
        metrics = FinancialMetrics(
            pe_ratio=25.5,
            debt_to_equity=0.3,
            return_on_equity=0.18,
            revenue_growth=0.12,
            profit_margin=0.22,
            free_cash_flow=1000000
        )
        assert metrics.pe_ratio == 25.5
        assert metrics.debt_to_equity == 0.3
        assert metrics.return_on_equity == 0.18
    
    def test_optional_fields(self):
        """Test optional fields can be None."""
        metrics = FinancialMetrics()
        assert metrics.pe_ratio is None
        assert metrics.debt_to_equity is None
        assert metrics.return_on_equity is None
    
    def test_negative_values_allowed(self):
        """Test negative values are allowed (no validation constraints)."""
        metrics = FinancialMetrics(pe_ratio=-5.0, revenue_growth=-2.0)
        assert metrics.pe_ratio == -5.0
        assert metrics.revenue_growth == -2.0


class TestInvestmentFindings:
    """Test InvestmentFindings model validation."""
    
    def test_valid_findings(self):
        """Test creating valid investment findings."""
        findings = InvestmentFindings(
            summary="Strong performance",
            key_insights=["Growth accelerating", "Market leader"],
            risk_factors=["Market volatility"],
            recommendation="BUY",
            confidence_score=0.85
        )
        assert findings.summary == "Strong performance"
        assert len(findings.key_insights) == 2
        assert len(findings.risk_factors) == 1
        assert findings.recommendation == "BUY"
        assert findings.confidence_score == 0.85
        assert isinstance(findings.financial_metrics, FinancialMetrics)
    
    def test_confidence_score_bounds(self):
        """Test confidence score must be between 0.0 and 1.0."""
        # Valid scores
        InvestmentFindings(
            summary="Test",
            key_insights=["Test"],
            risk_factors=["Test"],
            recommendation="HOLD",
            confidence_score=0.0
        )
        
        InvestmentFindings(
            summary="Test",
            key_insights=["Test"], 
            risk_factors=["Test"],
            recommendation="HOLD",
            confidence_score=1.0
        )
        
        # Invalid scores
        with pytest.raises(ValidationError):
            InvestmentFindings(
                summary="Test",
                key_insights=["Test"],
                risk_factors=["Test"], 
                recommendation="HOLD",
                confidence_score=1.5
            )
        
        with pytest.raises(ValidationError):
            InvestmentFindings(
                summary="Test",
                key_insights=["Test"],
                risk_factors=["Test"],
                recommendation="HOLD", 
                confidence_score=-0.1
            )
    
    def test_recommendation_values(self):
        """Test recommendation values (no validation constraints)."""
        findings = InvestmentFindings(
            summary="Test",
            key_insights=["Test"],
            risk_factors=["Test"],
            recommendation="MAYBE",  # Any string allowed
            confidence_score=0.5
        )
        assert findings.recommendation == "MAYBE"


class TestInvestmentAnalysis:
    """Test InvestmentAnalysis model validation."""
    
    def test_valid_analysis(self, sample_investment_findings):
        """Test creating valid investment analysis."""
        sample_plan = ResearchPlan(
            steps=[
                ResearchStep(
                    description="Test step",
                    focus_area="data",
                    expected_outcome="Test outcome"
                ),
                ResearchStep(
                    description="Test step 2",
                    focus_area="analysis",
                    expected_outcome="Test outcome 2"
                )
            ],
            reasoning="Test reasoning",
            priority_areas=["test"]
        )
        
        analysis = InvestmentAnalysis(
            query="Should I invest in AAPL?",
            context="Long-term growth",
            plan=sample_plan,
            findings=sample_investment_findings
        )
        assert analysis.query == "Should I invest in AAPL?"
        assert analysis.context == "Long-term growth"
        assert analysis.plan is not None
        assert analysis.findings is not None
        assert isinstance(analysis.created_at, datetime)
    
    def test_empty_query_allowed(self, sample_investment_findings):
        """Test empty query is allowed."""
        sample_plan = ResearchPlan(
            steps=[
                ResearchStep(description="Test", focus_area="data", expected_outcome="Test"),
                ResearchStep(description="Test 2", focus_area="analysis", expected_outcome="Test 2")
            ],
            reasoning="Test reasoning",
            priority_areas=["test"]
        )
        
        analysis = InvestmentAnalysis(
            query="",
            context="Long-term growth",
            plan=sample_plan,
            findings=sample_investment_findings
        )
        assert analysis.query == ""
    
    def test_automatic_timestamp(self, sample_investment_findings):
        """Test timestamp is automatically set."""
        sample_plan = ResearchPlan(
            steps=[
                ResearchStep(description="Test", focus_area="data", expected_outcome="Test"),
                ResearchStep(description="Test 2", focus_area="analysis", expected_outcome="Test 2")
            ],
            reasoning="Test reasoning",
            priority_areas=["test"]
        )
        
        analysis = InvestmentAnalysis(
            query="Test query",
            context="Test context",
            plan=sample_plan,
            findings=sample_investment_findings
        )
        assert analysis.created_at is not None
        assert isinstance(analysis.created_at, datetime)