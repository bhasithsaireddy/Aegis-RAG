"""
Shared singletons for FastAPI dependency injection.

Using a single ChromaStore instance prevents multiple PersistentClient
connections from opening against the same SQLite WAL file simultaneously,
which can cause file-locking errors under concurrent requests.
"""

from .vectorstore import ChromaStore
from .retrieval import Retriever

# ── Module-level singletons ──────────────────────────────────────────────────
_store: ChromaStore | None = None
_retriever: Retriever | None = None
_llm = None


def get_store() -> ChromaStore:
    """Return the shared ChromaStore instance (lazy init)."""
    global _store
    if _store is None:
        _store = ChromaStore()
    return _store


def get_retriever() -> Retriever:
    """Return the shared Retriever instance (lazy init)."""
    global _retriever
    if _retriever is None:
        _retriever = Retriever(get_store())
    return _retriever

def get_llm():
    """Return the LLM instance (HFInferenceLLM if cloud else LLM)."""
    global _llm
    if _llm is None:
        from .config import config
        if config.DEPLOYMENT_MODE == "cloud":
            from .generation.llm_cloud import HFInferenceLLM
            _llm = HFInferenceLLM()
        else:
            from .generation.llm import LLM
            _llm = LLM()
    return _llm
