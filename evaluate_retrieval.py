#!/usr/bin/env python3
"""
Aegis RAG Retrieval System - Comprehensive Evaluation Suite

This script tests the entire RAG pipeline and produces showcase-worthy metrics.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Set

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.embedding.embedder import Embedder
from src.vectorstore.chroma_store import ChromaStore
from src.retrieval import Retriever, BM25, HybridRetriever, MMRRetriever
from src.retrieval.mmr import mmr_select
from tests.retrieval_metrics import (
    evaluate_retrieval, evaluate_batch,
    recall_at_k, precision_at_k, ndcg_at_k_binary, 
    reciprocal_rank, average_precision
)


# =============================================================================
# TEST DATA - Synthetic corpus with known relevance
# =============================================================================

TEST_CORPUS = [
    # Machine Learning cluster
    {
        "id": "ml1",
        "content": "Machine learning is a subset of artificial intelligence that enables systems to learn from data. It includes supervised learning, unsupervised learning, and reinforcement learning approaches.",
        "category": "machine_learning",
        "relevance_queries": ["machine learning", "AI algorithms", "supervised learning"]
    },
    {
        "id": "ml2", 
        "content": "Deep learning uses neural networks with multiple layers to extract features from data. Convolutional neural networks are used for image recognition, while recurrent networks handle sequential data.",
        "category": "machine_learning",
        "relevance_queries": ["deep learning", "neural networks", "image recognition"]
    },
    {
        "id": "ml3",
        "content": "Gradient descent is an optimization algorithm used to minimize loss functions in machine learning. Variants include stochastic gradient descent and Adam optimizer.",
        "category": "machine_learning",
        "relevance_queries": ["machine learning", "optimization", "gradient descent"]
    },
    
    # Natural Language Processing cluster
    {
        "id": "nlp1",
        "content": "Natural language processing enables computers to understand human language. Key tasks include sentiment analysis, named entity recognition, and machine translation.",
        "category": "nlp",
        "relevance_queries": ["NLP", "natural language", "text analysis"]
    },
    {
        "id": "nlp2",
        "content": "Transformer models revolutionized NLP with self-attention mechanisms. BERT and GPT are examples of transformer-based language models that achieve state-of-the-art results.",
        "category": "nlp",
        "relevance_queries": ["transformers", "BERT", "language models"]
    },
    {
        "id": "nlp3",
        "content": "Word embeddings like Word2Vec and GloVe represent words as dense vectors in continuous space. These embeddings capture semantic relationships between words.",
        "category": "nlp",
        "relevance_queries": ["word embeddings", "NLP", "semantic similarity"]
    },
    
    # RAG and Retrieval cluster
    {
        "id": "rag1",
        "content": "Retrieval-Augmented Generation combines retrieval systems with generative models. The retriever finds relevant documents that the generator uses to produce accurate responses.",
        "category": "rag",
        "relevance_queries": ["RAG", "retrieval", "document retrieval"]
    },
    {
        "id": "rag2",
        "content": "Vector databases store embeddings for efficient similarity search. Popular options include Chroma, Pinecone, and Weaviate, which use approximate nearest neighbor algorithms.",
        "category": "rag",
        "relevance_queries": ["vector database", "embeddings", "similarity search"]
    },
    {
        "id": "rag3",
        "content": "Chunking strategies affect retrieval quality. Fixed-size chunks, semantic chunking, and sentence-based splitting each have trade-offs in terms of context preservation.",
        "category": "rag",
        "relevance_queries": ["chunking", "document processing", "RAG"]
    },
    
    # Unrelated documents (for testing precision)
    {
        "id": "other1",
        "content": "The Mediterranean diet emphasizes fruits, vegetables, whole grains, and olive oil. Studies show it reduces cardiovascular disease risk and promotes longevity.",
        "category": "health",
        "relevance_queries": ["diet", "nutrition", "health"]
    },
    {
        "id": "other2",
        "content": "Classical music originated in Western culture during the 18th century. Composers like Mozart and Beethoven created symphonies that remain influential today.",
        "category": "music",
        "relevance_queries": ["classical music", "Mozart", "symphony"]
    },
    {
        "id": "other3",
        "content": "The Amazon rainforest produces 20% of the world's oxygen. Deforestation threatens biodiversity and contributes to climate change.",
        "category": "environment",
        "relevance_queries": ["rainforest", "environment", "climate"]
    },
]

# Test queries with known relevant documents
TEST_QUERIES = [
    {
        "query": "What is machine learning and how does it work?",
        "relevant_ids": {"ml1", "ml2", "ml3"},
        "category": "machine_learning"
    },
    {
        "query": "Explain neural networks and deep learning architectures",
        "relevant_ids": {"ml2", "ml1"},
        "category": "machine_learning"
    },
    {
        "query": "How do transformers and BERT models process language?",
        "relevant_ids": {"nlp2", "nlp1"},
        "category": "nlp"
    },
    {
        "query": "What are word embeddings and how do they work?",
        "relevant_ids": {"nlp3", "nlp2"},
        "category": "nlp"
    },
    {
        "query": "How does RAG retrieval augmented generation work?",
        "relevant_ids": {"rag1", "rag2", "rag3"},
        "category": "rag"
    },
    {
        "query": "Vector database for storing embeddings and similarity search",
        "relevant_ids": {"rag2", "rag1"},
        "category": "rag"
    },
    {
        "query": "Optimization algorithms for training neural networks",
        "relevant_ids": {"ml3", "ml2"},
        "category": "machine_learning"
    },
    {
        "query": "NLP tasks like sentiment analysis and named entity recognition",
        "relevant_ids": {"nlp1", "nlp2"},
        "category": "nlp"
    },
]


def print_header(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_metric(name: str, value: float, indent: int = 2):
    bar_length = int(value * 20)
    bar = "█" * bar_length + "░" * (20 - bar_length)
    print(f"{' ' * indent}{name:20} {bar} {value:.3f}")


class EvaluationSuite:
    def __init__(self):
        self.embedder = Embedder()
        self.store = None
        self.retriever = None
        self.bm25 = BM25()
        self.results = {}
        
    def setup(self):
        """Initialize components and ingest test corpus"""
        print_header("Setting Up Test Environment")
        
        # Use temporary collection for testing
        import tempfile
        self.temp_dir = Path(tempfile.mkdtemp())
        
        self.store = ChromaStore(
            persist_directory=self.temp_dir,
            collection_name="aegis-rag_eval_test"
        )
        self.retriever = Retriever(self.store)
        
        print(f"  📁 Using temp directory: {self.temp_dir}")
        print(f"  📊 Corpus size: {len(TEST_CORPUS)} documents")
        print(f"  🔍 Test queries: {len(TEST_QUERIES)}")
        
        # Ingest test corpus
        print("\n  Ingesting test corpus...")
        from src.processors.base import Chunk
        
        chunks = []
        for doc in TEST_CORPUS:
            chunks.append(Chunk(
                content=doc["content"],
                document_id=doc["id"],
                doc_type="test",
                source_file=f"{doc['id']}.txt",
                metadata={"category": doc["category"]}
            ))
        
        self.store.add_chunks(chunks)
        print(f"  ✅ Ingested {len(chunks)} chunks")
        
        # Index for BM25
        print("  Indexing for BM25...")
        bm25_docs = [{"id": d["id"], "content": d["content"]} for d in TEST_CORPUS]
        self.bm25.index(bm25_docs)
        print("  ✅ BM25 indexed")
        
    def evaluate_dense_retrieval(self) -> Dict[str, float]:
        """Evaluate dense (vector) retrieval"""
        print_header("Dense Retrieval Evaluation")
        
        batch_results = []
        
        for tq in TEST_QUERIES:
            results = self.retriever.retrieve(tq["query"], top_k=5)
            retrieved_ids = [r["metadata"].get("document_id", r.get("id", "")) for r in results]
            batch_results.append((retrieved_ids, tq["relevant_ids"]))
            
            # Show individual query results
            print(f"\n  Query: \"{tq['query'][:50]}...\"")
            print(f"  Relevant: {tq['relevant_ids']}")
            print(f"  Retrieved: {retrieved_ids[:5]}")
        
        # Aggregate metrics
        metrics = evaluate_batch(batch_results, k_values=[1, 3, 5])
        
        print("\n" + "-" * 50)
        print("  📊 Dense Retrieval Metrics (averaged):")
        print("-" * 50)
        
        for name, value in sorted(metrics.items()):
            print_metric(name, value, indent=4)
        
        self.results["dense"] = metrics
        return metrics
    
    def evaluate_bm25_retrieval(self) -> Dict[str, float]:
        """Evaluate BM25 sparse retrieval"""
        print_header("BM25 Sparse Retrieval Evaluation")
        
        batch_results = []
        
        for tq in TEST_QUERIES:
            results = self.bm25.search(tq["query"], top_k=5)
            retrieved_ids = [r["id"] for r in results]
            batch_results.append((retrieved_ids, tq["relevant_ids"]))
        
        metrics = evaluate_batch(batch_results, k_values=[1, 3, 5])
        
        print("  📊 BM25 Retrieval Metrics (averaged):")
        print("-" * 50)
        
        for name, value in sorted(metrics.items()):
            print_metric(name, value, indent=4)
        
        self.results["bm25"] = metrics
        return metrics
    
    def evaluate_hybrid_retrieval(self) -> Dict[str, float]:
        """Evaluate hybrid (dense + BM25) retrieval"""
        print_header("Hybrid Retrieval Evaluation (Dense + BM25)")
        
        hybrid = HybridRetriever(self.retriever, self.bm25, alpha=0.6)
        hybrid._corpus_indexed = True  # Already indexed
        
        batch_results = []
        
        for tq in TEST_QUERIES:
            results = hybrid.search(tq["query"], top_k=5, dense_k=10, sparse_k=10)
            retrieved_ids = [r.get("metadata", {}).get("document_id", r.get("id", "")) for r in results]
            batch_results.append((retrieved_ids, tq["relevant_ids"]))
        
        metrics = evaluate_batch(batch_results, k_values=[1, 3, 5])
        
        print("  📊 Hybrid Retrieval Metrics (averaged):")
        print("-" * 50)
        
        for name, value in sorted(metrics.items()):
            print_metric(name, value, indent=4)
        
        self.results["hybrid"] = metrics
        return metrics
    
    def evaluate_mmr_retrieval(self) -> Dict[str, float]:
        """Evaluate MMR (diverse) retrieval"""
        print_header("MMR Diverse Retrieval Evaluation")
        
        mmr_retriever = MMRRetriever(self.retriever, self.embedder, lambda_param=0.7)
        
        batch_results = []
        
        for tq in TEST_QUERIES:
            results = mmr_retriever.retrieve(tq["query"], top_k=5, fetch_k=10)
            retrieved_ids = [r.get("metadata", {}).get("document_id", r.get("id", "")) for r in results]
            batch_results.append((retrieved_ids, tq["relevant_ids"]))
        
        metrics = evaluate_batch(batch_results, k_values=[1, 3, 5])
        
        print("  📊 MMR Retrieval Metrics (averaged):")
        print("-" * 50)
        
        for name, value in sorted(metrics.items()):
            print_metric(name, value, indent=4)
        
        self.results["mmr"] = metrics
        return metrics
    
    def generate_report(self):
        """Generate final comparison report"""
        print_header("Aegis RAG Retrieval Evaluation Report")
        
        print(f"\n  📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  📊 Corpus: {len(TEST_CORPUS)} documents")
        print(f"  🔍 Queries: {len(TEST_QUERIES)} test queries")
        print(f"  🧠 Embedding: nomic-embed-text (768 dim)")
        
        # Comparison table
        print("\n" + "=" * 70)
        print("  📈 Method Comparison (Key Metrics)")
        print("=" * 70)
        
        methods = ["dense", "bm25", "hybrid", "mmr"]
        key_metrics = ["mrr", "recall@3", "precision@3", "ndcg@3"]
        
        # Header
        print(f"\n  {'Metric':<20}", end="")
        for method in methods:
            print(f"{method.upper():<12}", end="")
        print()
        print("  " + "-" * 68)
        
        # Rows
        for metric in key_metrics:
            print(f"  {metric:<20}", end="")
            for method in methods:
                if method in self.results and metric in self.results[method]:
                    value = self.results[method][metric]
                    print(f"{value:<12.3f}", end="")
                else:
                    print(f"{'N/A':<12}", end="")
            print()
        
        # Best results
        print("\n" + "=" * 70)
        print("  🏆 Best Results")
        print("=" * 70)
        
        for metric in key_metrics:
            best_method = None
            best_value = -1
            for method in methods:
                if method in self.results and metric in self.results[method]:
                    if self.results[method][metric] > best_value:
                        best_value = self.results[method][metric]
                        best_method = method
            if best_method:
                print(f"  {metric:<15} → {best_method.upper():<10} ({best_value:.3f})")
        
        # Save results
        report_path = Path("evaluation_results.json")
        with open(report_path, "w") as f:
            json.dump({
                "date": datetime.now().isoformat(),
                "corpus_size": len(TEST_CORPUS),
                "num_queries": len(TEST_QUERIES),
                "results": self.results
            }, f, indent=2)
        
        print(f"\n  💾 Results saved to: {report_path}")
        
    def cleanup(self):
        """Clean up temp directory"""
        import shutil
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            print(f"\n  🧹 Cleaned up temp directory")


def main():
    print("\n" + "🌌" * 35)
    print("      Aegis RAG - Advanced Retrieval Evaluation Suite")
    print("🌌" * 35)
    
    suite = EvaluationSuite()
    
    try:
        suite.setup()
        suite.evaluate_dense_retrieval()
        suite.evaluate_bm25_retrieval()
        suite.evaluate_hybrid_retrieval()
        suite.evaluate_mmr_retrieval()
        suite.generate_report()
    finally:
        suite.cleanup()
    
    print("\n" + "=" * 70)
    print("  ✅ Evaluation complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
