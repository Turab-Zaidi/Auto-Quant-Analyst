import json
import redis
from functools import wraps
from typing import Any, Callable
from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize Redis client
try:
    redis_client = redis.Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        decode_responses=True
    )
    redis_client.ping()
except redis.ConnectionError:
    logger.warning("Redis is not running. Caching will be disabled.")
    redis_client = None

def cache_result(ttl_seconds: int = 14400): # Default 4 hours
    """Decorator to cache function results in Redis."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if redis_client is None:
                return func(*args, **kwargs)
                
            # Create a unique cache key based on function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            cached_val = redis_client.get(cache_key)
            if cached_val:
                logger.info(f"Cache HIT for {func.__name__}")
                return json.loads(cached_val)
                
            logger.info(f"Cache MISS for {func.__name__}. Fetching fresh data...")
            result = func(*args, **kwargs)
            
            # Save to cache
            redis_client.setex(cache_key, ttl_seconds, json.dumps(result))
            return result
        return wrapper
    return decorator