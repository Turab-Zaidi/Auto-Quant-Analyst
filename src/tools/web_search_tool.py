from tavily import TavilyClient
from src.utils.config import Config
from src.memory.redis_cache import cache_result
from src.utils.logger import get_logger

logger = get_logger(__name__)

@cache_result(ttl_seconds=3600) # 1-hour cache for news (it changes fast)
def search_news(query: str, max_results: int = 5) -> list[dict]:
    """
    Searches the web for news articles related to the query.
    Filters specifically for high-quality financial domains.
    """
    try:
        logger.info(f"Executing web search for: '{query}'")
        if not Config.TAVILY_API_KEY or Config.TAVILY_API_KEY == "tvly-your-key-here":
            logger.warning("Tavily API key missing. Returning empty news.")
            return []

        client = TavilyClient(api_key=Config.TAVILY_API_KEY)
        
        # We use advanced search and target financial domains for higher signal-to-noise
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_domains=["bloomberg.com", "reuters.com", "wsj.com", "cnbc.com", "yahoo.com", "seekingalpha.com"]
        )
        
        results = []
        for res in response.get("results", []):
            results.append({
                "title": res.get("title"),
                "url": res.get("url"),
                "content": res.get("content")
            })
            
        return results
        
    except Exception as e:
        logger.error(f"Tavily search failed for query '{query}': {e}")
        return []