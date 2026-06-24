"""
Maximal Marginal Relevance (MMR) for diverse retrieval results.
"""

from typing import List, Dict, Any, Callable, Optional
import numpy as np


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors"""
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def mmr_select(
    query_embedding: np.ndarray,
    candidates: List[Dict[str, Any]],
    embeddings: List[np.ndarray],
    lambda_param: float = 0.5,
    k: int = 5
) -> List[Dict[str, Any]]:
    """
    Select documents using Maximal Marginal Relevance (MMR).
    
    MMR balances relevance to the query with diversity among selected documents.
    
    MMR Score = λ × sim(doc, query) - (1-λ) × max(sim(doc, selected))
    
    Args:
        query_embedding: Query vector
        candidates: List of candidate documents
        embeddings: Embeddings for each candidate (same order)
        lambda_param: Trade-off between relevance (1) and diversity (0)
        k: Number of documents to select
        
    Returns:
        Selected documents in MMR order
    """
    if not candidates or not embeddings:
        return []
    
    k = min(k, len(candidates))
    
    # Convert to numpy arrays
    query_emb = np.asarray(query_embedding)
    doc_embs = [np.asarray(e) for e in embeddings]
    
    # Calculate query-document similarities
    query_sims = [cosine_similarity(query_emb, emb) for emb in doc_embs]
    
    # Track selected and remaining indices
    selected_indices: List[int] = []
    remaining_indices = list(range(len(candidates)))
    
    for _ in range(k):
        best_idx = None
        best_score = float('-inf')
        
        for idx in remaining_indices:
            # Relevance to query
            relevance = query_sims[idx]
            
            # Maximum similarity to already selected documents
            if selected_indices:
                max_sim_to_selected = max(
                    cosine_similarity(doc_embs[idx], doc_embs[sel_idx])
                    for sel_idx in selected_indices
                )
            else:
                max_sim_to_selected = 0.0
            
            # MMR score
            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim_to_selected
            
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx
        
        if best_idx is not None:
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)
    
    # Build result list with MMR scores
    results = []
    for rank, idx in enumerate(selected_indices):
        result = dict(candidates[idx])
        result["mmr_rank"] = rank + 1
        result["mmr_relevance"] = query_sims[idx]
        results.append(result)
    
    return results


class MMRRetriever:
    """
    Retriever wrapper that applies MMR for diverse results.
    """
    
    def __init__(
        self,
        base_retriever,
        embedder,
        lambda_param: float = 0.5
    ):
        """
        Initialize MMR retriever.
        
        Args:
            base_retriever: Underlying retriever for initial candidates
            embedder: Embedder for computing embeddings
            lambda_param: MMR lambda (0.5 = balanced, 1.0 = pure relevance)
        """
        self.base_retriever = base_retriever
        self.embedder = embedder
        self.lambda_param = lambda_param
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        fetch_k: int = 20,
        lambda_param: Optional[float] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents with MMR diversity.
        
        Args:
            query: Search query
            top_k: Number of diverse results to return
            fetch_k: Number of candidates to fetch before MMR
            lambda_param: Override default lambda (optional)
            **kwargs: Additional args for base retriever
            
        Returns:
            MMR-selected diverse documents
        """
        lambda_val = lambda_param if lambda_param is not None else self.lambda_param
        
        # Fetch candidates
        if hasattr(self.base_retriever, 'retrieve'):
            candidates = self.base_retriever.retrieve(query, top_k=fetch_k, **kwargs)
        else:
            candidates = []
        
        if len(candidates) <= top_k:
            return candidates
        
        # Get query embedding
        query_emb = self.embedder.embed_numpy(query)
        
        # Get candidate embeddings
        contents = [c.get("content", "") for c in candidates]
        try:
            candidate_embs = [self.embedder.embed_numpy(c) for c in contents]
        except Exception:
            # Fall back to returning first k if embedding fails
            return candidates[:top_k]
        
        # Apply MMR
        return mmr_select(
            query_embedding=query_emb,
            candidates=candidates,
            embeddings=candidate_embs,
            lambda_param=lambda_val,
            k=top_k
        )
