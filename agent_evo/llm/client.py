from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import openai
from openai import OpenAI

class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def generate(self, 
                 messages: List[Dict[str, str]], 
                 temperature: float = 0.7,
                 max_tokens: Optional[int] = None) -> str:
        """Generate a response from the LLM."""
        pass

class OpenAIClient(LLMClient):
    """OpenAI API client implementation."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def generate(self, 
                 messages: List[Dict[str, str]], 
                 temperature: float = 0.7,
                 max_tokens: Optional[int] = None) -> str:
        """Generate a response using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")

class MockLLMClient(LLMClient):
    """Mock LLM client for testing."""
    
    def __init__(self, responses: Optional[List[str]] = None):
        self.responses = responses or ["This is a mock response."]
        self.call_count = 0
    
    def generate(self, 
                 messages: List[Dict[str, str]], 
                 temperature: float = 0.7,
                 max_tokens: Optional[int] = None) -> str:
        """Return a mock response."""
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return response