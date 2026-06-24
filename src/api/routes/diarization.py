"""Speaker Diarization API endpoints"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import Optional, List
from pathlib import Path
from datetime import datetime
import shutil
import os

from pydantic import BaseModel

from ...config import config
from ...processors.voice_processor import EnhancedVoiceProcessor


router = APIRouter()

# Initialize voice processor
voice_processor = EnhancedVoiceProcessor(use_diarization=True)

# Temp upload directory for diarization
DIARIZATION_TEMP_DIR = config.UPLOADS_DIR / "diarization_temp"
DIARIZATION_TEMP_DIR.mkdir(parents=True, exist_ok=True)


class DiarizationRequest(BaseModel):
    """Request model for diarization by path."""
    audio_path: str
    language: Optional[str] = None
    num_speakers: Optional[int] = None


class SpeakerSegment(BaseModel):
    """A segment of speech from a speaker."""
    speaker: str
    start: float
    end: float
    text: str
    confidence: float = 1.0


class DiarizationResponse(BaseModel):
    """Response model for diarization results."""
    success: bool
    file_name: str
    duration: float
    speaker_count: int
    speakers: List[str]
    segments: List[SpeakerSegment]
    metadata: dict
    error: Optional[str] = None


def cleanup_temp_file(file_path: str):
    """Background task to cleanup temporary files."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass


@router.post("/diarize", response_model=DiarizationResponse)
async def diarize_by_path(request: DiarizationRequest):
    """
    Perform speaker diarization on an audio file by path.
    
    This endpoint is used when the audio file is already on disk.
    """
    try:
        if not os.path.exists(request.audio_path):
            raise HTTPException(
                status_code=404,
                detail=f"Audio file not found: {request.audio_path}"
            )
        
        result = voice_processor.diarize(
            audio_path=request.audio_path,
            language=request.language,
            num_speakers=request.num_speakers
        )
        
        return DiarizationResponse(
            success=True,
            file_name=result.get("file_name", "unknown"),
            duration=result.get("duration", 0),
            speaker_count=result.get("speaker_count", 0),
            speakers=result.get("speakers", []),
            segments=[SpeakerSegment(**seg) for seg in result.get("segments", [])],
            metadata=result.get("metadata", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return DiarizationResponse(
            success=False,
            file_name=os.path.basename(request.audio_path),
            duration=0,
            speaker_count=0,
            speakers=[],
            segments=[],
            metadata={},
            error=str(e)
        )


@router.post("/diarize/upload", response_model=DiarizationResponse)
async def diarize_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: Optional[str] = None,
    num_speakers: Optional[int] = None
):
    """
    Perform speaker diarization on an uploaded audio file.
    
    Supports: MP3, WAV, M4A, OGG, FLAC, WEBM, AAC
    """
    temp_path = None
    
    try:
        # Validate extension
        filename = file.filename or "unknown"
        ext = Path(filename).suffix.lower()
        
        supported = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm", ".aac"}
        if ext not in supported:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {ext}. Supported: {supported}"
            )
        
        # Save temp file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_path = DIARIZATION_TEMP_DIR / f"{timestamp}_{filename}"
        
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Perform diarization
        result = voice_processor.diarize(
            audio_path=str(temp_path),
            language=language,
            num_speakers=num_speakers
        )
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_temp_file, str(temp_path))
        
        return DiarizationResponse(
            success=True,
            file_name=result.get("file_name", filename),
            duration=result.get("duration", 0),
            speaker_count=result.get("speaker_count", 0),
            speakers=result.get("speakers", []),
            segments=[SpeakerSegment(**seg) for seg in result.get("segments", [])],
            metadata=result.get("metadata", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        
        return DiarizationResponse(
            success=False,
            file_name=file.filename or "unknown",
            duration=0,
            speaker_count=0,
            speakers=[],
            segments=[],
            metadata={},
            error=str(e)
        )


@router.post("/transcribe/upload")
async def transcribe_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: Optional[str] = None
):
    """
    Transcribe audio without speaker diarization.
    
    Faster option when speaker identification is not needed.
    """
    temp_path = None
    
    try:
        filename = file.filename or "unknown"
        ext = Path(filename).suffix.lower()
        
        supported = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm", ".aac"}
        if ext not in supported:
            raise HTTPException(status_code=400, detail=f"Unsupported: {ext}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_path = DIARIZATION_TEMP_DIR / f"trans_{timestamp}_{filename}"
        
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Create processor without diarization
        processor = EnhancedVoiceProcessor(use_diarization=False)
        result = processor.diarize(str(temp_path), language=language)
        
        background_tasks.add_task(cleanup_temp_file, str(temp_path))
        
        # Build full transcript
        full_text = " ".join(seg["text"] for seg in result.get("segments", []))
        
        return {
            "success": True,
            "file_name": filename,
            "text": full_text,
            "segments": result.get("segments", []),
            "duration": result.get("duration", 0),
            "metadata": result.get("metadata", {})
        }
        
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        
        return {
            "success": False,
            "file_name": file.filename or "unknown",
            "text": "",
            "segments": [],
            "error": str(e)
        }


@router.get("/diarize/status")
async def get_diarization_status():
    """Get status of diarization components."""
    whisper_available = False
    try:
        from faster_whisper import WhisperModel
        whisper_available = True
    except ImportError:
        try:
            import whisper
            whisper_available = True
        except ImportError:
            pass
    
    return {
        "voice_processor_initialized": True,
        "whisper_available": whisper_available,
        "diarization_enabled": voice_processor.use_diarization,
        "supported_formats": voice_processor.supported_extensions,
        "whisper_models": ["tiny", "base", "small", "medium", "large-v2"]
    }
