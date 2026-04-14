from langchain_core.prompts import ChatPromptTemplate
import json
from pydantic import BaseModel, Field
from src.graph.state import OverallState, SentimentReport
from src.llm.nvidia_nim_client import get_llm
# Use the new enriched fetcher
from src.tools.enhanced_news_fetcher import fetch_enriched_news 
from src.utils.logger import get_logger

logger = get_logger(__name__)


SYSTEM_PROMPT = """You are a Lead Financial Intelligence Analyst at a global macro hedge fund.
You are analyzing {company_name} ({ticker}).

### MISSION
Your goal is to perform a 'Scrutiny-First' sentiment analysis. You must look for 'Signal Decay'—where the official company narrative (Tier 2/Finnhub) is beginning to decouple from the deep investigative reality (Tier 1/Tavily Extract).

### STEP-BY-STEP REASONING PROTOCOL (Chain-of-Thought)
Before generating your final structured report, you MUST perform these internal steps:
1. ENTITY FILTERING: Ignore any 'crap' (ads, navigation text, irrelevant stock pick lists). Focus on {company_name} specifically.
2. SOURCE WEIGHTING: Assign 1.0 weight to institutional news (Bloomberg, WSJ, Reuters), 0.7 to official PR, and 0.2 to retail blogs.
3. CONTRADICTION SEARCH: Compare the CEO's quotes in Tier 2 summaries against the 'Fine Print' found in Tier 1 full-text extractions. Look for mentions of litigation, rising 'bad debt' provisions, or slowing customer growth.
4. SEGMENT MAPPING: Categorize sentiment into {company_name}'s key business units.

### ANALYTICAL RIGOR GUIDELINES
- BE CYNICAL: If a CEO says 'growth is robust,' but the full-text article mentions a 'challenging macro environment for credit,' highlight the friction.
- CITE DATA: Mention specific numbers or bank names (e.g., 'Goldman Sachs recently downgraded the price target to $195').
- DETECT HYPE: Differentiate between PR-driven 'American Dream' initiatives and operational efficiency metrics.
"""

def sentiment_node(state: OverallState) -> dict:
    logger.info("--- SENTIMENT ANALYST: Starting Enriched Tiered Analysis ---")
    
    req = state.get("analysis_request")
    plan = state.get("execution_plan")

    instructions = "No specific instructions provided."
    if plan:
        for task in plan.tasks:
            if task.agent == "sentiment_analyst":
                instructions = task.instructions
                break

    if not req:
        return {"sentiment_report": None}
    
    # 1. Tiered Fetching (Finnhub + Tavily Extract)
    logger.info(f"--- SENTIMENT ANALYST: Fetching Enriched News for {req.ticker} ---")
    
    # This tool handles the 15-article logic (5 full, 10 summary) + Redis Caching
    final_news_pool = fetch_enriched_news(
        ticker=req.ticker, 
        days_back=30
    )

    if not final_news_pool:
        logger.warning("No news gathered for analysis.")
        return {
            "sentiment_report": SentimentReport(
                overall_sentiment="NEUTRAL", 
                sentiment_score=0.0,
                status="NO_DATA"
            )
        }

    # 2. Analyze Enriched Data
    llm_smart = get_llm(tier="genius", temperature=0.1) 
    structured_llm = llm_smart.with_structured_output(SentimentReport)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", f"""
        Instructions: {{instructions}}
        
        ENRICHED NEWS POOL:
        {{news}}
        
        TASK:
        1. Perform your Step-by-Step reasoning.
        2. Detect any 'Market Storm' warnings (e.g., Dimon's warnings) and weigh them against fundamental EPS growth.
        3. Generate the SentimentReport JSON.
        """)
    ])
    
    chain = prompt | structured_llm
    
    try:
        logger.info(f"Running LLM Sentiment Analysis... (Total unique articles: {len(final_news_pool)})")
        
        report = chain.invoke({
            "company_name": req.company_name,
            "ticker": req.ticker,
            "instructions": instructions,
            "news": json.dumps(final_news_pool, indent=2)
        })
        
        report.status = "COMPLETE"
        logger.info(f"Sentiment Analysis Complete. Verdict: {report.overall_sentiment} ({report.sentiment_score})")
        
        return {"sentiment_report": report}
        
    except Exception as e:
        logger.error(f"Sentiment Analyst failed: {e}")
        return {"sentiment_report": SentimentReport(status="FAILED")}