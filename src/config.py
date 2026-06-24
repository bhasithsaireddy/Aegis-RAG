"""Aegis RAG - Offline Multimodal RAG System Configuration"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class Config:
    """Central configuration for Aegis RAG"""
    
    # Deployment Mode
    DEPLOYMENT_MODE: str = os.getenv("DEPLOYMENT_MODE", "local")
    
    # HF Inference API
    HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", "")
    HF_LLM_MODEL: str = os.getenv("HF_LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")

    # Paths
    BASE_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    DATA_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data")
    CHROMA_DIR: Path = field(default_factory=lambda: Path(os.getenv("CHROMA_DIR", "")) or Path(__file__).parent.parent / "data" / "chroma_db")
    UPLOADS_DIR: Path = field(default_factory=lambda: Path(os.getenv("UPLOADS_DIR", "")) or Path(__file__).parent.parent / "data" / "uploads")
    MODELS_DIR: Path = field(default_factory=lambda: Path(os.getenv("MODELS_DIR", "")) or Path(__file__).parent.parent / "models")
    CHAT_DB_PATH: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data" / "chat_history.db")
    
    # Chunking
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))       # tokens
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))  # tokens
    
    # Ollama
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "mistral:7b")
    VISION_MODEL: str = os.getenv("VISION_MODEL", "llava")
    # DeepSeek OCR uses the vision model (llava) for image understanding
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "llava")
    
    # Ollama Performance Tuning (RTX 4060 8GB Optimization)
    OLLAMA_OPTIONS: dict = field(default_factory=lambda: {
        "num_batch": 64,      # Reduce batch size for 8GB VRAM
        "num_gpu": 9,         # Limit GPU layers to prevent eviction loops
        "num_ctx": 2048,      # Context window
        # "flash_attn": True  # Uncomment if supported by installed Ollama version
    })
    
    # Vector Store
    COLLECTION_NAME: str = "aegis_rag_chunks"
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "5"))
    USE_RERANKER: bool = os.getenv("USE_RERANKER", "true").lower() == "true"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # Hybrid Search (BM25 + dense vector fusion)
    USE_HYBRID_SEARCH: bool = os.getenv("USE_HYBRID_SEARCH", "false").lower() == "true"
    HYBRID_ALPHA: float = 0.5  # Weight for dense results (1-alpha for BM25)
    
    # Chat History
    CHAT_CONTEXT_MESSAGES: int = 6  # Number of prior messages to inject into LLM prompt
    
    # Voice Processing
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")  # tiny, base, small, medium, large-v2
    
    # API
    API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Supported file types
    SUPPORTED_EXTENSIONS: List[str] = field(default_factory=lambda: [
        ".pdf", ".docx", ".doc",
        ".csv", ".tsv",
        ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif", ".gif",
        ".mp3", ".wav", ".m4a", ".ogg", ".flac"
    ])
    
    def __post_init__(self):
        """Ensure directories exist"""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        self.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        self.MODELS_DIR.mkdir(parents=True, exist_ok=True)


# Global config instance
config = Config()
