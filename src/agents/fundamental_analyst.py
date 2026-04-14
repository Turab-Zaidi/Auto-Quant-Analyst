from langchain_core.prompts import ChatPromptTemplate
import json

from src.graph.state import OverallState, FundamentalReport
from src.llm.nvidia_nim_client import get_llm
from src.tools.financial_data_tool import fetch_financial_metrics
from src.tools.macro_context_tool import get_macro_indicators
from src.tools.sec_edgar_tool import get_sec_filing_sections # <--- IMPORT THE NEW TOOL
from src.utils.logger import get_logger

logger = get_logger(__name__)



SYSTEM_PROMPT = """You are a Senior Fundamental Equities Analyst at a top-tier hedge fund. 
One very important rule is you have to be very thorough and detailed in your analysis.Make sure every field you fill is as detailed as possible, with specific numbers and insights. Avoid generic statements
Your goal is to provide a "Hardened Thesis" on {company_name} ({ticker}) based in {country}.

DATA PROVIDED:
1. RAW FINANCIALS: Hard numbers from yfinance.
2. MACRO DATA: Regional economic context from FRED.
3. SEC FILING TEXT: Direct excerpts from the MD&A and Risk Factors sections.

ANALYTICAL RIGOR INSTRUCTIONS:
- CROSS-EXAMINE: Do the raw financials (yfinance) support management's narrative in the SEC excerpts? If revenue is up but the SEC filing warns of supply chain "fragility," flag this contradiction.
- NO BOILERPLATE: Avoid phrases like "The company is doing well." Use "NVIDIA's 65% revenue growth is structurally supported by the transition to the Blackwell architecture, despite the $4.5B inventory charge noted in the 10-K."
- TONE: Be skeptical, ruthless, and objective. 

REPORT FIELDS:
- sec_insights_summary: DO NOT just summarize. Interpret the "delta." What did management admit in the filing that isn't obvious in the stock price? (e.g., geopolitical hurdles, energy constraints).
- fundamental_score: 0-100. Be stingy. A 90+ score requires perfect financials AND a "Clean" SEC risk profile.
- margin_health: Analyze Gross vs Operating margins. Explain if spending (R&D/Sales) is out-pacing revenue growth.

Always ground your commentary in the provided SEC text when available."""

def fundamental_node(state: OverallState) -> dict:
    logger.info("--- FUNDAMENTAL ANALYST: Starting Analysis ---")
    
    req = state.get("analysis_request")
    plan = state.get("execution_plan")
    
    instructions = "No specific instructions provided."
    if plan:
        for task in plan.tasks:
            if task.agent == "fundamental_analyst":
                instructions = task.instructions
                break
    
    if not req:
        return {"fundamental_report": None}
        
    metrics = fetch_financial_metrics(req.ticker)
    macro_data = get_macro_indicators(req.country)
    
    sec_data = get_sec_filing_sections(req.ticker)

    
    # Format the SEC data nicely for the LLM, or clearly state it's missing
    sec_text_for_llm = "Not available for this company."
    if sec_data:
        sec_text_for_llm = f"--- MANAGEMENT'S DISCUSSION (MD&A) ---\n{sec_data.get('mda_snippet', 'N/A')}\n\n"
        sec_text_for_llm += f"--- RISK FACTORS ---\n{sec_data.get('risk_factors_snippet', 'N/A')}"
    
    llm = get_llm(tier="genius", temperature=0.1)
    structured_llm = llm.with_structured_output(FundamentalReport)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "Specific Instructions:\n{instructions}\n\nFinancial Metrics:\n{metrics}\n\nMacroeconomic Data:\n{macro}\n\nSEC Filing Excerpts:\n{sec_text}\n\nGenerate the FundamentalReport.")
    ])
    
    chain = prompt | structured_llm
    
    try:
        logger.info(f"Running LLM Fundamental Analysis for {req.ticker}...")
        
        report = chain.invoke({
            "company_name": req.company_name,
            "ticker": req.ticker,
            "country": req.country,
            "instructions": instructions,
            "metrics": json.dumps(metrics, indent=2),
            "macro": json.dumps(macro_data, indent=2),
            "sec_text": sec_text_for_llm
        })
        
        # Add SEC to data sources if we used it
        sources = ["Yahoo Finance", f"FRED Macro ({req.country})"]
        if sec_data:
            sources.append("SEC EDGAR 10-K/10-Q")
            
        report.data_sources = sources
        report.status = "COMPLETE"
        
        logger.info(f"Fundamental Analysis Complete. Score: {report.fundamental_score}")
        
        return {"fundamental_report": report}
        
    except Exception as e:
        logger.error(f"Fundamental Analyst failed: {e}")
        # (Graceful fallback remains the same)
        return {
            "fundamental_report": FundamentalReport(
                revenue_trend="Error in generation.", eps_analysis="Error.", margin_health="Error.",
                debt_profile="Error.", key_risks=["Analysis failed"], fundamental_score=50,
                macro_context_summary="Error.", macro_impact_score=50,
                data_sources=[], status="FAILED"
            )
        }