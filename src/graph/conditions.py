from typing import List
from src.graph.state import OverallState
from src.utils.logger import get_logger


logger = get_logger(__name__)

def route_from_supervisor(state: OverallState) -> List[str]:
    """Dynamically fan-out to workers based on the required_analyses list."""
    req = state.get("analysis_request")
    
    if not req or not req.required_analyses:
        return ["fundamental_agent", "sentiment_agent", "quant_agent"]
        
    nodes_to_run = []
    
    if "fundamental" in req.required_analyses:
        nodes_to_run.append("fundamental_agent")
    if "sentiment" in req.required_analyses:
        nodes_to_run.append("sentiment_agent")
    if "quant" in req.required_analyses:
        nodes_to_run.append("quant_agent")
        
    # Safety catch: if list is somehow empty, run everything
    return nodes_to_run if nodes_to_run else ["fundamental_agent", "sentiment_agent", "quant_agent"]

def route_from_synthesis(state: OverallState) -> str:
    """Check self-reflection logic. Re-route if confidence is low, otherwise HITL."""
    confidence = state.get("synthesis_confidence_score", 100)
    iterations = state.get("synthesis_iteration_count", 0)
    
    if confidence < 65 and iterations < 2 and state.get("re_research_request"):
        logger.warning(f"Confidence score is {confidence} (<65). Looping back to Supervisor for more research.")
        return "supervisor_agent"
    
    logger.info(f"Confidence score is {confidence} (>=65). Proceeding to final report.")
    return "report_compiler" 

def route_from_hitl(state: OverallState) -> str:
    """Read the human decision and route accordingly."""
    decision = state.get("hitl_decision")
    
    if decision == "ABORT":
        return "END"
    elif decision == "DEEPEN_RESEARCH":
        return "supervisor_agent"
    
    # Default is APPROVE
    return "report_compiler"