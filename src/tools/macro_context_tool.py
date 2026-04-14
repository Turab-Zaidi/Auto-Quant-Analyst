from fredapi import Fred
from datetime import datetime, timedelta
from src.utils.config import Config
from src.memory.redis_cache import cache_result
from src.utils.logger import get_logger

logger = get_logger(__name__)


REGION_MAP = {
    "US": {"rate": "FEDFUNDS", "yield": "DGS10", "cpi": "CPIAUCSL"},
    "United Kingdom": {"rate": "IUDSOIA", "yield": "IRLTLT01GBM156N", "cpi": "GBRCPIALLMINMEI"},
    "China": {"rate": "CHILENDINORSTSAM", "yield": "IRLTLT01CNM156N", "cpi": "CHICPIALLMINMEI"},
    "India": {"rate": "INTDSRINM193N", "yield": "INDIRLTLT01STM", "cpi": "INDCPIALLMINMEI"},
    "Japan": {"rate": "IRSTCB01JPM156N", "yield": "IRLTLT01JPM156N", "cpi": "JPNCPIALLMINMEI"},
    # Eurozone countries share ECB rates
    "Netherlands": {"rate": "ECDFR", "yield": "IRLTLT01NLM156N", "cpi": "NLDCPALTT01CTGYM"},
    "Germany": {"rate": "ECDFR", "yield": "IRLTLT01DEM156N", "cpi": "DEUCPIALLMINMEI"},
    "France": {"rate": "ECDFR", "yield": "IRLTLT01FRM156N", "cpi": "FRACPIALLMINMEI"}
}

@cache_result(ttl_seconds=43200) 
def get_macro_indicators(country: str = "US") -> dict:
    """Fetches macro indicators dynamically based on the company's country."""
    if not Config.FRED_API_KEY:
        return {}

    try:
        fred = Fred(api_key=Config.FRED_API_KEY)
        start_date = datetime.today() - timedelta(days=365)
        
        # Determine mapping (Fallback to US as Global Reserve context)
        is_global_fallback = country not in REGION_MAP
        target_series = REGION_MAP.get(country, REGION_MAP["US"])
        
        results = {"context": f"{country} Local Macro" if not is_global_fallback else "Global USD/Fed Macro Backdrop"}
        
        for name, series_id in target_series.items():
            data = fred.get_series(series_id, observation_start=start_date)
            if not data.empty:
                current_val = float(data.iloc[-1])
                past_val = float(data.iloc[0])
                results[name] = {
                    "current_value": round(current_val, 2),
                    "1_year_ago": round(past_val, 2),
                    "trend": "UP" if current_val > past_val else "DOWN"
                }
                
        return results
    except Exception as e:
        logger.error(f"FRED Macro API failed for {country}: {e}")
        return {}