from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Literal

from src.graph.state import OverallState, AnalysisRequest
from src.llm.nvidia_nim_client import get_llm
from src.tools.ticker_validator import validate_ticker
from src.utils.logger import get_logger

logger = get_logger(__name__)

class IntakeExtraction(BaseModel):
    guessed_ticker: str = Field(description="The stock ticker symbol mentioned in the query.")
    questions: List[str] = Field(description="Specific questions the user wants answered.")
    required_analyses: List[Literal["fundamental", "sentiment", "quant"]] = Field(
        description="Select ALL that apply. 'fundamental' for financials/macro. 'sentiment' for news/social. 'quant' for charts/technical. If a general request, include all three."
    )

def intake_node(state: OverallState) -> dict:
    logger.info("--- INTAKE AGENT: Processing Query ---")
    raw_query = state.get("raw_query", "")
    
    llm_classifier = get_llm('fast', temperature=0.0)
    extractor = llm_classifier.with_structured_output(IntakeExtraction)
    
    try:
        extracted = extractor.invoke(f"Analyze this user query: '{raw_query}'. Extract the ticker, questions, and classify which analyses are needed.")
        raw_ticker = extracted.guessed_ticker
        required_analyses = list(set(extracted.required_analyses)) 
        questions = extracted.questions
    except Exception as e:
        logger.error(f"Failed to extract ticker/scope: {e}")
        raw_ticker = raw_query.split()[0]
        required_analyses = ["fundamental", "sentiment", "quant"] # Fallback to all
        questions = []
        
    validation_result = validate_ticker(raw_ticker)
    
    if not validation_result.get("is_valid"):
        logger.warning(f"Ticker validation failed for: {raw_ticker}")
        return {
            "pipeline_status": "FAILED",
            "pipeline_errors": [{"agent": "intake", "error_type": "InvalidTicker", "error_message": f"Could not find ticker for {raw_ticker}", "timestamp": ""}]
        }
        
    analysis_request = AnalysisRequest(
        ticker=validation_result["ticker"],
        company_name=validation_result["company_name"],
        country=validation_result.get("country", "US"),
        time_range="12M", 
        required_analyses=required_analyses, # <--- Updated
        specific_questions=questions
    )
    
    logger.info(f"Intake complete: {analysis_request.ticker} - Required: {required_analyses}")
    
    return {
        "analysis_request": analysis_request, 
        "pipeline_status": "RUNNING"
    }