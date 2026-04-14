import yfinance as yf
import pandas as pd
from typing import Dict, Any
from src.memory.redis_cache import cache_result
from src.utils.logger import get_logger
from src.utils.exceptions import ToolExecutionError

logger = get_logger(__name__)

@cache_result(ttl_seconds=14400) # 4 hours cache
def fetch_price_history(ticker: str, period: str = "1y") -> str:
    """
    Fetches OHLCV price history and returns it as a JSON string.
    This is what the Quant Coder will use to draw charts.
    """
    try:
        logger.info(f"Fetching {period} price history for {ticker}")
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        
        if df.empty:
            raise ToolExecutionError(f"No price data found for {ticker}")
            
        # Format the dataframe for easy LLM reading/coding
        df.reset_index(inplace=True)
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        # We only need core columns
        return df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].to_json(orient="records")
        
    except Exception as e:
        logger.error(f"Failed to fetch price history for {ticker}: {e}")
        raise ToolExecutionError(f"Price data fetch failed: {e}")

@cache_result(ttl_seconds=86400) # 24 hours cache for fundamentals
def fetch_financial_metrics(ticker: str) -> Dict[str, Any]:
    """
    Fetches core financial ratios and metrics for the Fundamental Analyst.
    """
    try:
        logger.info(f"Fetching financial metrics for {ticker}")
        stock = yf.Ticker(ticker)
        info = stock.info
        
        return {
            "market_cap": info.get("marketCap"),
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "price_to_book": info.get("priceToBook"),
            "profit_margins": info.get("profitMargins"),
            "operating_margins": info.get("operatingMargins"),
            "return_on_equity": info.get("returnOnEquity"),
            "revenue_growth": info.get("revenueGrowth"),
            "total_cash": info.get("totalCash"),
            "total_debt": info.get("totalDebt"),
            "free_cash_flow": info.get("freeCashflow"),
            "debt_to_equity": info.get("debtToEquity")
        }
    except Exception as e:
        logger.error(f"Failed to fetch financial metrics for {ticker}: {e}")
        raise ToolExecutionError(f"Metrics fetch failed: {e}")