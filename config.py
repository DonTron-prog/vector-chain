"""Shared configuration for the investment research system."""

import os
from dotenv import load_dotenv
from pydantic_ai.models.openai import OpenAIModel

# Load environment variables once
load_dotenv()


def get_openai_model(model_name: str = 'gpt-4o-mini') -> OpenAIModel:
    """Get configured OpenAI model instance.
    
    Args:
        model_name: Model name to use (default: gpt-4o-mini)
        
    Returns:
        Configured OpenAIModel instance
    """
    return OpenAIModel(
        model_name,
        base_url='https://openrouter.ai/api/v1',
        api_key=os.getenv('OPENROUTER_API_KEY')
    )


def get_required_env_var(var_name: str) -> str:
    """Get required environment variable or raise error.
    
    Args:
        var_name: Environment variable name
        
    Returns:
        Environment variable value
        
    Raises:
        RuntimeError: If environment variable is not set
    """
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(f"{var_name} environment variable is required")
    return value


# Common configuration values
DEFAULT_MODEL = 'gpt-4o-mini'
SEARXNG_URL = "http://localhost:8080"
CHROMA_PATH = "./investment_chroma_db"
KNOWLEDGE_PATH = "./knowledge_base"