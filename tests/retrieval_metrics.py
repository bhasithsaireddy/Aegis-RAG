"""
Comprehensive Information Retrieval Evaluation Metrics

This module provides standard IR metrics for evaluating retrieval quality:
- Recall@K, Precision@K
- Mean Reciprocal Rank (MRR)
- Normalized Discounted Cumulative Gain (NDCG)
- Mean Average Precision (MAP)
- F1@K
"""

from typing import List, Set, Dict, Optional
from statistics import mean
import math


# =============================================================================
# BASIC METRICS
# =============================================================================

def recall_at_k(
    retrieved_ids: List[str],
    relevant_ids: Set[str],
    k: int
) -> float:
    """
    Recall@K: Fraction of relevant documents retrieved in top-K.
    
    Formula: |Retrieved ∩ Relevant| / |Relevant|
    
    Args:
        retrieved_ids: List of retrieved document IDs (ranked)
        relevant_ids: Set of relevant document IDs
        k: Number of top results to consider
        
    Returns:
        Recall score (0 to 1)
    """
    if not relevant_ids:
        return 0.0
    
    retrieved_set = set(retrieved_ids[:k])
    hits = len(retrieved_set & relevant_ids)
    return hits / len(relevant_ids)


def precision_at_k(
    retrieved_ids: List[str],
    relevant_ids: Set[str],
    k: int
) -> float:
    """
    Precision@K: Fraction of top-K results that are relevant.
    
    Formula: |Retrieved@K ∩ Relevant| / K
    
    Args:
        retrieved_ids: List of retrieved document IDs (ranked)
        relevant_ids: Set of relevant document IDs
        k: Number of top results to consider
        
    Returns:
        Precision score (0 to 1)
    """
    if k == 0:
        return 0.0
    
    retrieved_set = set(retrieved_ids[:k])
    hits = len(retrieved_set & relevant_ids)
    return hits / k


def f1_at_k(
    retrieved_ids: List[str],
    relevant_ids: Set[str],
    k: int
) -> float:
    """
    F1@K: Harmonic mean of Precision@K and Recall@K.
    
    Formula: 2 × (P@K × R@K) / (P@K + R@K)
    
    Args:
        retrieved_ids: List of retrieved document IDs (ranked)
        relevant_ids: Set of relevant document IDs
        k: Number of top results to consider
        
    Returns:
        F1 score (0 to 1)
    """
    p = precision_at_k(retrieved_ids, relevant_ids, k)
    r = recall_at_k(retrieved_ids, relevant_ids, k)
    
    if p + r == 0:
        return 0.0
    
    return 2 * (p * r) / (p + r)


def hit_rate_at_k(
    retrieved_ids: List[str],
    relevant_ids: Set[str],
    k: int
) -> int:
    """
    Hit Rate@K (Binary Recall): 1 if any relevant doc in top-K, else 0.
    
    Also known as Success@K or Recall@K (binary).
    
    Args:
        retrieved_ids: List of retrieved document IDs (ranked)
        relevant_ids: Set of relevant document IDs
        k: Number of top results to consider
        
    Returns:
        1 if hit, 0 otherwise
    """
    return int(any(doc_id in relevant_ids for doc_id in retrieved_ids[:k]))


# =============================================================================
# RANKING METRICS
# =============================================================================

def reciprocal_rank(
    retrieved_ids: List[str],
    relevant_ids: Set[str]
) -> float:
    """
    Reciprocal Rank: 1/rank of the first relevant document.
    
    Used to compute Mean Reciprocal Rank (MRR) across queries.
    
    Args:
        retrieved_ids: List of retrieved document IDs (ranked)
        relevant_ids: Set of relevant document IDs
        
    Returns:
        Reciprocal rank (0 to 1, 0 if no relevant found)
    """
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def average_precision(
    retrieved_ids: List[str],
    relevant_ids: Set[str]
) -> float:
    """
    Average Precision (AP): Mean of precision at each relevant position.
    
    Used to compute Mean Average Precision (MAP) across queries.
    
    Args:
        retrieved_ids: List of retrieved document IDs (ranked)
        relevant_ids: Set of relevant document IDs
        
    Returns:
        Average precision score (0 to 1)
    """
    if not relevant_ids:
        return 0.0
    
    num_relevant = 0
    precision_sum = 0.0
    
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            num_relevant += 1
            precision_at_rank = num_relevant / rank
            precision_sum += precision_at_rank
    
    return precision_sum / len(relevant_ids)


def dcg_at_k(
    retrieved_ids: List[str],
    relevance_scores: Dict[str, float],
    k: int
) -> float:
    """
    Discounted Cumulative Gain at K.
    
    Measures ranking quality with graded relevance.
    
    Formula: Σ (2^rel_i - 1) / log2(i + 1) for i in 1..k
    
    Args:
        retrieved_ids: List of retrieved document IDs (ranked)
        relevance_scores: Dict mapping doc_id to relevance score (0-1 or graded)
        k: Number of top results to consider
        
    Returns:
        DCG score
    """
    dcg = 0.0
    for i, doc_id in enumerate(retrieved_ids[:k]):
        rel = relevance_scores.get(doc_id, 0.0)
        # Use 2^rel - 1 for graded relevance, or just rel for binary
        gain = (2 ** rel) - 1 if rel > 1 else rel
        discount = math.log2(i + 2)  # i+2 because i is 0-indexed
        dcg += gain / discount
    return dcg


def ndcg_at_k(
    retrieved_ids: List[str],
    relevance_scores: Dict[str, float],
    k: int
) -> float:
    """
    Normalized Discounted Cumulative Gain at K.
    
    NDCG = DCG@K / IDCG@K (ideal DCG)
    
    Args:
        retrieved_ids: List of retrieved document IDs (ranked)
        relevance_scores: Dict mapping doc_id to relevance score
        k: Number of top results to consider
        
    Returns:
        NDCG score (0 to 1)
    """
    dcg = dcg_at_k(retrieved_ids, relevance_scores, k)
    
    # Compute ideal DCG (sort by relevance desc)
    ideal_order = sorted(relevance_scores.keys(), 
                         key=lambda x: relevance_scores[x], 
                         reverse=True)[:k]
    idcg = dcg_at_k(ideal_order, relevance_scores, k)
    
    return dcg / idcg if idcg > 0 else 0.0


def ndcg_at_k_binary(
    retrieved_ids: List[str],
    relevant_ids: Set[str],
    k: int
) -> float:
    """
    NDCG@K for binary relevance (relevant=1, not relevant=0).
    
    Convenience function when you only have binary relevance judgments.
    
    Args:
        retrieved_ids: List of retrieved document IDs (ranked)
        relevant_ids: Set of relevant document IDs
        k: Number of top results to consider
        
    Returns:
        NDCG score (0 to 1)
    """
    relevance_scores = {doc_id: 1.0 for doc_id in relevant_ids}
    return ndcg_at_k(retrieved_ids, relevance_scores, k)


# =============================================================================
# AGGREGATION FUNCTIONS
# =============================================================================

def mean_reciprocal_rank(
    results: List[tuple]  # List of (retrieved_ids, relevant_ids)
) -> float:
    """
    Mean Reciprocal Rank (MRR) across multiple queries.
    
    Args:
        results: List of (retrieved_ids, relevant_ids) tuples
        
    Returns:
        MRR score (0 to 1)
    """
    if not results:
        return 0.0
    
    rrs = [reciprocal_rank(ret, rel) for ret, rel in results]
    return mean(rrs)


def mean_average_precision(
    results: List[tuple]  # List of (retrieved_ids, relevant_ids)
) -> float:
    """
    Mean Average Precision (MAP) across multiple queries.
    
    Args:
        results: List of (retrieved_ids, relevant_ids) tuples
        
    Returns:
        MAP score (0 to 1)
    """
    if not results:
        return 0.0
    
    aps = [average_precision(ret, rel) for ret, rel in results]
    return mean(aps)


def average(values: List[float]) -> float:
    """Compute mean of values, return 0 if empty"""
    return mean(values) if values else 0.0


# =============================================================================
# EVALUATION REPORT
# =============================================================================

def evaluate_retrieval(
    retrieved_ids: List[str],
    relevant_ids: Set[str],
    k_values: List[int] = [1, 3, 5, 10],
    relevance_scores: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Compute comprehensive evaluation metrics for a single query.
    
    Args:
        retrieved_ids: List of retrieved document IDs (ranked)
        relevant_ids: Set of relevant document IDs
        k_values: List of K values to compute metrics at
        relevance_scores: Optional graded relevance (for NDCG)
        
    Returns:
        Dictionary of metric names to values
    """
    results = {}
    
    # Per-K metrics
    for k in k_values:
        results[f"recall@{k}"] = recall_at_k(retrieved_ids, relevant_ids, k)
        results[f"precision@{k}"] = precision_at_k(retrieved_ids, relevant_ids, k)
        results[f"f1@{k}"] = f1_at_k(retrieved_ids, relevant_ids, k)
        results[f"hit_rate@{k}"] = hit_rate_at_k(retrieved_ids, relevant_ids, k)
        results[f"ndcg@{k}"] = ndcg_at_k_binary(retrieved_ids, relevant_ids, k)
    
    # Overall metrics
    results["mrr"] = reciprocal_rank(retrieved_ids, relevant_ids)
    results["ap"] = average_precision(retrieved_ids, relevant_ids)
    
    # With graded relevance
    if relevance_scores:
        for k in k_values:
            results[f"ndcg_graded@{k}"] = ndcg_at_k(retrieved_ids, relevance_scores, k)
    
    return results


def evaluate_batch(
    batch_results: List[tuple],  # List of (retrieved_ids, relevant_ids)
    k_values: List[int] = [1, 3, 5, 10]
) -> Dict[str, float]:
    """
    Evaluate retrieval across multiple queries and aggregate.
    
    Args:
        batch_results: List of (retrieved_ids, relevant_ids) tuples
        k_values: List of K values to compute metrics at
        
    Returns:
        Aggregated metrics (means) across all queries
    """
    if not batch_results:
        return {}
    
    all_metrics: Dict[str, List[float]] = {}
    
    for retrieved_ids, relevant_ids in batch_results:
        metrics = evaluate_retrieval(retrieved_ids, relevant_ids, k_values)
        for name, value in metrics.items():
            if name not in all_metrics:
                all_metrics[name] = []
            all_metrics[name].append(value)
    
    # Average each metric
    return {name: average(values) for name, values in all_metrics.items()}
