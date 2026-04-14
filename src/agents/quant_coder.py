from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json
import os
import uuid
import pandas as pd
import io

from src.graph.state import OverallState, QuantReport, TechnicalSummary
from src.llm.nvidia_nim_client import get_llm
from src.tools.financial_data_tool import fetch_price_history
from src.utils.plotting import create_dashboard_chart
from src.utils.logger import get_logger

logger = get_logger(__name__)



SYSTEM_PROMPT = """You are an elite Quantitative Technical Analyst (CMT).
Your only task is to analyze the provided raw JSON data (OHLCV, SMA, RSI) and write a professional, in-depth text summary.
You do NOT need to write any Python code. The charting is handled separately.
Focus entirely on interpreting the numbers and generating the text for the `TechnicalAnalysisSummary` object.
"""

def quant_node(state: OverallState) -> dict:
    logger.info("--- QUANT CODER: Generating Chart & Technical Summary ---")
    req = state.get("analysis_request")
    if not req: return {"quant_report": None}

    try:

        price_data_json = fetch_price_history(req.ticker, period="1y")
        
        df = pd.read_json(io.StringIO(price_data_json), orient='records')
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date').reset_index(drop=True)
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        chart_filename = f"{req.ticker}_dashboard_{uuid.uuid4().hex[:6]}.png"
        temp_save_dir = os.path.join(os.getcwd(), "charts")
        os.makedirs(temp_save_dir, exist_ok=True)
        temp_save_path = os.path.join(temp_save_dir, chart_filename)
        
        create_dashboard_chart(df.tail(252), req.ticker, temp_save_path) 
        docker_save_path = f"/charts/{chart_filename}"
        logger.info(f"Chart generated and saved locally to {temp_save_path}")
        
        llm = get_llm(tier="smart", temperature=0.1)
        structured_llm = llm.with_structured_output(TechnicalSummary)
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "Analyze this data for {ticker} and provide the summary:\n\n{data}")
        ])
        chain = prompt | structured_llm
        
        summary_data = df.tail(30).to_json(orient="records")
        technical_summary_obj = chain.invoke({"ticker": req.ticker, "data": summary_data})

        return {
            "quant_report": QuantReport(
                chart_paths=[docker_save_path],
                technical_summary=technical_summary_obj,
                iterations=1,
                status="COMPLETE"
            ),
            "chart_file_paths": [docker_save_path]
        }

    except Exception as e:
        logger.error(f"Quant Coder failed: {e}", exc_info=True)
        return { "quant_report": QuantReport(chart_paths=[], technical_summary=TechnicalSummary(trend="NEUTRAL", sma_signal="Failed", rsi=0, volume_trend="Failed"), iterations=0, status="FAILED") }