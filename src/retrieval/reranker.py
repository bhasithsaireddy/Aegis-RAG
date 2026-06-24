"""
Cross-Encoder Reranking for improved retrieval precision.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """
    Rerank retrieval results using a cross-encoder model.
    
    Cross-encoders process query-document pairs together, enabling
    more accurate relevance scoring than bi-encoders (embeddings).
    
    Falls back to LLM-based reranking if sentence-transformers unavailable.
    """
    
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        use_gpu: bool = False,
        fallback_to_llm: bool = True
    ):
        """
        Initialize cross-encoder reranker.
        
        Args:
            model_name: HuggingFace model name for cross-encoder
            use_gpu: Whether to use GPU for inference
            fallback_to_llm: Use LLM for reranking if cross-encoder unavailable
        """
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.fallback_to_llm = fallback_to_llm
        self._model = None
        self._model_loaded = False
        self._use_llm_fallback = False
    
    def _load_model(self):
        """Lazy load the cross-encoder model"""
        if self._model_loaded:
            return
        
        try:
            from sentence_transformers import CrossEncoder
            device = "cuda" if self.use_gpu else "cpu"
            self._model = CrossEncoder(self.model_name, device=device)
            self._model_loaded = True
            logger.info(f"Loaded cross-encoder model: {self.model_name}")
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
            if self.fallback_to_llm:
                self._use_llm_fallback = True
                logger.info("Falling back to LLM-based reranking")
            self._model_loaded = True  # Mark as loaded to avoid retry
        except Exception as e:
            logger.error(f"Failed to load cross-encoder: {e}")
            if self.fallback_to_llm:
                self._use_llm_fallback = True
            self._model_loaded = True
    
    def _rerank_with_cross_encoder(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int,
        content_key: str
    ) -> List[Dict[str, Any]]:
        """Rerank using cross-encoder model"""
        if not candidates:
            return []
        
        # Create query-document pairs
        pairs = [(query, c.get(content_key, "")) for c in candidates]
        
        # Get scores from cross-encoder
        scores = self._model.predict(pairs)
        
        # Combine candidates with scores
        scored = list(zip(candidates, scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Return reranked results
        results = []
        for doc, score in scored[:top_k]:
            result = dict(doc)
            result["rerank_score"] = float(score)
            results.append(result)
        
        return results
    
    def _rerank_with_llm(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int,
        content_key: str
    ) -> List[Dict[str, Any]]:
        """Rerank using Ollama LLM as fallback"""
        try:
            import ollama
        except ImportError:
            logger.warning("Ollama not available for LLM reranking")
            return candidates[:top_k]
        
        if not candidates:
            return []
        
        # Score each candidate
        scored = []
        for candidate in candidates:
            content = candidate.get(content_key, "")[:500]  # Truncate for efficiency
            
            prompt = f"""Rate the relevance of this passage to the query on a scale of 0-10.
Only respond with a single number.

Query: {query}

Passage: {content}

Relevance score (0-10):"""
            
            try:
                response = ollama.generate(
                    model="mistral:7b",
                    prompt=prompt,
                    options={"temperature": 0, "num_predict": 5}
                )
                score_text = response.get("response", "0").strip()
                # Extract first number from response
                import re
                match = re.search(r'\d+', score_text)
                score = int(match.group()) if match else 0
                score = min(10, max(0, score))  # Clamp to 0-10
            except Exception:
                score = 5  # Neutral score on error
            
            scored.append((candidate, score))
        
        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Return results with scores
        results = []
        for doc, score in scored[:top_k]:
            result = dict(doc)
            result["rerank_score"] = score / 10.0  # Normalize to 0-1
            results.append(result)
        
        return results
    
    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5,
        content_key: str = "content"
    ) -> List[Dict[str, Any]]:
        """
        Rerank candidates by relevance to query.
        
        Args:
            query: Search query
            candidates: List of candidate documents
            top_k: Number of results to return
            content_key: Key containing document content
            
        Returns:
            Reranked list of documents with rerank_score
        """
        self._load_model()
        
        if self._use_llm_fallback:
            return self._rerank_with_llm(query, candidates, top_k, content_key)
        elif self._model is not None:
            return self._rerank_with_cross_encoder(query, candidates, top_k, content_key)
        else:
            # No reranking available, return as-is
            return candidates[:top_k]


class CohereReranker:
    """
    Reranker using Cohere's rerank API (for online use cases).
    
    Note: Requires COHERE_API_KEY environment variable.
    """
    
    def __init__(self, model: str = "rerank-english-v2.0"):
        self.model = model
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            import os
            try:
                import cohere
                api_key = os.environ.get("COHERE_API_KEY")
                if not api_key:
                    raise ValueError("COHERE_API_KEY not set")
                self._client = cohere.Client(api_key)
            except ImportError:
                raise ImportError("cohere package not installed")
        return self._client
    
    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5,
        content_key: str = "content"
    ) -> List[Dict[str, Any]]:
        """Rerank using Cohere API"""
        client = self._get_client()
        
        documents = [c.get(content_key, "") for c in candidates]
        
        response = client.rerank(
            model=self.model,
            query=query,
            documents=documents,
            top_n=top_k
        )
        
        results = []
        for r in response.results:
            result = dict(candidates[r.index])
            result["rerank_score"] = r.relevance_score
            results.append(result)
        
        return results
