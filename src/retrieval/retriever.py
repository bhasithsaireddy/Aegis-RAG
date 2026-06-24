"""
Semantic retriever for RAG queries
"""

from typing import List, Dict, Any

from ..vectorstore import ChromaStore
from ..config import config
from .reranker import CrossEncoderReranker
from .hybrid import HybridRetriever, BM25


class Retriever:
    """
    Retrieve relevant chunks for RAG queries using vector similarity search.
    Optionally uses BM25 + dense hybrid retrieval (enable via USE_HYBRID_SEARCH).
    """

    def __init__(self, store: ChromaStore | None = None):
        """
        Initialize retriever.

        Args:
            store: ChromaStore instance (created if not provided)
        """
        self.store = store or ChromaStore()
        self.reranker = None
        if config.USE_RERANKER:
            self.reranker = CrossEncoderReranker(
                model_name=config.RERANKER_MODEL
            )

        # Optional hybrid retriever
        self._hybrid: HybridRetriever | None = None
        self._hybrid_indexed = False
        if config.USE_HYBRID_SEARCH:
            self._hybrid = HybridRetriever(
                dense_retriever=self.store,
                alpha=config.HYBRID_ALPHA
            )

    # ------------------------------------------------------------------
    # BM25 index management (only relevant when hybrid search is on)
    # ------------------------------------------------------------------

    def rebuild_bm25_index(self):
        """Re-index all stored documents into BM25 (call after bulk ingest)."""
        if self._hybrid is None:
            return
        all_results = self.store._collection.get(include=["documents", "metadatas"])
        docs = []
        for doc_id, content, meta in zip(
            all_results.get("ids", []),
            all_results.get("documents", []),
            all_results.get("metadatas", [])
        ):
            docs.append({"id": doc_id, "content": content, "metadata": meta})
        self._hybrid.index_corpus(docs)
        self._hybrid_indexed = True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        doc_types: List[str] | None = None,
        collections: List[str] | None = None,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: Search query
            top_k: Number of results to retrieve
            doc_types: Optional document-type filter
            collections: Optional logical collection filter
            min_similarity: Minimum similarity threshold (0–1)

        Returns:
            List of retrieved chunks with metadata and similarity score
        """
        if not query or not query.strip():
            return []

        top_k = top_k or config.TOP_K_RESULTS

        # ── Hybrid search path ────────────────────────────────────────
        if self._hybrid is not None:
            if not self._hybrid_indexed:
                self.rebuild_bm25_index()

            results = self._hybrid.search(
                query=query,
                top_k=top_k * 3 if self.reranker else top_k,
                dense_k=top_k * 3,
                sparse_k=top_k * 3,
                doc_types=doc_types,
                collections=collections,
            )
        else:
            # ── Dense-only path (default) ─────────────────────────────
            # Fetch more candidates for re-ranking (3× top_k)
            fetch_k = top_k * 3 if self.reranker else top_k

            results = self.store.query(
                query_text=query,
                n_results=fetch_k,
                doc_types=doc_types,
                collections=collections
            )

        # Defensive: ensure list format
        if not isinstance(results, list):
            return []

        # ── Re-rank results ───────────────────────────────────────────
        if self.reranker and results:
            results = self.reranker.rerank(
                query=query,
                candidates=results,
                top_k=top_k
            )
        else:
            results = results[:top_k]

        # Filter by similarity threshold
        if min_similarity > 0.0:
            results = [
                r for r in results
                if r.get("similarity") is not None
                and r["similarity"] >= min_similarity
            ]

        return results

    def get_context(
        self,
        query: str,
        top_k: int | None = None,
        doc_types: List[str] | None = None,
        collections: List[str] | None = None,
        max_tokens: int = 2000
    ) -> str:
        """
        Construct formatted context for LLM prompt.

        Args:
            query: Search query
            top_k: Number of chunks to retrieve
            doc_types: Optional document-type filter
            collections: Optional logical collection filter
            max_tokens: Maximum tokens allowed in context (soft limit)

        Returns:
            Formatted context string
        """
        results = self.retrieve(
            query=query,
            top_k=top_k,
            doc_types=doc_types,
            collections=collections
        )

        if not results:
            return ""

        context_parts: List[str] = []
        token_count = 0

        for i, result in enumerate(results, 1):
            content = result.get("content", "")
            if not content:
                continue

            metadata = result.get("metadata", {})

            # ---- Source formatting ----
            source_info = f"[Source {i}: {metadata.get('source_file', 'Unknown')}"
            if metadata.get("page") is not None:
                source_info += f", Page {metadata['page']}"
            if metadata.get("speaker"):
                source_info += f", Speaker: {metadata['speaker']}"
            if metadata.get("timestamp_start") is not None:
                source_info += f", Time: {metadata['timestamp_start']:.1f}s"
            source_info += "]"

            block = f"{source_info}\n{content}"

            # Soft token control (approximate)
            token_count += len(block.split())
            if token_count > max_tokens:
                break

            context_parts.append(block)

        return "\n\n---\n\n".join(context_parts)

    def get_sources(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract citation-friendly source metadata from retrieval results.

        Args:
            results: Retrieval results

        Returns:
            List of source citation objects
        """
        sources: List[Dict[str, Any]] = []

        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})

            source: Dict[str, Any] = {
                "index": i,
                "source_file": metadata.get("source_file"),
                "doc_type": metadata.get("doc_type"),
                "document_id": metadata.get("document_id"),
                "similarity": result.get("similarity", 0.0)
            }

            # Optional location metadata
            if metadata.get("page") is not None:
                source["page"] = metadata["page"]

            if metadata.get("timestamp_start") is not None:
                source["timestamp"] = {
                    "start": metadata["timestamp_start"],
                    "end": metadata.get("timestamp_end")
                }

            if metadata.get("speaker"):
                source["speaker"] = metadata["speaker"]

            sources.append(source)

        return sources
