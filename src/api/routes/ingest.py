"""File ingestion endpoints"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
from pathlib import Path
from uuid import uuid4
import shutil

from ..models import IngestRequest, IngestResponse
from ...config import config
from ...processors import PDFProcessor, DOCXProcessor, CSVProcessor, ImageProcessor, VoiceProcessor
from ...dependencies import get_store


router = APIRouter()

# Processor registry
PROCESSORS = {
    ".pdf": PDFProcessor(),
    ".docx": DOCXProcessor(),
    ".doc": DOCXProcessor(),
    ".csv": CSVProcessor(),
    ".tsv": CSVProcessor(),
    ".png": ImageProcessor(),
    ".jpg": ImageProcessor(),
    ".jpeg": ImageProcessor(),
    ".webp": ImageProcessor(),
    ".bmp": ImageProcessor(),
    # TIFF and GIF were listed as supported but missing from this registry
    ".tiff": ImageProcessor(),
    ".tif": ImageProcessor(),
    ".gif": ImageProcessor(),
    ".mp3": VoiceProcessor(),
    ".wav": VoiceProcessor(),
    ".m4a": VoiceProcessor(),
    ".ogg": VoiceProcessor(),
    ".flac": VoiceProcessor(),
}


@router.post("/ingest", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    collections: Optional[str] = Form(default=None)
):
    """
    Upload and process a file for RAG.
    
    Supports: PDF, DOCX, CSV, Images (PNG, JPG, TIFF, GIF, etc.), Audio (MP3, WAV, etc.)
    """
    store = get_store()

    # Parse collections from comma-separated string
    collection_list = []
    if collections:
        collection_list = [c.strip() for c in collections.split(",") if c.strip()]
    
    # Validate file extension
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()
    
    if ext not in PROCESSORS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {list(PROCESSORS.keys())}"
        )
    
    # Save uploaded file with UUID prefix to avoid filename collisions
    safe_name = f"{uuid4().hex}_{filename}"
    upload_path = config.UPLOADS_DIR / safe_name
    
    try:
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    
    try:
        # Get appropriate processor
        processor = PROCESSORS[ext]
        
        # Process the file
        chunks = processor.process(upload_path)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No content extracted from file")
        
        # Add to vector store
        chunk_ids = store.add_chunks(chunks, collections=collection_list)
        
        # Get document info
        document_id = chunks[0].document_id if chunks else ""
        doc_type = chunks[0].doc_type if chunks else "unknown"
        
        return IngestResponse(
            document_id=document_id,
            filename=filename,
            doc_type=doc_type,
            chunks_created=len(chunk_ids),
            collections=collection_list
        )
    
    except Exception as e:
        # Clean up on failure
        if upload_path.exists():
            upload_path.unlink()
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")


@router.post("/ingest/batch")
async def ingest_batch(
    files: List[UploadFile] = File(...),
    collections: Optional[str] = Form(default=None)
):
    """
    Upload and process multiple files.
    """
    store = get_store()
    results = []
    errors = []
    
    collection_list = []
    if collections:
        collection_list = [c.strip() for c in collections.split(",") if c.strip()]
    
    for file in files:
        try:
            # Process each file
            filename = file.filename or "unknown"
            ext = Path(filename).suffix.lower()
            
            if ext not in PROCESSORS:
                errors.append({"file": filename, "error": f"Unsupported type: {ext}"})
                continue
            
            # Save file with UUID prefix
            safe_name = f"{uuid4().hex}_{filename}"
            upload_path = config.UPLOADS_DIR / safe_name

            with open(upload_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Process
            processor = PROCESSORS[ext]
            chunks = processor.process(upload_path)
            
            if chunks:
                chunk_ids = store.add_chunks(chunks, collections=collection_list)
                results.append({
                    "file": filename,
                    "document_id": chunks[0].document_id,
                    "chunks": len(chunk_ids)
                })
            else:
                errors.append({"file": filename, "error": "No content extracted"})
        
        except Exception as e:
            errors.append({"file": file.filename, "error": str(e)})
    
    return {
        "processed": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }


@router.get("/ingest/supported")
async def get_supported_types():
    """Get list of supported file types"""
    return {
        "extensions": list(PROCESSORS.keys()),
        "types": {
            "documents": [".pdf", ".docx", ".doc", ".csv", ".tsv"],
            "images": [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif", ".gif"],
            "audio": [".mp3", ".wav", ".m4a", ".ogg", ".flac"]
        }
    }
