from typing import TypedDict, Annotated, List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field
from datetime import datetime
from src.graph.reducers import append_reducer, extend_reducer


class AnalysisRequest(BaseModel):
    ticker: str
    company_name: str
    country: str = "US"  
    time_range: str
    required_analyses: List[Literal["fundamental", "sentiment", "quant"]] 
    specific_questions: List[str] = []

class Task(BaseModel):
    agent: Literal["fundamental_analyst", "sentiment_analyst", "quant_coder"]
    instructions: str

class ExecutionPlan(BaseModel):
    rationale: str
    tasks: List[Task]
    parallel_execution: bool = True

class FundamentalReport(BaseModel):
    revenue_trend: str = Field(description="IN-DEPTH PARAGRAPH: Analyze the revenue growth, comparable sales, and core drivers. Minimum 3 sentences.")
    eps_analysis: str = Field(description="IN-DEPTH PARAGRAPH: Detailed breakdown of EPS performance, guidance, and future expectations. Minimum 3 sentences.")
    margin_health: str = Field(description="IN-DEPTH PARAGRAPH: Analyze gross and operating margins, inventory management, and pricing power.")
    debt_profile: str = Field(description="IN-DEPTH PARAGRAPH: Evaluate the balance sheet, debt-to-equity, and free cash flow generation.")
    key_risks: List[str] = Field(description="List of 4-5 highly specific, company-related risks (e.g., specific tariffs, specific competitors).")
    macro_context_summary: str = Field(description="Explain exactly how the current Fed rates and inflation affect this specific company's bottom line.")
    macro_impact_score: int = Field(default=50, ge=0, le=100)
    sec_filing_summary: Optional[str] = Field(default=None, description="IN-DEPTH PARAGRAPH: Summarize the CFO's commentary, insider trading, and risk factors explicitly stated in the SEC filing.")
    fundamental_score: int = Field(ge=0, le=100)
    data_sources: List[str]
    status: Literal["COMPLETE", "FAILED", "PARTIAL"]


class SegmentSentiment(BaseModel):
    segment: str = Field(description="Business unit, e.g., 'Consumer Banking', 'Investment Banking', 'Asset Management'")
    score: float = Field(description="Sentiment score from -1.0 to 1.0")
    narrative: str = Field(description="2-3 sentence deep-dive into this specific segment's current momentum.")

class SentimentReport(BaseModel):
    overall_sentiment: str
    sentiment_score: float
    segment_breakdown: List[SegmentSentiment] = Field(default_factory=list)
    detected_contradictions: List[str] = Field(description="List any discrepancies found between management quotes and independent news.")
    source_reliability_map: Dict[str, float] = Field(description="Weight assigned to each major source used (0.0 to 1.0).")
    top_news_narratives: List[str]
    geopolitical_risk_level: str
    analyst_consensus: str
    status: str

class TechnicalSummary(BaseModel):
    trend: str = Field(description="BULLISH, BEARISH, or NEUTRAL.")
    sma_signal: str = Field(description="IN-DEPTH PARAGRAPH: Analyze the current price action relative to the 50-day and 200-day SMAs.")
    rsi_signal: str = Field(description="IN-DEPTH PARAGRAPH: Analyze the 14-day RSI. Is it overbought (>70) or oversold (<30)?")
    volume_trend: str = Field(description="IN-DEPTH PARAGRAPH: Analyze the trading volume. Are up-days on high volume?")

class CodeReviewResult(BaseModel):
    code_version: int
    ast_check_passed: bool
    bandit_check_passed: bool
    llm_review_verdict: Literal["APPROVED", "APPROVED_WITH_WARNING", "REJECTED_WITH_FEEDBACK"]
    llm_review_feedback: str

class QuantReport(BaseModel):
    chart_paths: List[str]
    technical_summary: TechnicalSummary
    iterations: int
    status: Literal["COMPLETE", "FAILED"]

class RiskReport(BaseModel):
    contradiction_score: float = Field(ge=0.0, le=1.0)
    primary_contradiction: Optional[str]
    risk_factors: List[str]
    overall_risk_level: Literal["LOW", "MEDIUM", "MEDIUM-HIGH", "HIGH", "CRITICAL"]
    bear_bull_classification: Literal["STRONG_BULL", "BULL", "NEUTRAL", "BEAR", "STRONG_BEAR"]

class ReResearchRequest(BaseModel):
    target_agent: Literal["fundamental_agent", "sentiment_agent", "quant_agent"]
    specific_question: str
    reason: str

class PipelineError(BaseModel):
    agent: str
    error_type: str
    error_message: str
    timestamp: str

# --- The Master LangGraph State Dictionary ---

class OverallState(TypedDict):
    # Intake & Routing
    raw_query: str
    analysis_request: Optional[AnalysisRequest]
    
    # Orchestration
    execution_plan: Optional[ExecutionPlan]
    supervisor_iteration_count: int
    
    # Worker Outputs (Last-Write-Wins)
    fundamental_report: Optional[FundamentalReport]
    sentiment_report: Optional[SentimentReport]
    quant_report: Optional[QuantReport]
    
    # Risk & Validation
    risk_report: Optional[RiskReport]
    
    # Synthesis & Reflection
    synthesis_draft: Optional[str]
    synthesis_critique: Optional[str]
    synthesis_final: Optional[str]
    synthesis_confidence_score: Optional[int]
    synthesis_iteration_count: int
    re_research_request: Optional[ReResearchRequest]
    
    # Final Compilation
    final_report_markdown: Optional[str]
    chart_file_paths: List[str]
    
    # Human-In-The-Loop
    hitl_decision: Optional[Literal["APPROVE", "DEEPEN_RESEARCH", "ABORT"]]
    hitl_deepening_instructions: Optional[str]
    
    # Auditing
    pipeline_errors: Annotated[List[PipelineError], append_reducer]
    pipeline_status: Literal["RUNNING", "AWAITING_HITL", "COMPLETE", "FAILED", "ABORTED"]