"""Query and search endpoints"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
import json

from ..models import (
    QueryRequest, 
    QueryResponse, 
    SearchRequest, 
    SearchResponse,
    SearchResult,
    Source
)
from ...dependencies import get_retriever, get_store, get_llm
from ...generation import Guardrails, CitationEngine
from ...config import config

from ...chat_history.db import ChatDB

router = APIRouter()

# Shared singletons
llm = get_llm()
guardrails = Guardrails()
citations = CitationEngine()
chat_db = ChatDB()


def _build_conversation_context(session_id: str) -> str:
    """
    Load the last N messages from the chat DB and format as conversation history
    to inject into the LLM prompt for multi-turn awareness.
    """
    if not session_id:
        return ""

    messages = chat_db.get_messages(session_id)
    if not messages:
        return ""

    # Take last CHAT_CONTEXT_MESSAGES messages (excluding the current turn)
    recent = messages[-config.CHAT_CONTEXT_MESSAGES:]
    
    history_lines = []
    for msg in recent:
        role_label = "User" if msg["role"] == "user" else "Assistant"
        history_lines.append(f"{role_label}: {msg['content']}")
    
    if not history_lines:
        return ""

    return "Previous conversation:\n" + "\n".join(history_lines) + "\n\n"


@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """
    Ask a question using RAG.
    
    Returns an answer with source citations.
    Multi-turn: if session_id is provided, the last few messages are used as context.
    """
    retriever = get_retriever()

    # Save user query if session active
    if request.session_id:
        chat_db.add_message(request.session_id, "user", request.query)
        
        # Auto-rename session if it's "New Chat"
        session = chat_db.get_session(request.session_id)
        if session and session["title"] == "New Chat":
            new_title = request.query[:50] + "..." if len(request.query) > 50 else request.query
            chat_db.update_session_title(request.session_id, new_title)

    # Retrieve relevant chunks
    results = retriever.retrieve(
        query=request.query,
        top_k=request.top_k,
        doc_types=request.doc_types,
        collections=request.collections
    )
    

    
    # Create context with source markers
    context, sources = citations.create_context_with_sources(results)
    
    # Build conversation history prefix for multi-turn awareness
    conv_history = _build_conversation_context(request.session_id)
    
    # Generate response
    try:
        full_prompt = f"{conv_history}Context:\n{context}\n\nQuestion: {request.query}\n\nAnswer:"
        answer = llm.generate(
            prompt=full_prompt,
            system="""You are a helpful AI assistant.
If the user is making a casual greeting or conversational remark, you may reply naturally.
For factual questions, answer ONLY based on the provided Context.
If the Context doesn't contain relevant information for a factual question, say "I don't have enough information to answer that."
Cite sources using [Source X] format. Do not make up information.""",
            temperature=0.3
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {e}")
    
    # Validate response
    validation = guardrails.validate(answer, context, request.query)
    answer = guardrails.filter_response(answer)
    
    # Format sources
    formatted_sources = citations.format_sources(sources, cited_only=True, response=answer)
    
    # Save assistant response if session active
    if request.session_id:
        chat_db.add_message(
            request.session_id, 
            "assistant", 
            answer,
            metadata={
                "sources": formatted_sources,
                "confidence": validation["confidence"]
            }
        )
    
    return QueryResponse(
        answer=answer,
        sources=[Source(**s) for s in formatted_sources],
        confidence=validation["confidence"]
    )


@router.post("/query/stream")
async def query_rag_stream(request: QueryRequest):
    """
    Ask a question using RAG with streaming response.
    Multi-turn: if session_id is provided, conversation history is injected.
    """
    retriever = get_retriever()

    # Save user query if session active
    if request.session_id:
        chat_db.add_message(request.session_id, "user", request.query)
        
        # Auto-rename session if it's "New Chat"
        session = chat_db.get_session(request.session_id)
        if session and session["title"] == "New Chat":
            new_title = request.query[:50] + "..." if len(request.query) > 50 else request.query
            chat_db.update_session_title(request.session_id, new_title)

    # Retrieve relevant chunks
    results = retriever.retrieve(
        query=request.query,
        top_k=request.top_k,
        doc_types=request.doc_types,
        collections=request.collections
    )
    

    
    # Create context with source markers
    context, sources = citations.create_context_with_sources(results)

    # Multi-turn conversation history prefix
    conv_history = _build_conversation_context(request.session_id)
    
    async def generate():
        full_response = ""
        try:
            # Stream the response
            for chunk in llm.generate_stream(
                prompt=f"{conv_history}Context:\n{context}\n\nQuestion: {request.query}\n\nAnswer:",
                system="""You are a helpful AI assistant.
If the user is making a casual greeting or conversational remark, you may reply naturally.
For factual questions, answer ONLY based on the provided Context.
If the Context doesn't contain relevant information for a factual question, say "I don't have enough information to answer that."
Cite sources using [Source X] format."""
            ):
                full_response += chunk
                yield json.dumps({"type": "chunk", "content": chunk}) + "\n"
            
            # Send sources
            formatted_sources = citations.format_sources(sources, cited_only=True, response=full_response)
            yield json.dumps({"type": "sources", "sources": formatted_sources}) + "\n"
            yield json.dumps({"type": "done"}) + "\n"
            
            # Save full response if session active
            if request.session_id:
                chat_db.add_message(
                    request.session_id,
                    "assistant",
                    full_response,
                    metadata={"sources": formatted_sources}
                )
            
        except Exception as e:
            err_msg = str(e)
            yield json.dumps({"type": "error", "error": err_msg}) + "\n"
    
    return StreamingResponse(generate(), media_type="application/x-ndjson")


@router.post("/search", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """
    Perform semantic search without LLM generation.
    
    Returns matching chunks with similarity scores.
    """
    retriever = get_retriever()
    results = retriever.retrieve(
        query=request.query,
        top_k=request.top_k,
        doc_types=request.doc_types,
        collections=request.collections
    )
    
    search_results = []
    for r in results:
        metadata = r.get("metadata", {})
        search_results.append(SearchResult(
            id=r["id"],
            content=r["content"],
            source_file=metadata.get("source_file", "Unknown"),
            doc_type=metadata.get("doc_type", "unknown"),
            similarity=r.get("similarity", 0),
            metadata=metadata
        ))
    
    return SearchResponse(
        results=search_results,
        total=len(search_results)
    )


@router.get("/models/status")
async def check_models():
    """Check model availability (Groq in cloud, Ollama in local)."""
    if config.DEPLOYMENT_MODE == "cloud":
        return {
            "llm": {
                "model": getattr(llm, "model", "unknown"),
                "available": llm.is_available()
            },
            "vision": {"model": "N/A (cloud)", "available": False},
            "embedding": {"model": "all-MiniLM-L6-v2", "available": True}
        }
    return {
        "llm": {
            "model": getattr(llm, "model", "unknown"),
            "available": llm.is_available()
        },
        "vision": {
            "model": config.VISION_MODEL,
            "available": _check_model_available(config.VISION_MODEL)
        },
        "embedding": {
            "model": config.EMBEDDING_MODEL,
            "available": _check_model_available(config.EMBEDDING_MODEL)
        }
    }


def _check_model_available(model_name: str) -> bool:
    """Check if a specific Ollama model is available (local mode only)."""
    try:
        import ollama
        response = ollama.list()
        models = getattr(response, "models", [])
        names = [
            (getattr(m, "model", "") or getattr(m, "name", "")).lower()
            for m in models
        ]
        target = model_name.lower()
        return target in names or any(target in n for n in names)
    except Exception:
        return False
