"""Pydantic models for API requests and responses"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ----- Query Models -----

class QueryRequest(BaseModel):
    """Request for RAG query"""
    query: str = Field(..., description="The question to ask")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to retrieve")
    doc_types: Optional[List[str]] = Field(default=None, description="Filter by document types")
    collections: Optional[List[str]] = Field(default=None, description="Filter by collections")
    session_id: Optional[str] = Field(default=None, description="Persistent session ID")


class Source(BaseModel):
    """Source citation"""
    index: int
    file: str
    type: str
    location: Optional[str] = None
    similarity: float


class QueryResponse(BaseModel):
    """Response from RAG query"""
    answer: str
    sources: List[Source]
    confidence: float


class SearchRequest(BaseModel):
    """Request for semantic search"""
    query: str
    top_k: int = Field(default=10, ge=1, le=50)
    doc_types: Optional[List[str]] = None
    collections: Optional[List[str]] = None


class SearchResult(BaseModel):
    """Single search result"""
    id: str
    content: str
    source_file: str
    doc_type: str
    similarity: float
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    """Response from semantic search"""
    results: List[SearchResult]
    total: int


# ----- Ingestion Models -----

class IngestRequest(BaseModel):
    """Request for file ingestion"""
    collections: Optional[List[str]] = Field(default=None, description="Collections to add to")


class IngestResponse(BaseModel):
    """Response from file ingestion"""
    document_id: str
    filename: str
    doc_type: str
    chunks_created: int
    collections: List[str]


class IngestStatus(BaseModel):
    """Status of ingestion job"""
    document_id: str
    status: str  # processing, completed, failed
    progress: float
    message: Optional[str] = None


# ----- Document/Collection Models -----

class DocumentInfo(BaseModel):
    """Document information"""
    document_id: str
    doc_type: str
    source_file: str
    collections: List[str]
    chunk_count: Optional[int] = None
    created_at: Optional[str] = None


class CollectionInfo(BaseModel):
    """Collection information"""
    name: str
    document_count: int


class StatsResponse(BaseModel):
    """System statistics"""
    total_chunks: int
    total_documents: int
    total_collections: int
    documents_by_type: Dict[str, int]
    collections: List[str]


# ----- Collection Management -----

class AddToCollectionRequest(BaseModel):
    """Request to add document to collection"""
    document_id: str
    collection: str


class CreateCollectionRequest(BaseModel):
    """Request to create a new collection"""
    name: str
    description: Optional[str] = None
