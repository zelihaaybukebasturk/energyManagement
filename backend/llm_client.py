"""
LLM Client for AI-powered explanations
Supports multiple LLM providers: OpenAI, Anthropic, and Ollama (local)
"""

import os
from typing import Dict, Optional
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using the LLM."""
        pass


class OpenAIClient(LLMClient):
    """OpenAI GPT client."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name (default: gpt-4o-mini for cost efficiency)
        """
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
            self.model = model
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client: {e}")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using OpenAI API."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")


class AnthropicClient(LLMClient):
    """Anthropic Claude client."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        """
        Initialize Anthropic client.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model name (default: claude-3-haiku for cost efficiency)
        """
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
            self.model = model
        except ImportError:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")
        except Exception as e:
            raise ValueError(f"Failed to initialize Anthropic client: {e}")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using Anthropic API."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=system_prompt or "You are an expert energy efficiency consultant.",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {e}")


class OllamaClient(LLMClient):
    """Ollama local LLM client."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        """
        Initialize Ollama client for local LLM.
        
        Args:
            base_url: Ollama server URL (default: http://localhost:11434)
            model: Model name (default: llama3.2)
        """
        self.base_url = base_url
        self.model = model
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using Ollama API."""
        try:
            import requests
            
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 1500
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except ImportError:
            raise ImportError("requests package not installed. Install with: pip install requests")
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}. Make sure Ollama is running on {self.base_url}")


class TemplateLLMClient(LLMClient):
    """Fallback template-based client (no API needed)."""
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Return a simple message indicating LLM is not configured."""
        return (
            "LLM integration is not configured. "
            "Please set up OpenAI, Anthropic, or Ollama to enable AI-powered explanations. "
            "For now, using template-based explanations."
        )


def get_llm_client(provider: Optional[str] = None) -> LLMClient:
    """
    Factory function to get the appropriate LLM client.
    
    Args:
        provider: LLM provider name ("openai", "anthropic", "ollama", or None for auto-detect)
    
    Returns:
        LLMClient instance
    """
    provider = provider or os.getenv("LLM_PROVIDER", "").lower()
    
    # Auto-detect based on environment variables
    if not provider:
        # Check for Ollama first (local, free option)
        try:
            import requests
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            response = requests.get(f"{ollama_url}/api/tags", timeout=2)
            if response.status_code == 200:
                provider = "ollama"
        except:
            pass
        
        # Then check for API keys
        if not provider:
            if os.getenv("OPENAI_API_KEY"):
                provider = "openai"
            elif os.getenv("ANTHROPIC_API_KEY"):
                provider = "anthropic"
    
    if provider == "openai":
        return OpenAIClient()
    elif provider == "anthropic":
        return AnthropicClient()
    elif provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        # Support llama3.2 (default), tinyllama, mistral, etc.
        model = os.getenv("OLLAMA_MODEL", "llama3.2")
        return OllamaClient(base_url=base_url, model=model)
    else:
        # Fallback to template-based
        return TemplateLLMClient()
