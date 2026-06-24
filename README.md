---
title: Aegis RAG
emoji: 🌌
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
short_description: Offline Multimodal RAG System
---
<p align="center">
  <h1 align="center">🌌 Aegis RAG</h1>
  <p align="center"><strong>Offline Multimodal RAG System</strong></p>
  <p align="center">
    <em>A fully offline Retrieval-Augmented Generation system for PDF, DOCX, CSV, Images, and Voice recordings</em>
  </p>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.109+-00C7B7?logo=fastapi&logoColor=white" />
  <img alt="Electron" src="https://img.shields.io/badge/Electron-Desktop-47848F?logo=electron&logoColor=white" />
  <img alt="React" src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white" />
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green" />
</p>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔒 **100% Offline** | All processing happens locally — no cloud, no internet required |
| 📄 **Multi-format Support** | Ingest PDF, DOCX, Images, and Audio recordings |
| 🎯 **Semantic Search** | Find relevant content using natural language queries |
| 💬 **RAG-powered Chat** | Get AI-powered answers with inline source citations |
| 🗣️ **Speaker Diarization** | Identify who said what in audio files with timestamps |
| 🖼️ **Image Understanding** | OCR + Vision model descriptions for visual content |
| 🏷️ **Logical Collections** | Organize documents with flexible metadata tags |
| 📊 **Retrieval Evaluation** | Built-in Recall@K and MRR metrics for quality assessment |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Aegis RAG Desktop App                              │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                    Electron + React Frontend                        │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                   │                                      │
│                            IPC / REST API                                │
│                                   ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                     FastAPI Backend (Python)                        │ │
│  │  ┌───────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │ │
│  │  │ Ingest    │  │   Query    │  │   Search   │  │  Diarization   │  │ │
│  │  │ Routes    │  │   Routes   │  │   Routes   │  │   Routes       │  │ │
│  │  └─────┬─────┘  └─────┬──────┘  └─────┬──────┘  └───────┬────────┘  │ │
│  └────────┼──────────────┼───────────────┼─────────────────┼───────────┘ │
│           ▼              ▼               ▼                 ▼             │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                         Core Modules                                │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────────┐  │ │
│  │  │ Processors │  │  Chunking  │  │ Embedding  │  │  Generation   │  │ │
│  │  │ PDF/DOCX/  │  │  Semantic  │  │   Ollama   │  │  LLM + Guard  │  │ │
│  │  │ Image/Voice│  │  Splitting │  │  nomic-    │  │  + Citations  │  │ │
│  │  └────────────┘  └────────────┘  │  embed     │  └───────────────┘  │ │
│  │                                  └──────┬─────┘                     │ │
│  └─────────────────────────────────────────┼───────────────────────────┘ │
│                                            ▼                             │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                         Vector Store                                │ │
│  │                    ChromaDB (Persistent)                            │ │
│  │              Cosine Similarity | Logical Collections                │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────-──────┘
```

> 📚 See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed technical documentation.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Vector Store** | ChromaDB (persistent, cosine similarity) |
| **Embeddings** | nomic-embed-text via Ollama |
| **LLM** | Mistral 7B via Ollama |
| **Vision** | LLaVA via Ollama |
| **OCR** | PaddleOCR (optional) |
| **Speech-to-Text** | Faster-Whisper (local) |
| **Speaker Diarization** | MFCC + Spectral Clustering |
| **Backend** | FastAPI + Uvicorn |
| **Frontend** | Electron + React + Vite + Tailwind CSS |

---

## 📋 Prerequisites

### 1. Install Ollama

```bash
# Linux / macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Windows — download the installer from:
# https://ollama.ai/download/windows
```

### 2. Pull Required Models (one-time, works offline after)

```bash
ollama pull nomic-embed-text    # Embeddings (~274MB)
ollama pull mistral:7b          # Main LLM (~4.1GB)
ollama pull llava               # Vision model (~4.7GB)
```

### 3. System Requirements

- **Python**: 3.10+
- **Node.js**: 18+
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 10GB+ for models

---

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/HXMAN76/Aegis-RAG.git
cd Aegis-RAG

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# OR: venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r requirements.txt

# Optional: Install OCR support
pip install -e ".[ocr]"

# Optional: Install Voice processing support
pip install -e ".[voice]"

# Install Node dependencies
npm install

# Run development mode
npm run dev
```

---

## 📁 Project Structure

```
Aegis RAG/
├── src/                        # Python backend
│   ├── api/                    # FastAPI application
│   │   ├── main.py             # App entry point
│   │   ├── models.py           # Pydantic schemas
│   │   └── routes/             # API endpoints
│   │       ├── ingest.py       # Document ingestion
│   │       ├── query.py        # RAG queries & search
│   │       ├── manage.py       # Collection management
│   │       └── diarization.py  # Speaker diarization
│   ├── processors/             # Document processors
│   │   ├── base.py             # Base processor & Chunk model
│   │   ├── pdf_processor.py    # PDF extraction
│   │   ├── docx_processor.py   # DOCX extraction
│   │   ├── csv_processor.py    # CSV/TSV extraction
│   │   ├── image_processor.py  # Image OCR + Vision
│   │   └── voice_processor.py  # Audio transcription + diarization
│   ├── chunking/               # Text chunking
│   │   └── chunker.py          # Semantic chunking strategies
│   ├── embedding/              # Embedding generation
│   │   └── embedder.py         # Ollama embeddings wrapper
│   ├── vectorstore/            # Vector database
│   │   └── chroma_store.py     # ChromaDB with logical collections
│   ├── retrieval/              # Semantic retrieval
│   │   └── retriever.py        # Query + context building
│   ├── generation/             # LLM generation
│   │   ├── llm.py              # Ollama LLM wrapper
│   │   ├── guardrails.py       # Response validation
│   │   └── citations.py        # Source citation engine
│   └── config.py               # Configuration settings
├── electron/                   # Electron main process
│   ├── main.js                 # Window management
│   ├── preload.js              # IPC bridge
│   └── python-backend.js       # Backend spawner
├── renderer/                   # React frontend (Vite)
│   ├── src/                    # React components
│   ├── tailwind.config.js      # Tailwind configuration
│   └── vite.config.js          # Vite configuration
├── tests/                      # Test suite
│   └── retrieval_metrics.py    # Recall@K, MRR metrics
├── data/                       # Local data storage
│   ├── chroma_db/              # Vector database
│   └── uploads/                # Uploaded files
├── models/                     # Cached model files
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Python project config
└── package.json                # Node.js config
```

---

## 🔌 API Reference

### Base URL: `http://localhost:8000/api`

### Document Ingestion

#### Upload and Ingest File
```http
POST /ingest/upload
Content-Type: multipart/form-data

file: <file>
collections: ["research", "project-x"]  # optional
```

#### Ingest by Path
```http
POST /ingest/path
Content-Type: application/json

{
  "file_path": "/path/to/document.pdf",
  "collections": ["research"]
}
```

### RAG Query

#### Ask a Question
```http
POST /query
Content-Type: application/json

{
  "query": "What are the key findings?",
  "top_k": 5,
  "doc_types": ["pdf", "docx"],
  "collections": ["research"]
}
```

**Response:**
```json
{
  "answer": "The key findings include...",
  "sources": [
    {
      "source_file": "report.pdf",
      "page": 5,
      "similarity": 0.89
    }
  ],
  "confidence": 0.85
}
```

#### Streaming Query
```http
POST /query/stream
```
Returns NDJSON stream with chunks, sources, and completion events.

### Semantic Search

```http
POST /search
Content-Type: application/json

{
  "query": "machine learning experiments",
  "top_k": 10
}
```

### Speaker Diarization

#### Diarize Uploaded Audio
```http
POST /voice/diarize/upload
Content-Type: multipart/form-data

file: <audio file>
language: en
num_speakers: 2  # optional, auto-detected if omitted
```

**Response:**
```json
{
  "success": true,
  "duration": 151.25,
  "speaker_count": 2,
  "speakers": ["Speaker 1", "Speaker 2"],
  "segments": [
    {
      "speaker": "Speaker 1",
      "start": 5.11,
      "end": 15.53,
      "text": "Welcome to the meeting...",
      "confidence": 1.0
    }
  ]
}
```

### Collection Management

```http
GET    /api/settings             # Get current runtime config
PATCH  /api/settings             # Update settings at runtime
GET    /collections              # List all collections
POST   /collections/{name}       # Create collection
DELETE /collections/{name}       # Delete collection
POST   /collections/{name}/add   # Add document to collection
GET    /stats                    # System statistics
```

---

## 📊 Retrieval Evaluation

Aegis RAG includes built-in metrics for evaluating retrieval quality:

```python
from tests.retrieval_metrics import recall_at_k, reciprocal_rank, average

# Recall@K: Did we find relevant documents in top-K?
recall = recall_at_k(
    retrieved_ids=["doc1", "doc2", "doc3"],
    relevant_ids={"doc2", "doc5"},
    k=3
)  # Returns 1 (found doc2 in top-3)

# MRR: How high did the first relevant document rank?
mrr = reciprocal_rank(
    retrieved_ids=["doc1", "doc2", "doc3"],
    relevant_ids={"doc2"}
)  # Returns 0.5 (doc2 is at position 2)
```

---

## 🎨 Desktop Application

Aegis RAG features a professional desktop interface designed for research workflows:

- **Three-pane layout**: Knowledge Explorer | Workspace | Source Context
- **Drag & drop ingestion**: Drop files directly from your file manager
- **Real-time streaming**: Watch responses generate token-by-token
- **Source highlighting**: Click citations to jump to original documents
- **Keyboard-first**: Ctrl+Enter to submit, extensive shortcuts

---

## 🔧 Configuration

Edit `src/config.py` or set environment variables:

| Setting | Default | Description |
|---------|---------|-------------|
| `EMBEDDING_MODEL` | `nomic-embed-text` | Ollama embedding model |
| `LLM_MODEL` | `mistral:7b` | Ollama LLM model |
| `VISION_MODEL` | `llava` | Ollama vision model |
| `CHUNK_SIZE` | `512` | Target chunk size (tokens) |
| `CHUNK_OVERLAP` | `50` | Chunk overlap (tokens) |
| `TOP_K_RESULTS` | `5` | Default retrieval count |
| `CHROMA_DIR` | `data/chroma_db` | Vector DB location |

---

## 🧪 Development

```bash
# Run backend only
uvicorn src.api.main:app --reload --port 8000

# Run frontend only
cd renderer && npm run dev

# Run full desktop app
npm run dev

# Run tests
pytest tests/ -v
```

---

## 📝 License

MIT License — see [LICENSE](./LICENSE) for details.

---

<p align="center">
  <strong>Built for researchers, lawyers, analysts, and engineers who need private, offline intelligence.</strong>
</p>
<p align="center">
  See <a href="./ARCHITECTURE.md">ARCHITECTURE.md</a> for the full data-flow and design documentation.
</p>
