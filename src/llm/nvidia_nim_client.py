from langchain_nvidia_ai_endpoints import ChatNVIDIA
from pydantic import BaseModel, Field
from src.utils.config import Config
from src.utils.logger import get_logger
from src.utils.exceptions import LLMConnectionError

logger = get_logger(__name__)

MODEL_TIERS = {
    "fast": "meta/llama-3.1-8b-instruct",
    
    "smart": "meta/llama-3.3-70b-instruct",
    
    "genius": "meta/llama-3.1-405b-instruct" 
}

def get_llm(tier: str = "smart", temperature: float = 0.0) -> ChatNVIDIA:
    """
    Returns an initialized ChatNVIDIA client based on the requested tier.
    """
    try:
        model_name = MODEL_TIERS.get(tier, MODEL_TIERS["smart"])

        # if tier=='smart':
        #     return ChatNVIDIA(
        #         model=model_name,
        #         nvidia_api_key=Config.NVIDIA_API_KEY, 
        #         max_tokens=4096,
        #         reasoning_budget=4096,
        #         chat_template_kwargs={"enable_thinking":True},
        #     )

        
        # else :
        return ChatNVIDIA(
                model=model_name,
                nvidia_api_key=Config.NVIDIA_API_KEY,
                temperature=temperature,
                max_tokens=8192
            )
    except Exception as e:
        logger.error(f"Failed to initialize NVIDIA LLM ({tier}): {str(e)}")
        raise LLMConnectionError(f"LLM Init Failed: {str(e)}")