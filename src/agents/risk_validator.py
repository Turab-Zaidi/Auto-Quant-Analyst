from langchain_core.prompts import ChatPromptTemplate
import json

from src.graph.state import OverallState, RiskReport
from src.llm.nvidia_nim_client import get_llm
from src.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the Chief Risk Officer at a top-tier hedge fund.
Your job is to review the findings from your three analysts (Fundamental, Sentiment, and Quant) and identify CONTRADICTIONS and RISKS.

INSTRUCTIONS:
1. Compare the Fundamental Score, Sentiment Verdict, and Technical Trend.
2. contradiction_score: 0.0 means all analysts agree perfectly. 1.0 means complete contradiction (e.g., Fundamentals say Strong Buy, Sentiment says Panic Sell).
3. primary_contradiction: Briefly describe the biggest disagreement between the analysts. If none, say "None".
4. risk_factors: List 3-4 major risks identified across all reports.
5. overall_risk_level: "LOW", "MEDIUM", "MEDIUM-HIGH", "HIGH", or "CRITICAL".
6. bear_bull_classification: Your final aggregated verdict based on all data.

Be deeply skeptical. If the price is bullish but fundamentals are deteriorating, flag that as a major contradiction."""

def risk_node(state: OverallState) -> dict:
    logger.info("--- RISK VALIDATOR: Analyzing Cross-Worker Contradictions ---")
    
    # Safely extract the reports from the state, handling missing/skipped agents
    fund = state.get("fundamental_report")
    sent = state.get("sentiment_report")
    quant = state.get("quant_report")
    
    # We only want to analyze what actually completed
    inputs_to_analyze = {}
    if fund and fund.status == "COMPLETE":
        inputs_to_analyze["Fundamental"] = fund.model_dump()
    if sent and sent.status == "COMPLETE":
        inputs_to_analyze["Sentiment"] = sent.model_dump()
    if quant and quant.status == "COMPLETE":
        inputs_to_analyze["Quant"] = quant.model_dump()

    if not inputs_to_analyze:
        logger.error("Risk Validator found no completed reports to analyze.")
        return {
            "risk_report": RiskReport(
                contradiction_score=0.0, primary_contradiction="No data.",
                risk_factors=["Analysis failure"], overall_risk_level="CRITICAL",
                bear_bull_classification="NEUTRAL"
            )
        }

    llm = get_llm(tier="smart", temperature=0.0) # Low temperature for logical consistency
    structured_llm = llm.with_structured_output(RiskReport)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "Analyst Reports:\n{reports}\n\nGenerate the RiskReport.")
    ])
    
    chain = prompt | structured_llm
    
    try:
        report = chain.invoke({
            "reports": json.dumps(inputs_to_analyze, indent=2)
        })
        
        logger.info(f"Risk Validation Complete. Contradiction Score: {report.contradiction_score}")
        return {"risk_report": report}
        
    except Exception as e:
        logger.error(f"Risk Validator failed: {e}")
        return {
            "risk_report": RiskReport(
                contradiction_score=0.0, primary_contradiction="Error in analysis.",
                risk_factors=[], overall_risk_level="HIGH", bear_bull_classification="NEUTRAL"
            )
        }