# app/router/model_clients.py
from abc import ABC, abstractmethod
from typing import Dict, Any
import httpx
import time
from openai import OpenAI
from app.config import settings

class ModelClient(ABC):
    """Abstract base class for model clients"""
    
    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Generate a response from the model"""
        pass

class OpenAIClient(ModelClient):
    """Client for OpenRouter (compatible with OpenAI API)"""
    
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        # Hardcode a simple free model for testing
        self.model = "qwen/qwen-2-7b-instruct:free"
    
    async def generate(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,  # Use the hardcoded model
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            return {
                "response": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens if response.usage else 100,
                "latency_ms": latency_ms,
                "status": "success"
            }
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "tokens_used": 0,
                "latency_ms": (time.time() - start_time) * 1000,
                "status": "error"
            }

class TogetherAIClient(ModelClient):
    """Client for Together AI (Llama models, Phi-3, etc.)"""
    
    def __init__(self, model_name: str):
        self.api_key = settings.together_api_key
        self.base_url = "https://api.together.xyz/v1/chat/completions"
        self.model_name = model_name
        
        # Model name mapping for Together AI
        self.model_map = {
            "llama-3-70b": "meta-llama/Llama-3-70b-chat-hf",
            "llama-3-8b": "meta-llama/Llama-3-8b-chat-hf",
            "phi-3-mini": "microsoft/phi-3-mini-128k-instruct",
        }
    
    async def generate(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        start_time = time.time()
        
        model_id = self.model_map.get(self.model_name, self.model_name)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
            
            latency_ms = (time.time() - start_time) * 1000
            
            return {
                "response": data["choices"][0]["message"]["content"],
                "tokens_used": data["usage"]["total_tokens"],
                "latency_ms": latency_ms,
                "status": "success"
            }
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "tokens_used": 0,
                "latency_ms": (time.time() - start_time) * 1000,
                "status": "error"
            }

class ModelRouter:
    """Routes requests to the appropriate model based on difficulty"""
    
    def __init__(self):
        # We'll create clients on-demand for OpenRouter
        pass
    
    def get_client(self, model_name: str) -> ModelClient:
        """Get the appropriate client for a model"""
        # All models go through OpenRouter now
        client = OpenAIClient()
        client.model = model_name
        return client
    
    async def route_and_generate(
        self,
        difficulty: str,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> tuple:
        """Route the prompt to appropriate model and generate response"""
        from app.config import DIFFICULTY_TO_MODEL
        
        model_name = DIFFICULTY_TO_MODEL[difficulty]
        client = self.get_client(model_name)
        
        response = await client.generate(prompt, max_tokens, temperature)
        
        return response, model_name