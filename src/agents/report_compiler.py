from langchain_core.prompts import ChatPromptTemplate
import json

from src.graph.state import OverallState
from src.llm.nvidia_nim_client import get_llm
from src.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the Lead Investment Publisher at a top-tier institutional hedge fund (e.g., Goldman Sachs, Morgan Stanley). 
Your task is to transform raw multi-agent JSON data into a comprehensive, 10-section, 3,500-4,000 word professional Investment Memo.

### THE RESEARCH CONFIDENCE PROTOCOL
You must explicitly define the 'Confidence Score' as the internal integrity of our research process.
- State that the score reflects the alignment between analysts and the freshness of the data.
- High Confidence (80+): Reflects data congruence across Fundamental, Sentiment, and Quant agents.
- Lower Confidence (<70): Suggests a data gap or a divergence in agent signals, requiring higher modeling uncertainty.
DO NOT frame this as a prediction of the stock's future success; it is a score of our document's reliability.

### STERN EXPANSION RULES:
1. NO SUMMARIZING: You are strictly forbidden from condensing the JSON input. If an analyst provides 5 sentences, you must use all 5 and expand with 2-3 sentences of analytical 'Why'.
2. THE 'SO WHAT' FACTOR: For every metric (e.g., RSI of 73 or a 2.5% revenue growth), explain the institutional implication. How does this affect the Portfolio Manager's risk?
3. ATTRIBUTION: Explicitly mention the sources cited in the JSON (e.g., 'Per SEC 10-K filings' or 'Institutional sentiment from Finnhub').
4. PROFESSIONAL TONE: Use sophisticated financial vernacular (e.g., 'Operational Leverage', 'Accretive Growth', 'Mean Reversion', 'Thesis Hardening').

### MEMO STRUCTURE:
# 1. Executive Summary & Final Verdict
(3-5 paragraphs. Lead with Buy/Sell/Hold, Target Price, and the 12-month rationale. Highlight the Research Confidence Score and its definition as a process reliability metric.)

# 2. Strategic Investment Thesis (The Synthesis)
(Expand heavily on the 'synthesis' field. Discuss the 'clash' of narratives and how the final recommendation was forged through agent consensus.)

# 3. Fundamental Deep Dive: Revenue & EPS Quality
(Use 'revenue_trend' and 'eps_analysis'. Analyze the sustainability of the growth—is it top-line volume or just margin expansion?)

# 4. Operational Efficiency & Margin Health
(Use the 'margin_health' data. Discuss the 'efficiency ratio' and how it compares to the broader sector.)

# 5. SEC Filing Analysis & Risk Transparency
(Use 'sec_filing_summary'. Highlight 'Delta Risks'—the small risks mentioned in filings that the mainstream media is currently ignoring.)

# 6. Solvency & Capital Allocation
(Use 'debt_profile'. Analyze the cash-to-debt relationship. Discuss the company’s ability to fund M&A or buybacks in a 3.75% rate environment.)

# 7. Sentiment Intelligence & Narrative Pulse
(Expand on the 5 news narratives. Identify the dominant market 'Obsession' and whether it is supported by the Ticker-Specific news pool.)

# 8. Technical & Quantitative Posture
(Use the 'technical_summary'. Discuss SMA crossovers and the RSI logic. Reference the dashboard.)
![Technical Dashboard](CHART_PATH_HERE)

# 9. Risk Asymmetry & Analyst Contradictions
(Explain the 'contradiction_score'. Detail exactly why the agents disagree (e.g., 'Bullish technicals vs. Bearish SEC warnings').)

# 10. Conclusion & Forward-Looking Outlook
(Final 12-month prediction based on 'analyst_consensus'. Define the 'Bull Case' and the 'Bear Trigger' for the next quarter.)
"""

def report_compiler_node(state: OverallState) -> dict:
    logger.info("--- REPORT COMPILER: Assembling Final Report ---")
    
    req = state.get("analysis_request")
    synthesis = state.get("synthesis_final")
    confidence = state.get("synthesis_confidence_score")
    fund = state.get("fundamental_report")
    sent = state.get("sentiment_report")
    quant = state.get("quant_report")
    risk = state.get("risk_report")
    chart_paths = state.get("chart_file_paths", [])
    
    report_data = {
        "ticker": req.ticker if req else "N/A",
        "company_name": req.company_name if req else "N/A",
        "synthesis": synthesis,
        "confidence_score": confidence,
        
        "fundamental_analysis": fund.model_dump() if fund and fund.status == "COMPLETE" else None,
        "sentiment_analysis": sent.model_dump() if sent and sent.status == "COMPLETE" else None,
        
        "technical_summary": quant.technical_summary.model_dump() if quant and quant.status == "COMPLETE" else None,
        
        "risk_assessment": risk.model_dump() if risk else None,
        "chart_paths": chart_paths
    }
    
    logger.info(f"Compiling final report... with data {json.dumps(report_data, indent=2)}")
    llm_fast = get_llm(tier="smart", temperature=0.2)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "Here is all the data. Please compile the final Markdown report:\n\n{report_data}")
    ])
    
    chain = prompt | llm_fast
    
    try:
        final_report = chain.invoke({
            "report_data": json.dumps(report_data, indent=2)
        }).content
        
        logger.info("Final report compiled successfully.")
        
        return {
            "final_report_markdown": final_report,
            "pipeline_status": "COMPLETE"
        }
        
    except Exception as e:
        logger.error(f"Report Compiler failed: {e}")
        return {
            "final_report_markdown": f"# Report Generation Failed\n\nAn error occurred during the final compilation step: {e}",
            "pipeline_status": "FAILED"
        }