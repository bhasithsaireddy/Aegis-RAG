"""Base processor interface and Chunk data structure"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


@dataclass
class Chunk:
    """Represents a chunk of content with metadata"""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    
    # Document metadata
    document_id: str = ""
    doc_type: str = ""  # pdf, docx, image, voice
    source_file: str = ""
    
    # Position metadata
    page: Optional[int] = None
    timestamp_start: Optional[float] = None  # For voice
    timestamp_end: Optional[float] = None
    speaker: Optional[str] = None  # For voice diarization
    
    # Logical collections (user-defined)
    collections: List[str] = field(default_factory=list)
    
    # Additional metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "content": self.content,
            "document_id": self.document_id,
            "doc_type": self.doc_type,
            "source_file": self.source_file,
            "page": self.page,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end,
            "speaker": self.speaker,
            "collections": self.collections,
            "created_at": self.created_at,
            **self.metadata
        }


class BaseProcessor(ABC):
    """Abstract base class for document processors"""
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """List of file extensions this processor handles"""
        pass
    
    @property
    @abstractmethod
    def doc_type(self) -> str:
        """Document type identifier (pdf, docx, image, voice)"""
        pass
    
    def can_process(self, file_path: Path) -> bool:
        """Check if this processor can handle the given file"""
        return file_path.suffix.lower() in self.supported_extensions
    
    @abstractmethod
    def process(self, file_path: Path, document_id: Optional[str] = None) -> List[Chunk]:
        """
        Process a file and return a list of chunks.
        
        Args:
            file_path: Path to the file to process
            document_id: Optional ID for the document (generated if not provided)
            
        Returns:
            List of Chunk objects
        """
        pass
    
    def _generate_document_id(self, file_path: Path) -> str:
        """Generate a unique document ID"""
        return f"{file_path.stem}_{uuid.uuid4().hex[:8]}"
