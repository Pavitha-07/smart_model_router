# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./smart_router.db")
    
    # API Keys
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    together_api_key: str = os.getenv("TOGETHER_API_KEY", "")
    
    # Model names
    simple_model: str = os.getenv("SIMPLE_MODEL", "google/gemini-flash-1.5")
    medium_model: str = os.getenv("MEDIUM_MODEL", "anthropic/claude-3-haiku")
    complex_model: str = os.getenv("COMPLEX_MODEL", "anthropic/claude-3.5-sonnet")
    
    # Cost per 1M tokens (in USD)
    phi3_cost: float = float(os.getenv("PHI3_COST", "0.10"))
    llama_70b_cost: float = float(os.getenv("LLAMA_70B_COST", "1.00"))
    gpt4o_cost: float = float(os.getenv("GPT4O_COST", "3.00"))


settings = Settings()

# Cost mapping
# Cost mapping
MODEL_COSTS = {
    "google/gemini-flash-1.5": 0.10 / 1_000_000,
    "anthropic/claude-3-haiku": 1.00 / 1_000_000,
    "anthropic/claude-3.5-sonnet": 3.00 / 1_000_000,
}

# Difficulty to model mapping
DIFFICULTY_TO_MODEL = {
    "simple": settings.simple_model,
    "medium": settings.medium_model,
    "complex": settings.complex_model,
}