"""FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .routes import ingest, query, manage, diarization, chat, settings
from ..config import config

# Create FastAPI app
app = FastAPI(
    title="Aegis RAG",
    description="Offline Multimodal RAG System with Speaker Diarization",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Electron app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router, prefix="/api", tags=["Ingestion"])
app.include_router(query.router, prefix="/api", tags=["Query"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(manage.router, prefix="/api", tags=["Management"])
app.include_router(settings.router, prefix="/api", tags=["Settings"])
app.include_router(diarization.router, prefix="/api/voice", tags=["Speaker Diarization"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Aegis RAG",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# Serve static files if they exist (for development without Electron)
static_dir = Path(__file__).parent.parent.parent / "renderer" / "dist"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
