# Aegis

Aegis is an intelligent, high-performance Retrieval-Augmented Generation (RAG) system built to provide accurate, context-aware answers from your personal documents. 

Designed with flexibility in mind, Aegis can run entirely offline for maximum privacy or be deployed to the cloud (Vercel + Render / Hugging Face Spaces) for global accessibility.

## ✨ Features
- **Multi-Modal Ingestion:** Upload and process PDFs, Word documents (DOCX), plain text files, and even Audio recordings.
- **Conversational AI:** A sleek, modern React frontend for natural, multi-turn conversations that remember context.
- **Strict RAG Enforcement:** Intelligently cites sources and refuses to hallucinate facts outside of the provided context documents.
- **Lightning Fast Vector Search:** Powered by ChromaDB and state-of-the-art embedding models.
- **Cloud & Local Ready:** Seamlessly switch between local Ollama models for absolute privacy, or Hugging Face Inference APIs for cloud-hosted deployments.

## 🚀 Tech Stack
- **Frontend:** React, Vite, Zustand, TailwindCSS, Framer Motion
- **Backend:** Python, FastAPI, Uvicorn
- **AI/ML:** Hugging Face Inference API, Sentence-Transformers, ChromaDB
- **Infrastructure:** Docker, Render (Backend), Vercel (Frontend)

## 📦 Deployment
Aegis is configured for a split deployment architecture:
1. **Frontend (Vercel):** The `renderer/` directory is automatically configured as a SPA via `vercel.json`.
2. **Backend (Render):** The `render.yaml` blueprint automates the deployment of the FastAPI server via Docker.

*Note: Requires setting `VITE_API_BASE_URL` in Vercel and `HF_API_TOKEN` in Render.*
