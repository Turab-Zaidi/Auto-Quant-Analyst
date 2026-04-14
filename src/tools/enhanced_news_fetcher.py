import requests
import json
from datetime import datetime, timedelta
from tavily import TavilyClient
from src.utils.config import Config
from src.memory.redis_cache import cache_result
from src.utils.logger import get_logger
import re

logger = get_logger(__name__)

def clean_text(text):
    """Removes markdown images, links, and excessive whitespace."""
    if not text: return ""
    # Remove markdown images: ![alt](url)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # Remove markdown links but keep text: [text](url) -> text
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    # Remove excessive newlines and tabs
    text = " ".join(text.split())
    return text[:12000]

@cache_result(ttl_seconds=7200) 
def fetch_enriched_news(ticker: str, days_back: int = 30) -> list:
    """
    Tiered News Strategy:
    1. Fetches 15 articles from Finnhub (Symbol-matched).
    2. Sends top 5 URLs to Tavily Extract for full article content.
    3. Keeps descriptions for the remaining 10.
    """
    ticker_upper = ticker.upper()
    api_key = Config.FINNHUB_API_KEY
    tavily_key = Config.TAVILY_API_KEY

    if not api_key or not tavily_key:
        logger.error("Missing Finnhub or Tavily API keys.")
        return []

    # 1. Fetch from Finnhub
    to_date = datetime.today().strftime('%Y-%m-%d')
    from_date = (datetime.today() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    finnhub_url = "https://finnhub.io/api/v1/company-news"
    params = {
        "symbol": ticker_upper,
        "from": from_date,
        "to": to_date,
        "token": api_key
    }

    try:
        logger.info(f"🚀 Fetching institutional URLs from Finnhub for {ticker_upper}")
        response = requests.get(finnhub_url, params=params)
        response.raise_for_status()
        raw_articles = response.json()
        
        if not raw_articles:
            logger.warning(f"No Finnhub news found for {ticker_upper}")
            return []

        top_25 = raw_articles[:25]
        
        tier_1_urls = [a.get("url") for a in top_25[:5] if a.get("url")]


        full_content_map = {}
        if tier_1_urls:
            try:
                logger.info(f"🧠 Cleaning and extracting top 5 {ticker_upper} articles...")
                tavily = TavilyClient(api_key=tavily_key)
                
                extraction = tavily.extract(urls=tier_1_urls)
                
                for res in extraction.get("results", []):
                    raw_body = res.get("raw_content") or res.get("text")
                    if raw_body:
                        full_content_map[res["url"]] = clean_text(raw_body)
            except Exception as e:
                logger.error(f"Tavily extraction failed: {e}")

        enriched_pool = []
        logger.info(f"📊 Assembling enriched news pool for {ticker_upper}{full_content_map.get(list(full_content_map.keys())[0])}...")
        for i, art in enumerate(top_25):
            url = art.get("url")
            date_str = datetime.fromtimestamp(art.get("datetime", 0)).isoformat() + "Z"
            

            if i < 5:
                content_body = full_content_map.get(url) or art.get("summary") or "Content unavailable."
            else:
                content_body = art.get("summary") or "Summary unavailable."
            
            enriched_pool.append({
                "title": art.get("headline"),
                "source": art.get("source"),
                "date": date_str,
                "url": url,
                "content": content_body,
                "is_full_content": (url in full_content_map)
            })

        logger.info(f"✅ Enriched pool complete: {len(enriched_pool)} articles (5 full-text).")
        return enriched_pool

    except Exception as e:
        logger.error(f"Enriched news fetch failed: {e}")
        return []