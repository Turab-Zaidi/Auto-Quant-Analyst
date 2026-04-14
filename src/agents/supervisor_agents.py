from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict, Any

from src.graph.state import OverallState, ExecutionPlan
from src.llm.nvidia_nim_client import get_llm
from src.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the Supervisor of a team of expert financial AI agents.
Your role is to create a detailed, step-by-step execution plan based on the user's request.

You MUST generate an `ExecutionPlan` object. The `tasks` field must be a list of `Task` objects.
Each `Task` object has two fields:
- `agent`: The specific agent to perform the task. MUST be one of: "fundamental_analyst", "sentiment_analyst", "quant_coder".
- `instructions`: A detailed, specific prompt for that agent.

- The user wants to analyze {company_name} ({ticker}).
- The required analyses are: {analyses}
- If a re-research request is provided, you MUST create a new task that directly addresses it.

Be specific in your instructions. For example, if the user asks about competitive moats, the `instructions` for the `fundamental_analyst` should be "Analyze the company's competitive moat, focusing on network effects and intellectual property."
"""

def supervisor_node(state: OverallState) -> dict:
    logger.info("--- SUPERVISOR AGENT: Generating Execution Plan ---")
    
    req = state.get("analysis_request")
    re_research = state.get("re_research_request") # Check if this is a loop-back
    
    if not req:
        logger.error("Supervisor: No analysis request found.")
        return {}

    llm = get_llm(tier="smart", temperature=0.0) # 70B is great for planning
    structured_llm = llm.with_structured_output(ExecutionPlan)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "User's specific questions: {questions}\n\nRe-research request (if any): {re_research}\n\nGenerate the plan.")
    ])
    
    chain = prompt | structured_llm
    
    try:
        plan = chain.invoke({
            "company_name": req.company_name,
            "ticker": req.ticker,
            "analyses": ", ".join(req.required_analyses),
            "questions": ", ".join(req.specific_questions) if req.specific_questions else "None",
            "re_research": re_research.model_dump_json() if re_research else "None"
        })
        

        logger.info(f"Supervisor Plan Rationale: {plan.rationale}")
        
        return {"execution_plan": plan}
        
    except Exception as e:
        logger.error(f"Supervisor failed to generate plan: {e}")
        return {}