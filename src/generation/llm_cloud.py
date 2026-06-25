from typing import Generator
from groq import Groq
from ..config import config


class GroqLLM:
    """
    LLM implementation using Groq API.
    Ultra-fast inference for cloud deployments.
    """

    def __init__(self, model_name: str = None):
        self.model = model_name or config.GROQ_MODEL
        self.api_key = config.GROQ_API_KEY

        if not self.api_key:
            print("WARNING: GROQ_API_KEY is not set. API calls will fail.")

        self.client = Groq(api_key=self.api_key)

    def is_available(self) -> bool:
        """Check if the Groq API key is configured."""
        return bool(self.api_key)

    def generate(
        self,
        prompt: str,
        system: str = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        """Generate a complete response using Groq API."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error communicating with Groq API: {str(e)}"

    def generate_stream(
        self,
        prompt: str,
        system: str = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> Generator[str, None, None]:
        """Generate a streaming response using Groq API."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
        except Exception as e:
            yield f"\n[Error communicating with Groq API: {str(e)}]"
