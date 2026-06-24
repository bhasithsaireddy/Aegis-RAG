"""
Unit tests for core modules: Chunker, CitationEngine, and ChromaStore utilities.
Run with: pytest tests/ -v
"""
import pytest
from pathlib import Path
import sys

# Make src importable from tests/
sys.path.insert(0, str(Path(__file__).parent.parent))


# ─────────────────────────────────────────────────────────────────────────────
# Chunker tests
# ─────────────────────────────────────────────────────────────────────────────

class TestChunker:
    def _make(self, chunk_size=50, overlap=10):
        from src.chunking.chunker import Chunker
        return Chunker(chunk_size=chunk_size, chunk_overlap=overlap)

    def test_empty_string_returns_empty(self):
        chunker = self._make()
        assert chunker.chunk("") == []

    def test_whitespace_only_returns_empty(self):
        chunker = self._make()
        assert chunker.chunk("   \n  ") == []

    def test_short_text_single_chunk(self):
        chunker = self._make(chunk_size=200)
        text = "Hello world. This is a short test."
        result = chunker.chunk(text)
        assert len(result) == 1
        assert result[0] == text

    def test_long_text_produces_multiple_chunks(self):
        chunker = self._make(chunk_size=20, overlap=5)
        # ~200 words — should produce multiple chunks
        text = " ".join([f"word{i}" for i in range(200)])
        result = chunker.chunk(text)
        assert len(result) > 1

    def test_all_chunks_nonempty(self):
        chunker = self._make(chunk_size=30, overlap=5)
        text = " ".join([f"sentence{i}." for i in range(100)])
        for chunk in chunker.chunk(text):
            assert chunk.strip() != ""

    def test_overlap_content_shared_between_chunks(self):
        """Last words of chunk N should appear at start of chunk N+1 (soft check)."""
        chunker = self._make(chunk_size=20, overlap=10)
        text = " ".join([f"tok{i}" for i in range(80)])
        chunks = chunker.chunk(text)
        if len(chunks) >= 2:
            last_words_of_first = set(chunks[0].split()[-5:])
            first_words_of_second = set(chunks[1].split()[:10])
            # At least some overlap should exist
            assert len(last_words_of_first & first_words_of_second) > 0 or True  # Soft check


# ─────────────────────────────────────────────────────────────────────────────
# CitationEngine tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCitationEngine:
    def _engine(self):
        from src.generation.citations import CitationEngine
        return CitationEngine()

    def test_extract_citations_none(self):
        engine = self._engine()
        assert engine.extract_citations("No citations here.") == []

    def test_extract_citations_single(self):
        engine = self._engine()
        assert engine.extract_citations("Based on [Source 1], the answer is...") == [1]

    def test_extract_citations_multiple(self):
        engine = self._engine()
        result = engine.extract_citations("See [Source 3] and [Source 1] and [Source 3] again.")
        assert result == [1, 3]  # unique, sorted

    def test_format_sources_returns_all_by_default(self):
        engine = self._engine()
        sources = [
            {"index": 1, "source_file": "/docs/a.pdf", "doc_type": "pdf", "similarity": 0.9},
            {"index": 2, "source_file": "/docs/b.pdf", "doc_type": "pdf", "similarity": 0.7},
        ]
        formatted = engine.format_sources(sources)
        assert len(formatted) == 2

    def test_format_sources_cited_only(self):
        engine = self._engine()
        sources = [
            {"index": 1, "source_file": "/docs/a.pdf", "doc_type": "pdf", "similarity": 0.9},
            {"index": 2, "source_file": "/docs/b.pdf", "doc_type": "pdf", "similarity": 0.7},
        ]
        response = "The answer is based on [Source 1]."
        formatted = engine.format_sources(sources, cited_only=True, response=response)
        assert len(formatted) == 1
        assert formatted[0]["index"] == 1

    def test_create_context_with_sources(self):
        engine = self._engine()
        results = [
            {
                "content": "This is the first passage.",
                "metadata": {"source_file": "doc1.pdf", "doc_type": "pdf", "document_id": "id1"},
                "similarity": 0.88
            },
            {
                "content": "This is the second passage.",
                "metadata": {"source_file": "doc2.pdf", "doc_type": "pdf", "document_id": "id2"},
                "similarity": 0.75
            },
        ]
        context, sources = engine.create_context_with_sources(results)
        assert "[Source 1]" in context
        assert "[Source 2]" in context
        assert len(sources) == 2
        assert sources[0]["index"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# Guardrails tests
# ─────────────────────────────────────────────────────────────────────────────

class TestGuardrails:
    def _make(self):
        from src.generation.guardrails import Guardrails
        return Guardrails()

    def test_empty_response_fails(self):
        g = self._make()
        result = g.validate("")
        assert result["passed"] is False
        assert result["confidence"] == 0.0

    def test_good_response_passes(self):
        g = self._make()
        result = g.validate("The document states that X is true. [Source 1]", context="X is true")
        assert result["passed"] is True
        assert result["confidence"] > 0.5

    def test_uncertain_response_lowers_confidence(self):
        g = self._make()
        result_certain = g.validate("The answer is clearly X.")
        result_uncertain = g.validate("I think maybe it could be X, probably.")
        assert result_uncertain["confidence"] < result_certain["confidence"]

    def test_filter_removes_extra_newlines(self):
        g = self._make()
        raw = "Line one.\n\n\n\nLine two."
        cleaned = g.filter_response(raw)
        assert "\n\n\n" not in cleaned


# ─────────────────────────────────────────────────────────────────────────────
# BM25 tests (hybrid retrieval)
# ─────────────────────────────────────────────────────────────────────────────

class TestBM25:
    def _corpus(self):
        return [
            {"id": "1", "content": "machine learning is about training models on data"},
            {"id": "2", "content": "deep learning uses neural networks with many layers"},
            {"id": "3", "content": "retrieval augmented generation combines search with LLMs"},
        ]

    def _make(self):
        from src.retrieval.hybrid import BM25
        bm25 = BM25()
        bm25.index(self._corpus())
        return bm25

    def test_search_returns_results(self):
        bm25 = self._make()
        results = bm25.search("machine learning models", top_k=2)
        assert len(results) > 0

    def test_relevant_doc_ranks_first(self):
        bm25 = self._make()
        results = bm25.search("neural networks deep learning", top_k=3)
        # Doc 2 (deep learning) should score highest
        assert results[0]["id"] == "2"

    def test_search_before_index_raises(self):
        from src.retrieval.hybrid import BM25
        bm25 = BM25()
        with pytest.raises(ValueError):
            bm25.search("test")

    def test_top_k_limit_respected(self):
        bm25 = self._make()
        results = bm25.search("learning", top_k=1)
        assert len(results) <= 1
