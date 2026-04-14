import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
    CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", 8000))
    
    # NEW FREE API KEYS
    FRED_API_KEY = os.getenv("FRED_API_KEY")
    NEWS_API_KEY = os.getenv("NEWS_API_KEY")
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
    
    @classmethod
    def validate(cls):
        if not cls.NVIDIA_API_KEY or cls.NVIDIA_API_KEY == "nvapi-your-key-here":
            raise ValueError("NVIDIA_API_KEY is missing or invalid in .env")