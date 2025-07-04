"""Clean Pydantic schemas for investment research."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class ResearchStep(BaseModel):
    """Individual research step."""
    description: str = Field(..., description="What this step accomplishes")
    focus_area: str = Field(..., description="The main focus area (data, analysis, valuation, etc.)")
    expected_outcome: str = Field(..., description="What we expect to learn from this step")


class ResearchPlan(BaseModel):
    """Investment research plan with structured steps."""
    steps: List[ResearchStep] = Field(..., description="2-4 logical research steps", min_length=2, max_length=4)
    reasoning: str = Field(..., description="Explanation of the planning approach")
    priority_areas: List[str] = Field(..., description="Key areas to focus research on")


class FinancialMetrics(BaseModel):
    """Financial metrics and ratios."""
    pe_ratio: Optional[float] = None
    price_to_book: Optional[float] = None  
    debt_to_equity: Optional[float] = None
    return_on_equity: Optional[float] = None
    profit_margin: Optional[float] = None
    revenue_growth: Optional[float] = None
    free_cash_flow: Optional[float] = None


class InvestmentFindings(BaseModel):
    """Complete investment research findings."""
    summary: str = Field(..., description="Executive summary of findings")
    key_insights: List[str] = Field(..., description="Key insights discovered")
    financial_metrics: FinancialMetrics = Field(default_factory=FinancialMetrics)
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    opportunities: List[str] = Field(default_factory=list, description="Growth opportunities")
    sources: List[str] = Field(default_factory=list, description="Information sources used")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in findings (0-1)")
    recommendation: str = Field(..., description="Investment recommendation")


class InvestmentAnalysis(BaseModel):
    """Complete investment analysis result."""
    query: str = Field(..., description="Original investment query")
    context: str = Field(default="", description="Research context provided")
    plan: ResearchPlan = Field(..., description="Research plan used")
    findings: InvestmentFindings = Field(..., description="Research findings")
    created_at: datetime = Field(default_factory=datetime.now)
    success: bool = Field(default=True, description="Whether analysis completed successfully")


class WebSearchResult(BaseModel):
    """Web search result item."""
    url: str
    title: str
    content: Optional[str] = None
    published_date: Optional[str] = None


class DocumentMetadata(BaseModel):
    """Enhanced document metadata."""
    company: str
    doc_type: str
    date: Optional[str] = None
    section: Optional[str] = None
    page_number: Optional[int] = None
    file_path: Optional[str] = None


class DocumentSearchResult(BaseModel):
    """Enhanced document search result from vector DB."""
    content: str
    metadata: DocumentMetadata
    score: float = Field(ge=0.0, le=1.0, description="Relevance score between 0 and 1")
    chunk_id: Optional[str] = None
    
    @property
    def relevance_level(self) -> str:
        """Human-readable relevance level."""
        if self.score >= 0.9: 
            return "Highly Relevant"
        elif self.score >= 0.7: 
            return "Relevant"
        elif self.score >= 0.5: 
            return "Somewhat Relevant"
        else: 
            return "Low Relevance"


class RAGMetrics(BaseModel):
    """RAG retrieval metrics for performance tracking."""
    query: str
    num_results: int
    avg_relevance_score: float
    top_score: float
    retrieval_time_ms: float
    enhanced_query: Optional[str] = None


class ExecutionFeedback(BaseModel):
    """Feedback from research agent execution to planning agent."""
    step_completed: str = Field(..., description="Description of completed research step")
    findings_quality: float = Field(..., ge=0.0, le=1.0, description="Quality of findings (0-1)")
    data_gaps: List[str] = Field(default_factory=list, description="Identified data gaps or missing information")
    unexpected_findings: List[str] = Field(default_factory=list, description="Unexpected discoveries during research")
    suggested_adjustments: List[str] = Field(default_factory=list, description="Suggested plan modifications")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Confidence in current research direction")
    next_step_recommendation: Optional[str] = None


class PlanUpdateRequest(BaseModel):
    """Request to update research plan based on execution feedback."""
    current_step: int = Field(..., description="Current step number being executed")
    feedback: ExecutionFeedback = Field(..., description="Feedback from research execution")
    remaining_steps: List[ResearchStep] = Field(..., description="Remaining steps in current plan")


class PlanUpdateResponse(BaseModel):
    """Response from planning agent with updated plan."""
    should_update: bool = Field(..., description="Whether plan needs updating")
    updated_steps: Optional[List[ResearchStep]] = None
    reasoning: str = Field(..., description="Reasoning for update decision")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in updated plan")


class AdaptivePlan(BaseModel):
    """Research plan that evolves based on execution feedback."""
    original_plan: ResearchPlan = Field(..., description="Original research plan")
    current_steps: List[ResearchStep] = Field(..., description="Current active steps")
    completed_steps: List[ResearchStep] = Field(default_factory=list, description="Successfully completed steps")
    adaptation_history: List[str] = Field(default_factory=list, description="History of plan adaptations")
    total_adaptations: int = Field(default=0, description="Number of plan adaptations made")
    current_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Current confidence in plan")