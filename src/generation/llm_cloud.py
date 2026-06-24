from typing import List, Generator
from huggingface_hub import InferenceClient
from ..config import config

class HFInferenceLLM:
    """
    LLM implementation using Hugging Face Inference API.
    Used for cloud deployments where Ollama is not available.
    """
    def __init__(self, model_name: str = None):
        self.model = model_name or config.HF_LLM_MODEL
        self.token = config.HF_API_TOKEN
        
        if not self.token:
            print("WARNING: HF_API_TOKEN is not set. Inference API calls will fail.")
            
        self.client = InferenceClient(model=self.model, token=self.token)

    def is_available(self) -> bool:
        """Check if the HF API token is configured and the client is ready."""
        return bool(self.token)

    def generate(self, prompt: str, system: str = None, temperature: float = 0.3, max_tokens: int = 1024) -> str:
        """Generate a complete response using HF Inference API."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error communicating with Hugging Face API: {str(e)}"

    def generate_stream(self, prompt: str, system: str = None, temperature: float = 0.3, max_tokens: int = 1024) -> Generator[str, None, None]:
        """Generate a streaming response using HF Inference API."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        
        messages.append({"role": "user", "content": prompt})

        try:
            stream = self.client.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"\n[Error communicating with Hugging Face API: {str(e)}]"
