"""
Advanced Retrieval Module

Provides:
- Retriever: Base semantic retriever
- HybridRetriever: Dense + BM25 hybrid search
- MMRRetriever: Maximal Marginal Relevance for diversity
- CrossEncoderReranker: Reranking with cross-encoder models
- BM25: Sparse retrieval algorithm
"""
from .retriever import Retriever
from .hybrid import BM25, HybridRetriever
from .mmr import mmr_select, MMRRetriever
from .reranker import CrossEncoderReranker

__all__ = [
    "Retriever",
    "BM25",
    "HybridRetriever",
    "mmr_select",
    "MMRRetriever",
    "CrossEncoderReranker",
]
