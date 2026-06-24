"""
Embedding generation using Ollama's nomic-embed-text
"""

from typing import List
import numpy as np

from ..config import config


class Embedder:
    """
    Generate embeddings using Ollama's local embedding models.
    """

    def __init__(self, model: str | None = None):
        """
        Initialize embedder.

        Args:
            model: Embedding model name (defaults to config.EMBEDDING_MODEL)
        """
        self.model = model or config.EMBEDDING_MODEL
        self._client = None

    def _get_client(self):
        """
        Lazy-load Ollama client.
        """
        if self._client is None:
            try:
                import ollama
                self._client = ollama
            except ImportError as e:
                raise ImportError(
                    "Ollama package not installed. Run: pip install ollama"
                ) from e
        return self._client

    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Input text for embedding is empty.")

        client = self._get_client()

        # Manual truncation to avoid context length errors
        # 8000 chars is roughly 2000 tokens, safe for most models
        if len(text) > 8000:
            text = text[:8000]

        try:
            response = client.embeddings(
                model=self.model,
                prompt=text,
                options=config.OLLAMA_OPTIONS
            )
            embedding = response.get("embedding")
            if embedding is None:
                raise RuntimeError("No embedding returned by Ollama.")
            return embedding

        except Exception as e:
            raise RuntimeError(f"Embedding generation failed: {e}") from e

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts
            batch_size: Number of texts processed per batch

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        client = self._get_client()
        embeddings: List[List[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = [t for t in texts[i:i + batch_size] if t.strip()]
            if not batch:
                continue

            # Manual truncation
            batch = [t[:8000] if len(t) > 8000 else t for t in batch]

            try:
                response = client.embeddings(
                    model=self.model,
                    prompt=batch,
                    options=config.OLLAMA_OPTIONS
                )
                batch_embeddings = response.get("embeddings")

                if batch_embeddings is None:
                    raise RuntimeError("Batch embedding failed.")

                embeddings.extend(batch_embeddings)

            except Exception as e:
                raise RuntimeError(f"Batch embedding failed: {e}") from e

        return embeddings

    def embed_numpy(self, text: str) -> np.ndarray:
        """
        Generate embedding as numpy array.

        Args:
            text: Input text

        Returns:
            Embedding as numpy array
        """
        return np.asarray(self.embed(text), dtype=np.float32)

    def similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Cosine similarity score in range [0, 1]
        """
        emb1 = self.embed_numpy(text1)
        emb2 = self.embed_numpy(text2)

        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0

        similarity = float(np.dot(emb1, emb2) / (norm1 * norm2))
        return max(0.0, min(similarity, 1.0))
