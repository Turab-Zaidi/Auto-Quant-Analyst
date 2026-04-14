from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.graph.state import (
    OverallState, AnalysisRequest, ExecutionPlan, FundamentalReport,
    SentimentReport, QuantReport, TechnicalSummary, RiskReport
)
from src.graph.conditions import route_from_supervisor, route_from_synthesis, route_from_hitl
from src.utils.logger import get_logger
from src.agents.intake_agent import intake_node
from src.agents.fundamental_analyst import fundamental_node
from src.agents.sentiment_analyst import sentiment_node
from src.agents.quant_coder import quant_node
from src.agents.risk_validator import risk_node
from src.agents.synthesis_agent import synthesis_node
from src.agents.supervisor_agents import supervisor_node
from src.agents.report_compiler import report_compiler_node

logger = get_logger(__name__)



def build_graph():
    builder = StateGraph(OverallState)

    # 1. Add Nodes
    builder.add_node("intake_agent", intake_node)
    builder.add_node("supervisor_agent", supervisor_node)
    builder.add_node("fundamental_agent", fundamental_node)
    builder.add_node("sentiment_agent", sentiment_node)
    builder.add_node("quant_agent", quant_node)
    builder.add_node("risk_validator", risk_node)
    builder.add_node("synthesis_agent", synthesis_node)
    builder.add_node("report_compiler", report_compiler_node)

    # 2. Add Edges
    builder.set_entry_point("intake_agent")
    builder.add_edge("intake_agent", "supervisor_agent")
    
    # Parallel Fan-out
    builder.add_conditional_edges("supervisor_agent", route_from_supervisor, 
                                  ["fundamental_agent", "sentiment_agent", "quant_agent"])
    
    # Fan-in to Risk Validator
    builder.add_edge("fundamental_agent", "risk_validator")
    builder.add_edge("sentiment_agent", "risk_validator")
    builder.add_edge("quant_agent", "risk_validator")
    
    # Linear flow
    builder.add_edge("risk_validator", "synthesis_agent")
    
    # Conditional synthesis loop to HITL
    builder.add_conditional_edges("synthesis_agent", route_from_synthesis, 
                                  {"report_compiler": "report_compiler", "supervisor_agent": "supervisor_agent"})
                                  
    builder.add_edge("report_compiler", END)

    # Compile with memory (Required for Human-in-the-Loop interruptions)
    memory = MemorySaver()
    return builder.compile(checkpointer=memory, interrupt_before=["report_compiler"])