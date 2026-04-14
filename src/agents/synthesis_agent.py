from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json
from typing import Optional
from src.graph.state import OverallState
from src.graph.state import ReResearchRequest
from src.llm.nvidia_nim_client import get_llm
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Pydantic schema for the self-critique step
class Critique(BaseModel):
    critique_text: str = Field(description="Constructive, skeptical critique of the investment thesis.")
    initial_confidence_score: int = Field(ge=0, le=100, description="Your confidence (0-100) in the investment thesis AFTER considering the critique.")
    re_research_request: Optional[ReResearchRequest] = Field(
        description="If confidence is < 65, create a request for a specific agent to get more data. Otherwise, this should be null."
    )

class FinalThesis(BaseModel):
    final_thesis_text: str = Field(description="The final, revised, and polished investment thesis.")
    final_confidence_score: int = Field(ge=0, le=100, description="Your FINAL confidence score (0-100) after incorporating the critique and revising the thesis.")
# --- PROMPTS FOR EACH STEP ---

DRAFT_PROMPT = """You are a Senior Portfolio Manager at a multi-billion dollar hedge fund.
Your task is to synthesize the reports from your junior analysts (Fundamental, Sentiment, Quant, Risk) into a single, cohesive, and actionable investment thesis.

- Weave the different data points together into a narrative.
- Start with a clear "Investment Thesis & Recommendation" section.
- Follow with supporting evidence from the reports.
- Do not just list the data; interpret it. What does it mean for the stock's future?

Generate the initial draft of the investment thesis based on the provided data.
"""

CRITIQUE_PROMPT = """You are a "Red Team" manager at a hedge fund, known for your skepticism.
Your job is to read the draft investment thesis from your colleague and find every possible flaw, unsupported claim, or unaddressed risk.

- What is the weakest part of this argument?
- What data is missing that would make this thesis stronger?
- What would a bear argue against this thesis?
- Assign a final confidence score (0-100). 0 is a fatally flawed thesis, 100 is an undeniable one.

Critique the following draft thesis.
"""

REVISE_PROMPT = """
You are the Senior Portfolio Manager again. You have received a tough critique of your draft.
Your task is to revise your original draft to directly address the critique.
After revising, re-evaluate your own work and provide a FINAL confidence score for the new, hardened thesis.
The final output MUST be a `FinalThesis` object containing both the text and the new score.
"""

def synthesis_node(state: OverallState) -> dict:
    logger.info("--- SYNTHESIS AGENT: Generating & Critiquing Thesis ---")
    
    # Gather all completed reports
    reports = {
        "Fundamental": state.get("fundamental_report").model_dump() if state.get("fundamental_report") else None,
        "Sentiment": state.get("sentiment_report").model_dump() if state.get("sentiment_report") else None,
        "Quant": state.get("quant_report").model_dump() if state.get("quant_report") else None,
        "Risk": state.get("risk_report").model_dump() if state.get("risk_report") else None
    }
    # Filter out any failed/missing reports
    reports_json = json.dumps({k: v for k, v in reports.items() if v}, indent=2)

    # Use our most powerful model for this complex reasoning
    llm = get_llm(tier="smart", temperature=0.2)
    
    try:
        # --- Step 1: Draft Synthesis ---
        logger.info("Step 1: Generating draft thesis...")
        draft_prompt = ChatPromptTemplate.from_messages([("system", DRAFT_PROMPT), ("human", "Analyst Reports:\n{reports}")])
        draft_chain = draft_prompt | llm
        draft_thesis = draft_chain.invoke({"reports": reports_json}).content
        
        logger.info("Step 2: Critiquing the draft...")
        critique_prompt = ChatPromptTemplate.from_messages([("system", CRITIQUE_PROMPT), ("human", "Draft Thesis:\n{draft}")])
        critique_chain = critique_prompt | llm.with_structured_output(Critique)
        critique_result = critique_chain.invoke({"draft": draft_thesis})
        
        # --- Step 3: Final Revision ---
        logger.info("Step 3: Revising based on critique...")
        revise_prompt = ChatPromptTemplate.from_messages([("system", REVISE_PROMPT), ("human", "Original Draft:\n{draft}\n\nSkeptical Critique:\n{critique}")])
        revise_chain = revise_prompt | llm.with_structured_output(FinalThesis)

        final_result = revise_chain.invoke({
            "draft": draft_thesis,
            "critique": critique_result.critique_text
        })
        
        initial_confidence = critique_result.initial_confidence_score   
        final_confidence = final_result.final_confidence_score
        
        logger.info(f"Synthesis Complete. Initial Score: {initial_confidence}, Final Score: {final_confidence}")

        should_loop = critique_result.re_research_request and final_confidence < 65

        if should_loop:
            logger.warning(f"Self-healing triggered! Requesting re-research from {critique_result.re_research_request.target_agent}.")

        current_iterations = state.get("synthesis_iteration_count", 0) + 1


        return {
            "synthesis_draft": draft_thesis,
            "synthesis_critique": critique_result.critique_text,
            "synthesis_final": final_result.final_thesis_text,
            "synthesis_confidence_score": final_confidence,
            "re_research_request": critique_result.re_research_request if should_loop else None,
            "synthesis_iteration_count": current_iterations
        }

    except Exception as e:
        logger.error(f"Synthesis Agent failed: {e}")
        return {
            "synthesis_final": "Error during synthesis.",
            "synthesis_confidence_score": 0,
        }