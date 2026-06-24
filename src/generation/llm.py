"""Local LLM client using Ollama"""
from typing import Optional, Generator, Dict, Any, List
from dataclasses import dataclass

from ..config import config


@dataclass
class Message:
    """Chat message"""
    role: str  # system, user, assistant
    content: str


class LLM:
    """Local LLM client using Ollama"""
    
    def __init__(self, model: str = None):
        """
        Initialize LLM client.
        
        Args:
            model: Model name (default from config)
        """
        self.model = model or config.LLM_MODEL
        self._client = None
    
    def _get_client(self):
        """Lazy load Ollama client"""
        if self._client is None:
            try:
                import ollama
                self._client = ollama
            except ImportError:
                raise ImportError("Ollama package not installed. Run: pip install ollama")
        return self._client
    
    def generate(
        self,
        prompt: str,
        system: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """
        Generate a response.
        
        Args:
            prompt: User prompt
            system: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        client = self._get_client()
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat(
            model=self.model,
            messages=messages,
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
                **getattr(config, 'OLLAMA_OPTIONS', {})
            }
        )
        
        return response["message"]["content"]
    
    def generate_stream(
        self,
        prompt: str,
        system: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Generator[str, None, None]:
        """
        Generate a response with streaming.
        
        Args:
            prompt: User prompt
            system: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Yields:
            Generated text chunks
        """
        client = self._get_client()
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        stream = client.chat(
            model=self.model,
            messages=messages,
            stream=True,
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
                **getattr(config, 'OLLAMA_OPTIONS', {})
            }
        )
        
        for chunk in stream:
            yield chunk["message"]["content"]
    
    def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """
        Multi-turn chat.
        
        Args:
            messages: List of Message objects
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response
        """
        client = self._get_client()
        
        formatted_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
        
        response = client.chat(
            model=self.model,
            messages=formatted_messages,
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
                **getattr(config, 'OLLAMA_OPTIONS', {})
            }
        )
        
        return response["message"]["content"]
    
    def rag_generate(
        self,
        query: str,
        context: str,
        temperature: float = 0.3
    ) -> str:
        """
        Generate a RAG response with context.
        
        Args:
            query: User query
            context: Retrieved context
            temperature: Sampling temperature (lower for factual)
            
        Returns:
            Generated response
        """
        system = """You are a helpful AI assistant that answers questions based on the provided context.

Rules:
1. Answer ONLY based on the information in the context below
2. If the context doesn't contain relevant information, say "I don't have enough information to answer that"
3. Cite your sources by referencing [Source X] when using information
4. Be concise and accurate
5. Do not make up information"""

        prompt = f"""Context:
{context}

Question: {query}

Answer:"""

        return self.generate(
            prompt=prompt,
            system=system,
            temperature=temperature
        )
    
    def is_available(self) -> bool:
        """Check if Ollama is available and model is loaded"""
        try:
            client = self._get_client()
            # Try to list models
            response = client.list()
            
            # ollama.list() returns ListResponse with .models attribute
            # Each model has .model attribute (not .name)
            models = getattr(response, 'models', [])
            
            # Extract model names
            model_names = []
            for m in models:
                # Model object has .model attribute
                name = getattr(m, 'model', '') or getattr(m, 'name', '')
                if name:
                    model_names.append(name.lower())
            
            # Check if our model is available
            target = self.model.lower()
            return target in model_names or any(target in name for name in model_names)
            
        except Exception as e:
            print(f"Model check error: {e}")
            return False
