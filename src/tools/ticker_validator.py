import yfinance as yf
from src.utils.logger import get_logger

logger = get_logger(__name__)

def validate_ticker(ticker: str) -> dict:
    ticker = ticker.upper().strip()
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if "shortName" in info:
            return {
                "is_valid": True,
                "ticker": ticker,
                "company_name": info.get("shortName", ticker),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "country": info.get("country", "US")  # NEW: Extract the country!
            }
        else:
            return {"is_valid": False, "ticker": ticker, "error": "Ticker not found"}
            
    except Exception as e:
        logger.error(f"Error validating ticker {ticker}: {str(e)}")
        return {"is_valid": False, "ticker": ticker, "error": str(e)}