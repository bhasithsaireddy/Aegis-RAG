# FRONTEND DESIGN PROMPT (Electron + React)
---
## ROLE & CONTEXT

You are a **senior desktop application UI/UX engineer** building a **production-grade offline desktop application** using:

* **Electron.js** (desktop shell)
* **React + Vite** (renderer)
* **Tailwind CSS** (styling)
* **Local Python FastAPI backend** (spawned internally, no internet)
* **NO cloud services**
* **NO external APIs**
* **NO browser-first UI assumptions**

This application is called **Aegis RAG** — a **fully offline multimodal RAG system** that processes:

* PDFs
* DOCX files
* Images
* Voice recordings

The frontend must feel like:

* A **professional research workstation**
* A **knowledge exploration tool**
* A **private intelligence desktop app**

NOT like:

* ChatGPT
* Claude
* Generic AI dashboards
* SaaS admin panels
* Tailwind template UIs

---

## HARD CONSTRAINTS (VERY IMPORTANT)

1. **Offline-first**

   * No internet dependency
   * No Google fonts
   * No CDN usage
   * All assets bundled locally

2. **Desktop-native behavior**

   * File system access
   * Drag-and-drop from OS
   * Persistent state across sessions
   * Keyboard-heavy workflows

3. **Backend communication**

   * All data comes from **FastAPI on localhost**
   * Use IPC via Electron preload securely
   * Never expose Node APIs directly to React

4. **UI originality**

   * Do NOT use standard chat layouts
   * Do NOT copy AI chat interfaces
   * Must feel purpose-built for multimodal knowledge work

---

## APPLICATION IDENTITY

**Name:** Aegis RAG
**Tagline:** *Offline Multimodal Intelligence Workspace*

Design philosophy:

* Calm
* Dense but readable
* Research-oriented
* Minimal animations
* Zero visual noise

Think:

> “VS Code + Obsidian + Research Lab Tool”

---

## CORE UI LAYOUT (MANDATORY)

### 1️⃣ Global Layout

Design a **three-pane desktop layout**:

```
┌───────────────────────────────────────────────┐
│ Top Command Bar (status, model, system state) │
├───────────────┬────────────────┬──────────────┤
│ Left Sidebar  │ Main Workspace │ Right Context │
│ (Knowledge)   │ (Interaction)  │ (Sources)    │
└───────────────┴────────────────┴──────────────┘
```

---

### 2️⃣ Top Command Bar (NOT a navbar)

Purpose:

* System-level awareness, not navigation

Must include:

* Backend status
* Loaded LLM name
* Embedding model
* Vector DB status
* Processing queue indicator

Design:

* Thin height
* Text-heavy
* No big buttons
* Looks like a **toolchain header**

---

### 3️⃣ Left Sidebar — Knowledge Manager

This is **NOT a menu**.

This is a **knowledge explorer**.

Must support:

* Document collections
* File type grouping (PDF / Image / Audio)
* Index status per document
* Search within documents
* Delete / reindex actions

UI ideas:

* Tree structure
* Expandable nodes
* Icons per modality
* Small metadata text (pages, chunks, timestamps)

No emojis. Use icons from lucide react or something similar. No cards.

---

### 4️⃣ Main Workspace — Query & Reasoning Area

This is the **heart of Aegis RAG**.

#### DO NOT create a chat bubble UI.

Instead:

* Structured conversation blocks
* Each query = a “Query Session”
* Responses appear as **annotated analysis blocks**

Each response block must support:

* Expand / collapse
* Highlighted cited sentences
* Inline citation markers
* Streaming text rendering (token-by-token)

Query input:

* Large multiline input
* Keyboard-first
* Cmd/Ctrl + Enter to submit
* No placeholder like “Ask me anything”

---

### 5️⃣ Right Context Panel — Evidence & Sources

This panel shows **WHY the answer exists**.

Must include:

* Source documents
* Page numbers / timestamps
* Confidence indicators
* Chunk previews
* Click → jump to source

This panel must update **live** while the model streams output.

---

## FILE INGESTION UX (CRITICAL)

Design a **desktop-native ingestion flow**:

### Features:

* Drag & drop from OS
* File picker via Electron dialog
* Visual pipeline stages:

  * Reading
  * OCR
  * Chunking
  * Embedding
  * Indexed

Each file must show:

* Progress bar
* Current stage
* Estimated time
* Error handling

NO modal popups unless critical.

---

## SETTINGS & CONFIGURATION UI

Settings are **technical**, not consumer-friendly.

Include:

* LLM selection (local only)
* Chunk size
* Overlap size
* Retrieval top-k
* Enable/disable vision/audio pipelines

Design:

* Side panel or drawer
* Dense form layout
* Clear defaults
* No tooltips spam

---

## VISUAL DESIGN SYSTEM

### Colors

* Dark-first
* Neutral grays
* One accent color only
* No gradients
* No neon

### Typography

* montserrat / poppins
* Monospace for metadata
* Serif fonts NOT allowed

### Animations

* Minimal
* Purpose-driven only
* No fancy transitions

---

## TECHNICAL IMPLEMENTATION REQUIREMENTS

### Electron

* `main.js`: window lifecycle, backend spawn
* `preload.js`: IPC bridge only
* Secure context isolation

### React

* Component-driven
* No global mutable state hacks
* Clear separation:

  * UI
  * IPC services
  * API clients

### API Integration

Endpoints include:

* `/api/ingest`
* `/api/query`
* `/api/search`
* `/api/collections`
* `/api/stats`

Design frontend to be **backend-agnostic**.

---

## DELIVERABLES YOU MUST GENERATE

1. Full **component hierarchy**
2. UI wireframe description (textual)
3. State management strategy
4. IPC communication flow
5. Accessibility considerations
6. Error & edge-case UX
7. Desktop-specific UX decisions
8. Folder structure
9. Styling strategy
10. Rationale for every major UI choice

---

## ABSOLUTE AVOIDANCE LIST ❌

Do NOT:

* Use chat bubbles
* Use AI avatars
* Use “thinking…” spinners
* Use SaaS-style dashboards
* Use Tailwind template layouts
* Use generic landing-page UI
* Use cloud metaphors

---

## FINAL INSTRUCTION

Design Aegis RAG as if:

> This app will be used by **lawyers, researchers, intelligence analysts, and engineers** who trust it with **private, sensitive data**, fully offline.

Precision > Flash
Clarity > Beauty
Control > Convenience