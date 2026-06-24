"""Collection and document management endpoints"""
from fastapi import APIRouter, HTTPException
from typing import List

from ..models import (
    DocumentInfo,
    CollectionInfo,
    StatsResponse,
    AddToCollectionRequest
)
from ...dependencies import get_store


router = APIRouter()


@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """Get all documents in the system"""
    store = get_store()
    documents = store.get_all_documents()
    
    return [
        DocumentInfo(
            document_id=doc["document_id"],
            doc_type=doc["doc_type"],
            source_file=doc["source_file"],
            collections=doc["collections"]
        )
        for doc in documents
    ]


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all its chunks"""
    store = get_store()
    count = store.delete_document(document_id)
    
    if count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "document_id": document_id,
        "chunks_deleted": count
    }


@router.get("/collections", response_model=List[str])
async def list_collections():
    """Get all logical collections"""
    return get_store().get_all_collections()


@router.post("/collections")
async def create_collection(name: str):
    """Create a new empty collection"""
    store = get_store()
    existing = store.get_all_collections()
    if name in existing:
        raise HTTPException(status_code=400, detail="Collection already exists")
    
    store.create_collection(name)
    
    return {
        "name": name,
        "status": "created"
    }


@router.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str):
    """Delete a collection (removes collection tag from documents, doesn't delete documents)"""
    store = get_store()
    existing = store.get_all_collections()
    if collection_name not in existing:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    count = store.delete_collection(collection_name)
    
    return {
        "name": collection_name,
        "documents_affected": count,
        "status": "deleted"
    }


@router.post("/collections/add")
async def add_to_collection(request: AddToCollectionRequest):
    """Add a document to a collection"""
    get_store().add_to_collection(request.document_id, request.collection)
    
    return {
        "document_id": request.document_id,
        "collection": request.collection,
        "status": "added"
    }


@router.get("/collections/{collection}/documents", response_model=List[DocumentInfo])
async def get_collection_documents(collection: str):
    """Get all documents in a collection"""
    all_docs = get_store().get_all_documents()
    
    docs = [
        DocumentInfo(
            document_id=doc["document_id"],
            doc_type=doc["doc_type"],
            source_file=doc["source_file"],
            collections=doc["collections"]
        )
        for doc in all_docs
        if collection in doc.get("collections", [])
    ]
    
    return docs


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get system statistics"""
    stats = get_store().get_stats()
    
    return StatsResponse(
        total_chunks=stats["total_chunks"],
        total_documents=stats["total_documents"],
        total_collections=stats["total_collections"],
        documents_by_type=stats["documents_by_type"],
        collections=stats["collections"]
    )
