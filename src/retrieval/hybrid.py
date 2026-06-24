"""
BM25 Sparse Search for Hybrid Retrieval
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
import math
import re


class BM25:
    """
    BM25 (Best Matching 25) sparse retrieval algorithm.
    
    BM25 is a bag-of-words retrieval function that ranks documents
    based on query terms appearing in each document.
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25.
        
        Args:
            k1: Term frequency saturation parameter (1.2-2.0 typical)
            b: Document length normalization (0-1, 0.75 typical)
        """
        self.k1 = k1
        self.b = b
        self.corpus: List[Dict[str, Any]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        self.doc_freqs: Dict[str, int] = defaultdict(int)  # term -> doc count
        self.idf: Dict[str, float] = {}
        self.tf: List[Dict[str, int]] = []  # doc_idx -> term -> freq
        self._indexed = False
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple whitespace + lowercase tokenization"""
        # Remove punctuation, lowercase, split on whitespace
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        return [t for t in text.split() if len(t) > 1]
    
    def index(self, corpus: List[Dict[str, Any]], content_key: str = "content"):
        """
        Index a corpus of documents.
        
        Args:
            corpus: List of document dicts
            content_key: Key in dict that contains text content
        """
        self.corpus = corpus
        self.doc_lengths = []
        self.doc_freqs = defaultdict(int)
        self.tf = []
        
        # Calculate term frequencies per document
        for doc in corpus:
            content = doc.get(content_key, "")
            tokens = self._tokenize(content)
            self.doc_lengths.append(len(tokens))
            
            # Term frequency for this doc
            tf_doc: Dict[str, int] = defaultdict(int)
            seen_terms = set()
            
            for token in tokens:
                tf_doc[token] += 1
                if token not in seen_terms:
                    self.doc_freqs[token] += 1
                    seen_terms.add(token)
            
            self.tf.append(dict(tf_doc))
        
        # Average document length
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0
        
        # Calculate IDF for all terms
        N = len(corpus)
        for term, df in self.doc_freqs.items():
            # IDF formula: log((N - df + 0.5) / (df + 0.5) + 1)
            self.idf[term] = math.log((N - df + 0.5) / (df + 0.5) + 1)
        
        self._indexed = True
    
    def _score_document(self, query_tokens: List[str], doc_idx: int) -> float:
        """Calculate BM25 score for a single document"""
        score = 0.0
        doc_len = self.doc_lengths[doc_idx]
        tf_doc = self.tf[doc_idx]
        
        for term in query_tokens:
            if term not in tf_doc:
                continue
            
            tf = tf_doc[term]
            idf = self.idf.get(term, 0)
            
            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_length))
            score += idf * (numerator / denominator)
        
        return score
    
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search the indexed corpus.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            
        Returns:
            List of documents with BM25 scores
        """
        if not self._indexed:
            raise ValueError("Corpus not indexed. Call index() first.")
        
        query_tokens = self._tokenize(query)
        
        # Score all documents
        scores = []
        for doc_idx in range(len(self.corpus)):
            score = self._score_document(query_tokens, doc_idx)
            if score > 0:
                scores.append((doc_idx, score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k with scores
        results = []
        for doc_idx, score in scores[:top_k]:
            result = dict(self.corpus[doc_idx])
            result["bm25_score"] = score
            results.append(result)
        
        return results


class HybridRetriever:
    """
    Hybrid retrieval combining dense (vector) and sparse (BM25) search.
    
    Uses Reciprocal Rank Fusion (RRF) to merge results from both methods.
    """
    
    def __init__(self, dense_retriever, bm25: Optional[BM25] = None, alpha: float = 0.5):
        """
        Initialize hybrid retriever.
        
        Args:
            dense_retriever: Dense vector retriever (ChromaStore or Retriever)
            bm25: BM25 instance (created if not provided)
            alpha: Weight for dense results (1-alpha for sparse)
        """
        self.dense_retriever = dense_retriever
        self.bm25 = bm25 or BM25()
        self.alpha = alpha
        self._corpus_indexed = False
    
    def index_corpus(self, documents: List[Dict[str, Any]], content_key: str = "content"):
        """
        Index documents for BM25 search.
        
        Args:
            documents: List of document dicts with content
            content_key: Key containing text content
        """
        self.bm25.index(documents, content_key)
        self._corpus_indexed = True
    
    def _reciprocal_rank_fusion(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Merge results using Reciprocal Rank Fusion (RRF).
        
        RRF Score = Σ 1 / (k + rank)
        
        Args:
            dense_results: Results from dense retrieval
            sparse_results: Results from sparse (BM25) retrieval
            k: RRF constant (typically 60)
            
        Returns:
            Merged and re-ranked results
        """
        doc_scores: Dict[str, float] = defaultdict(float)
        doc_data: Dict[str, Dict[str, Any]] = {}
        
        # Score from dense results
        for rank, doc in enumerate(dense_results, 1):
            doc_id = doc.get("id", str(rank))
            doc_scores[doc_id] += self.alpha * (1 / (k + rank))
            doc_data[doc_id] = doc
        
        # Score from sparse results
        for rank, doc in enumerate(sparse_results, 1):
            doc_id = doc.get("id", str(rank))
            doc_scores[doc_id] += (1 - self.alpha) * (1 / (k + rank))
            if doc_id not in doc_data:
                doc_data[doc_id] = doc
        
        # Sort by combined score
        ranked = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Build result list
        results = []
        for doc_id, rrf_score in ranked:
            result = dict(doc_data[doc_id])
            result["rrf_score"] = rrf_score
            results.append(result)
        
        return results
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        dense_k: int = 20,
        sparse_k: int = 20,
        **dense_kwargs
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search.
        
        Args:
            query: Search query
            top_k: Number of final results
            dense_k: Number of dense results to fetch
            sparse_k: Number of sparse results to fetch
            **dense_kwargs: Additional args for dense retriever
            
        Returns:
            Merged results with RRF scores
        """
        # Dense search
        if hasattr(self.dense_retriever, 'retrieve'):
            dense_results = self.dense_retriever.retrieve(query, top_k=dense_k, **dense_kwargs)
        elif hasattr(self.dense_retriever, 'query'):
            dense_results = self.dense_retriever.query(query_text=query, n_results=dense_k, **dense_kwargs)
        else:
            dense_results = []
        
        # Sparse search
        if self._corpus_indexed:
            sparse_results = self.bm25.search(query, top_k=sparse_k)
        else:
            sparse_results = []
        
        # Merge with RRF
        merged = self._reciprocal_rank_fusion(dense_results, sparse_results)
        
        return merged[:top_k]
