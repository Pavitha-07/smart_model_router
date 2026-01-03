# app/models.py
from pydantic import BaseModel, Field
from typing import Optional, Literal

class PromptRequest(BaseModel):
    """Incoming request from user"""
    prompt: str = Field(..., min_length=1, max_length=50000)
    user_id: Optional[str] = None
    max_tokens: Optional[int] = Field(default=1000, ge=1, le=4000)
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)

class ClassificationResult(BaseModel):
    """Result from the classifier"""
    difficulty: Literal["simple", "medium", "complex"]
    confidence: float = Field(..., ge=0, le=1)
    reasoning: Optional[str] = None

class RouterResponse(BaseModel):
    """Response sent back to user"""
    response: str
    model_used: str
    difficulty: str
    classification_confidence: float
    tokens_used: int
    cost_usd: float
    cost_saved_usd: float
    latency_ms: float
    request_id: int

class StatsResponse(BaseModel):
    """API statistics"""
    total_requests: int
    total_cost_usd: float
    total_saved_usd: float
    model_breakdown: dict
    avg_latency_ms: float