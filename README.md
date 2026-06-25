# 🛡️ Aegis — Intelligent Multimodal RAG System

Aegis is a production-grade, privacy-first **Retrieval-Augmented Generation (RAG)** system that transforms your unstructured documents — PDFs, Word files, spreadsheets, images, and audio recordings — into a searchable, conversational knowledge base. Ask questions in natural language and receive accurate, source-cited answers grounded entirely in your own data.

Designed to run **fully offline** on local hardware for maximum data privacy, or deploy seamlessly to the **cloud** (Vercel + Render) for global accessibility.

---

## 📑 Table of Contents

- [Architecture Overview](#-architecture-overview)
- [Complete RAG Pipeline](#-complete-rag-pipeline)
  - [Stage 1: Document Ingestion](#stage-1-document-ingestion--preprocessing)
  - [Stage 2: Chunking](#stage-2-semantic-chunking)
  - [Stage 3: Embedding](#stage-3-embedding-generation)
  - [Stage 4: Vector Storage](#stage-4-vector-storage)
  - [Stage 5: Retrieval](#stage-5-retrieval)
  - [Stage 6: Generation](#stage-6-llm-generation--response)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Deployment](#-deployment)
- [Local Development](#-local-development)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AEGIS ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────┐   ┌────────────┐   ┌──────────┐   ┌──────────────┐ │
│  │  React UI │──▶│  FastAPI   │──▶│ Retriever│──▶│  ChromaDB    │ │
│  │  (Vite)   │   │  Backend   │   │ + Rerank │   │  VectorStore │ │
│  └───────────┘   └─────┬──────┘   └──────────┘   └──────────────┘ │
│                        │                                            │
│                        ▼                                            │
│               ┌────────────────┐                                    │
│               │   LLM Engine   │                                    │
│               │  Ollama (local)│                                    │
│               │  Groq  (cloud) │                                    │
│               └────────────────┘                                    │
│                                                                     │
│  INGESTION PIPELINE                                                 │
│  ┌─────┐ ┌──────┐ ┌─────┐ ┌───────┐ ┌───────┐                    │
│  │ PDF │ │ DOCX │ │ CSV │ │ Image │ │ Audio │                    │
│  └──┬──┘ └──┬───┘ └──┬──┘ └───┬───┘ └───┬───┘                    │
│     └────────┴────────┴────────┴─────────┘                         │
│                       │                                             │
│              ┌────────▼────────┐                                    │
│              │   Processors    │                                    │
│              │ + OCR + Whisper │                                    │
│              └────────┬────────┘                                    │
│                       ▼                                             │
│              ┌─────────────────┐    ┌──────────────┐               │
│              │  Chunker        │──▶ │  Embedder    │               │
│              │  (sentence-aware)│    │  (nomic/ST)  │               │
│              └─────────────────┘    └──────┬───────┘               │
│                                            ▼                        │
│                                    ┌──────────────┐                │
│                                    │   ChromaDB   │                │
│                                    └──────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Complete RAG Pipeline

### Stage 1: Document Ingestion & Preprocessing

When a user uploads a file, Aegis automatically detects the file type and routes it to the appropriate **processor**. Each processor is a specialized class that inherits from `BaseProcessor` and implements a `process()` method that returns a list of `Chunk` objects.

| File Type | Processor | Library | What It Extracts |
|---|---|---|---|
| `.pdf` | `PDFProcessor` | **PyMuPDF** (`fitz`) | Native text with layout, tables (converted to Markdown), embedded images. For scanned/image-only PDFs, falls back to OCR (DeepSeek local or Gemini API cloud). |
| `.docx` `.doc` | `DOCXProcessor` | **python-docx** | Section/heading-aware text, tables to Markdown, embedded images via OCR, hyperlinks, and style metadata. |
| `.csv` `.tsv` | `CSVProcessor` | Python `csv` module | Schema detection (column names + types), row-based chunking with column headers preserved, and a statistics summary chunk. |
| `.png` `.jpg` `.jpeg` `.webp` `.bmp` `.tiff` `.gif` | `ImageProcessor` | **DeepSeek OCR** (local) / **Gemini OCR** (cloud) | OCR text extraction, visual scene descriptions, and table/chart detection from images. |
| `.mp3` `.wav` `.m4a` `.ogg` `.flac` | `EnhancedVoiceProcessor` | **Faster-Whisper** (local) / **Groq Whisper** (cloud) + **Librosa** | Speech-to-text transcription, MFCC-based speaker diarization (identifies who is speaking), timestamped segments, and automatic speaker count detection via silhouette scoring. |

#### OCR Engine: DeepSeek Vision

For scanned documents and images, Aegis automatically adapts based on the environment:
- **Local Mode**: Uses a **DeepSeek/LLaVA vision model** via Ollama. Runs entirely offline — no data ever leaves your machine.
- **Cloud Mode**: Uses the **Gemini 1.5 Flash API** for blazing fast, highly accurate multimodal extraction.
Both modes extract raw text, tables (as Markdown), and generate visual descriptions of charts/scenes.

#### Voice Processing Pipeline

The `EnhancedVoiceProcessor` implements a sophisticated audio analysis pipeline:
1. **Transcription**: Converts audio to text with word-level timestamps using **Faster-Whisper** (local GPU) or **Groq Whisper API** (cloud).
2. **Feature Extraction**: Librosa extracts MFCC (Mel-Frequency Cepstral Coefficients) audio features per segment
3. **Speaker Clustering**: Spectral Clustering or Agglomerative Clustering groups segments by voice similarity
4. **Speaker Count Detection**: Silhouette scoring automatically determines the optimal number of speakers
5. **Output**: Timestamped, speaker-labeled transcript chunks (e.g., `[Speaker 1 | 00:12–00:34]`)

---

### Stage 2: Semantic Chunking

After raw text is extracted, the `Chunker` class splits it into semantically meaningful pieces optimized for embedding and retrieval.

| Parameter | Default | Description |
|---|---|---|
| `CHUNK_SIZE` | 512 tokens | Target chunk size |
| `CHUNK_OVERLAP` | 50 tokens | Overlap between consecutive chunks for context continuity |
| `respect_sentences` | `True` | Avoids breaking mid-sentence |

**How it works:**
1. Text is split into sentences using regex-based sentence boundary detection
2. Sentences are accumulated until the token budget (`CHUNK_SIZE`) is reached
3. A new chunk begins with **overlap sentences** carried from the previous chunk's tail, preventing loss of context at chunk boundaries
4. If a single sentence exceeds the chunk size, it falls back to **token-level splitting** using `tiktoken` (OpenAI's `cl100k_base` tokenizer), or a word-based approximation if tiktoken is unavailable
5. CSV files use a custom **row-based chunking** strategy (default: 20 rows per chunk) that preserves column headers in every chunk

---

### Stage 3: Embedding Generation

Each chunk is converted into a dense vector representation (embedding) for similarity search.

| Mode | Model | Dimensions | Library |
|---|---|---|---|
| **Local** (offline) | `nomic-embed-text` | 768 | Ollama |
| **Cloud** (deployed) | `all-MiniLM-L6-v2` | 384 | Sentence-Transformers |

The `Embedder` class handles both modes transparently:
- In `local` mode: Calls the Ollama API running on `localhost:11434`
- In `cloud` mode: Loads the `SentenceTransformer` model in-process
- Supports single text embedding, batch embedding, and numpy output
- Automatically truncates text to 8,000 characters to avoid context length errors

---

### Stage 4: Vector Storage

Embeddings and their associated metadata are stored in **ChromaDB**, a high-performance vector database.

**Key design decisions:**
- Uses a **single physical collection** with **logical collections via metadata filtering** — this avoids the overhead of managing multiple Chroma collections while still letting users organize documents into named groups (e.g., "Research Papers", "Meeting Notes")
- In `local` mode: Uses `PersistentClient` for durable on-disk storage
- In `cloud` mode: Uses `EphemeralClient` (in-memory, wiped on restart)
- Cosine similarity is used as the distance metric (`hnsw:space: cosine`)
- A sidecar `collections.json` file tracks user-created collection names (even empty ones)

---

### Stage 5: Retrieval

When a user asks a question, the `Retriever` orchestrates a multi-stage search pipeline:

#### 5a. Dense Vector Search (Default)
The query is embedded using the same model as ingestion, and ChromaDB returns the top-K nearest chunks by cosine similarity. Default `TOP_K_RESULTS = 5`.

#### 5b. Hybrid Search (Optional — `USE_HYBRID_SEARCH=true`)
Combines dense vector search with **BM25** (Best Matching 25) sparse keyword search using Reciprocal Rank Fusion:

| Component | What It Does |
|---|---|
| **Dense (Embeddings)** | Finds semantically similar chunks even with different wording |
| **Sparse (BM25)** | Finds exact keyword matches that embeddings might miss |
| **Fusion** | Weighted combination controlled by `HYBRID_ALPHA` (default 0.5) |

#### 5c. Cross-Encoder Reranking (`USE_RERANKER=true` by default)
After initial retrieval (3× top-K candidates), a **Cross-Encoder** model (`cross-encoder/ms-marco-MiniLM-L-6-v2`) re-scores each query-document pair jointly for much higher precision. The reranker processes query and document together (unlike bi-encoders which encode them independently), producing significantly more accurate relevance scores. Falls back to LLM-based reranking if the cross-encoder library is unavailable.

#### 5d. Maximal Marginal Relevance (MMR)
An optional diversity filter that balances relevance to the query against redundancy among selected results:

```
MMR Score = λ × sim(doc, query) - (1-λ) × max(sim(doc, selected))
```

This ensures the final result set is both relevant and diverse, avoiding near-duplicate chunks.

---

### Stage 6: LLM Generation & Response

The retrieved context chunks are assembled into a prompt and sent to the LLM for answer generation.

| Mode | Model | Provider |
|---|---|---|
| **Local** | `mistral:7b` | Ollama (local GPU) |
| **Cloud** | `llama-3.1-8b-instant` | Groq API (ultra-fast cloud inference) |

**Generation pipeline:**
1. **Context Assembly**: The `CitationEngine` injects `[Source 1]`, `[Source 2]`, etc. markers into the context so the LLM can reference them
2. **Conversation History**: The last 6 messages from the chat session are prepended to the prompt for multi-turn awareness
3. **LLM Call**: The prompt is sent with a system instruction that enforces grounded answering and source citation
4. **Guardrails Validation**: The `Guardrails` module post-processes every response:
   - Detects uncertainty phrases ("I think", "probably") and adjusts confidence score
   - Checks for source citation presence
   - Filters excessive formatting
5. **Citation Extraction**: The `CitationEngine` parses `[Source N]` references from the response and maps them back to original document metadata
6. **Streaming**: Responses are streamed token-by-token via Server-Sent Events (NDJSON) for real-time display in the UI

---

## 🚀 Tech Stack

### Backend
| Component | Technology |
|---|---|
| API Framework | **FastAPI** + **Uvicorn** |
| Vector Database | **ChromaDB** |
| Embedding (Local) | **Ollama** (`nomic-embed-text`) |
| Embedding (Cloud) | **Sentence-Transformers** (`all-MiniLM-L6-v2`) |
| LLM (Local) | **Ollama** (`mistral:7b`) |
| LLM (Cloud) | **Groq API** (`llama-3.1-8b-instant`) |
| PDF Processing | **PyMuPDF** (`fitz`) |
| DOCX Processing | **python-docx** |
| OCR | **DeepSeek/LLaVA** (local) / **Gemini 1.5 Flash** (cloud) |
| Speech-to-Text | **Faster-Whisper** (local) / **Groq Whisper API** (cloud) |
| Speaker Diarization | **Librosa** + **scikit-learn** (MFCC + Spectral Clustering) |
| Reranking | **Cross-Encoder** (`ms-marco-MiniLM-L-6-v2`) |
| Chat Persistence | **SQLite** |
| Containerization | **Docker** |

### Frontend
| Component | Technology |
|---|---|
| Framework | **React 18** |
| Build Tool | **Vite** |
| State Management | **Zustand** |
| Styling | **TailwindCSS** |
| Animations | **Framer Motion** |
| Icons | **Lucide React** |

---

## 📁 Project Structure

```
Aegis/
├── src/                          # Python backend
│   ├── api/                      # FastAPI application
│   │   ├── main.py               # App entry point, middleware, static files
│   │   └── routes/               # API endpoint handlers
│   │       ├── ingest.py         # File upload & processing endpoints
│   │       ├── query.py          # RAG query & semantic search endpoints
│   │       ├── chat.py           # Chat session management
│   │       ├── manage.py         # Document & collection management
│   │       ├── diarization.py    # Speaker diarization endpoints
│   │       └── settings.py       # Runtime settings endpoints
│   ├── processors/               # Document processors
│   │   ├── base.py               # BaseProcessor ABC & Chunk dataclass
│   │   ├── pdf_processor.py      # PDF text, table, image, OCR extraction
│   │   ├── docx_processor.py     # DOCX section-aware extraction
│   │   ├── csv_processor.py      # CSV schema detection & row chunking
│   │   ├── image_processor.py    # Image OCR & visual understanding
│   │   └── voice_processor.py    # Audio transcription & speaker diarization
│   ├── chunking/                 # Text chunking
│   │   └── chunker.py            # Sentence-aware semantic chunking with overlap
│   ├── embedding/                # Embedding generation
│   │   └── embedder.py           # Ollama (local) / SentenceTransformer (cloud)
│   ├── vectorstore/              # Vector database
│   │   └── chroma_store.py       # ChromaDB with logical collections
│   ├── retrieval/                # Search & retrieval
│   │   ├── retriever.py          # Main retriever (dense + hybrid + rerank)
│   │   ├── reranker.py           # Cross-Encoder reranking
│   │   ├── hybrid.py             # BM25 sparse search + fusion
│   │   └── mmr.py                # Maximal Marginal Relevance diversity
│   ├── generation/               # LLM response generation
│   │   ├── llm.py                # Local Ollama LLM client
│   │   ├── llm_cloud.py          # Groq API LLM client
│   │   ├── guardrails.py         # Response validation & confidence scoring
│   │   └── citations.py          # Source citation extraction & formatting
│   ├── ocr/                      # OCR engine
│   │   ├── deepseek_ocr.py       # DeepSeek vision model OCR via Ollama
│   │   └── gemini_ocr.py         # Gemini OCR API for cloud environments
│   ├── chat_history/             # Chat persistence
│   │   └── db.py                 # SQLite session & message storage
│   ├── config.py                 # Central configuration (dataclass)
│   └── dependencies.py           # Singleton dependency injection
│
├── renderer/                     # React frontend
│   ├── src/
│   │   ├── App.jsx               # Main application shell
│   │   ├── components/           # Reusable UI components
│   │   │   ├── chat/             # Chat interface components
│   │   │   ├── ingestion/        # File upload components
│   │   │   └── layout/           # Sidebar, header, navigation
│   │   ├── views/                # Page-level views
│   │   │   ├── Dashboard.jsx     # System stats & overview
│   │   │   ├── QueryWorkspace.jsx # Search interface
│   │   │   ├── CollectionsManager.jsx # Document collections
│   │   │   └── SettingsView.jsx  # Configuration panel
│   │   ├── services/api.js       # API client (fetch wrapper)
│   │   ├── store/                # Zustand state stores
│   │   └── hooks/                # Custom React hooks
│   ├── vercel.json               # Vercel SPA routing config
│   └── package.json
│
├── Dockerfile                    # Multi-stage build (Node + Python)
├── render.yaml                   # Render deployment blueprint
├── requirements-cloud.txt        # Cloud Python dependencies
└── README.md
```

---

## 🌐 Deployment

Aegis supports a **split deployment** architecture:

| Component | Platform | URL |
|---|---|---|
| Frontend (React) | **Vercel** | Auto-deployed from `renderer/` |
| Backend (FastAPI) | **Render** | Docker container from `Dockerfile` |

### Environment Variables

**Vercel:**
| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | URL of your Render backend (e.g., `https://aegis-backend.onrender.com`) |

**Render:**
| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key for LLM inference |
| `GEMINI_API_KEY` | Gemini API key for OCR and image understanding |
| `DEPLOYMENT_MODE` | Set to `cloud` (configured in `render.yaml`) |

---

## 🖥️ Local Development

### Prerequisites
- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.com/) installed and running
- Required Ollama models: `mistral:7b`, `nomic-embed-text`, `llava`

### Setup
```bash
# Clone the repository
git clone https://github.com/bhasithsaireddy/Aegis-RAG.git
cd Aegis-RAG

# Install Python dependencies
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Pull required Ollama models
ollama pull mistral:7b
ollama pull nomic-embed-text
ollama pull llava

# Install frontend dependencies
cd renderer
npm install

# Start the backend
cd ..
python -m uvicorn src.api.main:app --reload

# Start the frontend (in a separate terminal)
cd renderer
npm run dev
```

---

<p align="center">
  Built with ❤️ by <strong>Bhasith Sai Reddy</strong>
</p>
