"""Runtime settings endpoints — allows the frontend to read and update backend config."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from ...config import config

router = APIRouter()


class SettingsResponse(BaseModel):
    ollama_host: str
    llm_model: str
    vision_model: str
    embedding_model: str
    whisper_model: str
    chunk_size: int
    chunk_overlap: int
    top_k_results: int
    use_reranker: bool
    use_hybrid_search: bool


class SettingsUpdateRequest(BaseModel):
    ollama_host: Optional[str] = None
    llm_model: Optional[str] = None
    vision_model: Optional[str] = None
    embedding_model: Optional[str] = None
    whisper_model: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    top_k_results: Optional[int] = None
    use_reranker: Optional[bool] = None
    use_hybrid_search: Optional[bool] = None


@router.get("/settings", response_model=SettingsResponse)
async def get_settings():
    """Get current runtime configuration."""
    return SettingsResponse(
        ollama_host=config.OLLAMA_HOST,
        llm_model=config.LLM_MODEL,
        vision_model=config.VISION_MODEL,
        embedding_model=config.EMBEDDING_MODEL,
        whisper_model=config.WHISPER_MODEL,
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        top_k_results=config.TOP_K_RESULTS,
        use_reranker=config.USE_RERANKER,
        use_hybrid_search=config.USE_HYBRID_SEARCH,
    )


@router.patch("/settings", response_model=SettingsResponse)
async def update_settings(request: SettingsUpdateRequest):
    """
    Update runtime configuration.

    Changes take effect immediately for subsequent requests.
    Note: Changes are in-memory only and reset on server restart.
    Persist settings by editing .env or config.py.
    """
    if request.ollama_host is not None:
        config.OLLAMA_HOST = request.ollama_host
    if request.llm_model is not None:
        config.LLM_MODEL = request.llm_model
    if request.vision_model is not None:
        config.VISION_MODEL = request.vision_model
    if request.embedding_model is not None:
        config.EMBEDDING_MODEL = request.embedding_model
    if request.whisper_model is not None:
        config.WHISPER_MODEL = request.whisper_model
    if request.chunk_size is not None:
        config.CHUNK_SIZE = request.chunk_size
    if request.chunk_overlap is not None:
        config.CHUNK_OVERLAP = request.chunk_overlap
    if request.top_k_results is not None:
        config.TOP_K_RESULTS = request.top_k_results
    if request.use_reranker is not None:
        config.USE_RERANKER = request.use_reranker
    if request.use_hybrid_search is not None:
        config.USE_HYBRID_SEARCH = request.use_hybrid_search

    return await get_settings()
