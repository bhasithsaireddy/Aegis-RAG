# Aegis RAG — Architecture

## System Overview

Aegis RAG is a fully-offline desktop application for multimodal Retrieval-Augmented Generation (RAG).
All AI processing happens locally — no data leaves your machine.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Aegis RAG Desktop App                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │              Electron Shell (electron/main.js)                      ││
│  │   Spawns Python backend · Manages window · IPC bridge               ││
│  └────────────────────────┬────────────────────────────────────────────┘│
│                           │ loads                                        │
│  ┌────────────────────────▼────────────────────────────────────────────┐│
│  │              React + Vite Frontend (renderer/)                      ││
│  │   Dashboard · QueryWorkspace · CollectionsManager · SettingsView    ││
│  └────────────────────────┬────────────────────────────────────────────┘│
│                           │ HTTP / NDJSON streaming                      │
│  ┌────────────────────────▼────────────────────────────────────────────┐│
│  │                  FastAPI Backend (src/api/)                         ││
│  │  /ingest  /query  /query/stream  /search  /collections  /settings  ││
│  │  /voice/diarize  /chat/sessions  /models/status  /stats            ││
│  └──────────────────────────────────────────────────────────────────── ┘│
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Ingest Pipeline

```
File Upload (PDF / DOCX / CSV / Image / Audio)
        │
        ▼
  Processor (src/processors/)
  ├── PDFProcessor     — PyMuPDF + OCR fallback (LLaVA via Ollama)
  ├── DOCXProcessor    — python-docx, preserves headings + tables
  ├── CSVProcessor     — row-based chunking with header context
  ├── ImageProcessor   — OCR + visual description via LLaVA
  └── VoiceProcessor   — Faster-Whisper transcription + MFCC speaker diarization
        │
        ▼
  Chunker (src/chunking/chunker.py)
  Sentence-aware sliding window with configurable size + overlap (tokens)
        │
        ▼
  Embedder (src/embedding/embedder.py)
  nomic-embed-text via Ollama → List[float]
        │
        ▼
  ChromaStore (src/vectorstore/chroma_store.py)
  Single physical ChromaDB collection + logical collections via metadata
```

---

## Query Pipeline

```
User Question
        │
        ▼
  Embedder → query vector
        │
        ▼
  Retriever (src/retrieval/retriever.py)
  ├── Dense path (default): ChromaDB cosine similarity
  └── Hybrid path (opt-in): BM25 sparse + Dense → RRF fusion
        │
        ▼
  CrossEncoderReranker (src/retrieval/reranker.py)
  sentence-transformers cross-encoder/ms-marco-MiniLM-L-6-v2
  (LLM fallback if sentence-transformers unavailable)
        │
        ▼
  CitationEngine.create_context_with_sources()
  Formats [Source N] markers + builds source list
        │
        ▼
  LLM (src/generation/llm.py)
  Mistral:7b via Ollama  ·  Multi-turn context injected from SQLite history
        │
        ▼
  Guardrails (src/generation/guardrails.py)
  Confidence scoring + uncertainty detection
        │
        ▼
  Response + Citations → Frontend
```

---

## Speaker Diarization Pipeline

```
Audio File
   │
   ├─ Faster-Whisper → timestamped transcript segments
   │
   ├─ librosa MFCC extraction per segment
   │   (20 coefficients + delta + delta² = 240-dim embedding)
   │
   ├─ Silhouette-score speaker count estimation
   │
   ├─ SpectralClustering (fallback: AgglomerativeClustering)
   │
   └─ Segment merging → {speaker, start, end, text}[]
```

---

## Data Storage

| Store | Technology | Purpose |
|-------|------------|---------|
| Vector DB | ChromaDB (persistent) | Chunk embeddings + metadata |
| Chat History | SQLite (`data/chat_history.db`) | Session + message persistence |
| Collections | JSON sidecar (`data/chroma_db/collections.json`) | Named logical collections |
| Uploads | Filesystem (`data/uploads/`) | UUID-prefixed raw files |
| Models | Filesystem (`models/`) | Whisper model cache |

---

## Key Design Decisions

- **Single ChromaDB collection** with metadata-based logical collections avoids Chroma's per-collection overhead and enables cross-collection search.
- **Hybrid search is opt-in** (`USE_HYBRID_SEARCH=true`) because BM25 requires in-memory indexing of the full corpus on startup.
- **Singletons via `src/dependencies.py`** ensure only one `ChromaStore` / `PersistentClient` is open at a time, avoiding SQLite WAL conflicts under concurrent requests.
- **Multi-turn context** is injected from SQLite history into the LLM prompt (last `CHAT_CONTEXT_MESSAGES` turns), keeping the FastAPI endpoint stateless while enabling conversational follow-ups.
