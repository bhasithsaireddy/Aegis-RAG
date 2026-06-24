"""Chat session management routes"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ...chat_history.db import ChatDB

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize DB
db = ChatDB()


class SessionResponse(BaseModel):
    id: str
    title: str
    updated_at: str


class CreateSessionRequest(BaseModel):
    title: Optional[str] = "New Chat"


class UpdateSessionRequest(BaseModel):
    title: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str
    metadata: Dict[str, Any]


@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(limit: int = 50):
    """List recent chat sessions."""
    sessions = db.get_sessions(limit)
    return [
        SessionResponse(
            id=s["id"],
            title=s["title"],
            updated_at=str(s["updated_at"])
        )
        for s in sessions
    ]


@router.post("/sessions", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest):
    """Create a new chat session."""
    session_id = db.create_session(request.title or "New Chat")
    session = db.get_session(session_id)
    return SessionResponse(
        id=session["id"],
        title=session["title"],
        updated_at=str(session["updated_at"])
    )


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(session_id: str):
    """Get all messages for a session."""
    messages = db.get_messages(session_id)
    return [
        MessageResponse(
            id=m["id"],
            role=m["role"],
            content=m["content"],
            created_at=str(m["created_at"]),
            metadata=m["metadata"]
        )
        for m in messages
    ]


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session."""
    db.delete_session(session_id)
    return {"status": "deleted"}


@router.patch("/sessions/{session_id}")
async def update_session(session_id: str, request: UpdateSessionRequest):
    """Update session title."""
    db.update_session_title(session_id, request.title)
    return {"status": "updated"}
