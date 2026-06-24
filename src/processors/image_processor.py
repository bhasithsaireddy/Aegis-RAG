"""Advanced Image processor with OCR and visual understanding"""
from pathlib import Path
from typing import List, Optional, Dict, Any
import base64
import logging

from .base import BaseProcessor, Chunk
from ..chunking import Chunker
from ..config import config

logger = logging.getLogger(__name__)


class ImageProcessor(BaseProcessor):
    """
    Advanced Image processor with:
    - OCR text extraction (DeepSeek vision model)
    - Visual understanding (scene description)
    - Table/chart detection in images
    - Dual-mode content: text + visual context
    """
    
    @property
    def supported_extensions(self) -> List[str]:
        return [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".gif"]
    
    @property
    def doc_type(self) -> str:
        return "image"
    
    def __init__(
        self,
        chunker: Optional[Chunker] = None,
        use_ocr: bool = True,
        use_vision: bool = True,
        extract_tables: bool = True
    ):
        """
        Initialize image processor.
        
        Args:
            use_ocr: Extract text using OCR
            use_vision: Generate visual descriptions
            extract_tables: Detect and extract tables from images
        """
        self.chunker = chunker or Chunker()
        self.use_ocr = use_ocr
        self.use_vision = use_vision
        self.extract_tables = extract_tables
        self._ocr = None
        self._ollama = None
    
    def _get_ocr(self):
        """Lazy load OCR engine (DeepSeek)"""
        if self._ocr is None and self.use_ocr:
            try:
                from ..ocr import DeepSeekOCR
                self._ocr = DeepSeekOCR()
                if not self._ocr.is_available():
                    logger.warning("DeepSeek model not found, OCR disabled")
                    self._ocr = None
            except ImportError:
                logger.warning("OCR module not available")
                self._ocr = None
            except Exception as e:
                logger.warning(f"OCR init failed: {e}")
                self._ocr = None
        return self._ocr
    
    def _get_ollama(self):
        """Lazy load Ollama client for vision"""
        if self._ollama is None and self.use_vision:
            try:
                import ollama
                self._ollama = ollama
            except ImportError:
                logger.warning("Ollama not installed, vision disabled")
        return self._ollama
    
    def process(self, file_path: Path, document_id: Optional[str] = None) -> List[Chunk]:
        """Process an image file and extract chunks."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Image file not found: {file_path}")
        
        document_id = document_id or self._generate_document_id(file_path)
        chunks: List[Chunk] = []
        
        # Extract image metadata
        img_metadata = self._get_image_metadata(file_path)
        
        # OCR: Extract text from image
        if self.use_ocr:
            ocr_chunks = self._extract_ocr_content(file_path, document_id, img_metadata)
            chunks.extend(ocr_chunks)
        
        # Vision: Get visual description
        if self.use_vision:
            vision_chunks = self._extract_visual_content(file_path, document_id, img_metadata)
            chunks.extend(vision_chunks)
        
        # If no content extracted, create placeholder
        if not chunks:
            chunks.append(Chunk(
                content=f"[Image: {file_path.name}]\n\nNo text or content could be extracted from this image.",
                document_id=document_id,
                doc_type=self.doc_type,
                source_file=str(file_path),
                metadata={
                    **img_metadata,
                    "content_type": "placeholder"
                }
            ))
        
        return chunks
    
    def _get_image_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract image metadata."""
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "file_size": file_path.stat().st_size
                }
        except ImportError:
            return {"file_size": file_path.stat().st_size}
        except Exception:
            return {}
    
    def _extract_ocr_content(
        self, 
        file_path: Path, 
        document_id: str,
        img_metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """Extract OCR text and tables from image."""
        chunks = []
        ocr = self._get_ocr()
        
        if ocr is None:
            return chunks
        
        try:
            # Full content extraction (text + tables)
            content = ocr.extract_full_content(file_path)
            
            # Text chunks
            text = content.get("text", "").strip()
            if text:
                text_chunks = self.chunker.chunk(text)
                for idx, chunk_text in enumerate(text_chunks):
                    chunks.append(Chunk(
                        content=f"[OCR Text from Image]\n\n{chunk_text}",
                        document_id=document_id,
                        doc_type=self.doc_type,
                        source_file=str(file_path),
                        metadata={
                            **img_metadata,
                            "content_type": "ocr_text",
                            "chunk_index": idx,
                            "extraction_method": "deepseek"
                        }
                    ))
            
            # Table chunks
            if self.extract_tables:
                for table_idx, table_md in enumerate(content.get("tables", [])):
                    # Chunk large tables
                    table_chunks = self.chunker.chunk(table_md)
                    
                    for chunk_idx, chunk_text in enumerate(table_chunks):
                        chunks.append(Chunk(
                            content=f"[Table {table_idx + 1} from Image]\n\n{chunk_text}",
                            document_id=document_id,
                            doc_type=self.doc_type,
                            source_file=str(file_path),
                            metadata={
                                **img_metadata,
                                "content_type": "table",
                                "table_index": table_idx,
                                "chunk_index": chunk_idx,
                                "extraction_method": "deepseek"
                            }
                        ))
        
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
        
        return chunks
    
    def _extract_visual_content(
        self, 
        file_path: Path, 
        document_id: str,
        img_metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """Extract visual description using vision model."""
        chunks = []
        
        # Try DeepSeek OCR for visual description first
        ocr = self._get_ocr()
        if ocr:
            try:
                description = ocr.get_visual_description(file_path)
                if description:
                    chunks.append(Chunk(
                        content=f"[Visual Description]\n\n{description}",
                        document_id=document_id,
                        doc_type=self.doc_type,
                        source_file=str(file_path),
                        metadata={
                            **img_metadata,
                            "content_type": "visual_description",
                            "model": "deepseek-ocr",
                            "extraction_method": "vision"
                        }
                    ))
                    return chunks
            except Exception as e:
                logger.debug(f"DeepSeek vision failed: {e}")
        
        # Fallback to LLaVA or other vision model
        ollama = self._get_ollama()
        if ollama is None:
            return chunks
        
        try:
            # Encode image
            with open(file_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
            
            # Call vision model
            response = ollama.chat(
                model=getattr(config, 'VISION_MODEL', 'llava'),
                messages=[{
                    "role": "user",
                    "content": (
                        "Describe this image in detail for a document search system. Include:\n"
                        "1. Main subject and objects\n"
                        "2. Any diagrams, charts, or graphs\n"
                        "3. Colors and visual layout\n"
                        "4. Context clues about what this represents\n"
                        "Be comprehensive but concise."
                    ),
                    "images": [image_data]
                }],
                options={"temperature": 0.2}
            )
            
            description = response["message"]["content"]
            if description:
                desc_chunks = self.chunker.chunk(description)
                for idx, chunk_text in enumerate(desc_chunks):
                    chunks.append(Chunk(
                        content=f"[Visual Description]\n\n{chunk_text}",
                        document_id=document_id,
                        doc_type=self.doc_type,
                        source_file=str(file_path),
                        metadata={
                            **img_metadata,
                            "content_type": "visual_description",
                            "chunk_index": idx,
                            "model": getattr(config, 'VISION_MODEL', 'llava'),
                            "extraction_method": "vision"
                        }
                    ))
        
        except Exception as e:
            logger.error(f"Vision extraction failed: {e}")
        
        return chunks
    
    def get_combined_representation(self, file_path: Path) -> str:
        """
        Get combined text+visual representation for embedding.
        
        Useful for creating a unified embedding that captures both
        textual content and visual context.
        """
        chunks = self.process(file_path)
        
        parts = []
        for chunk in chunks:
            content = chunk.content
            content_type = chunk.metadata.get("content_type", "")
            
            if content_type == "ocr_text":
                parts.append(f"Text: {content}")
            elif content_type == "visual_description":
                parts.append(f"Visual: {content}")
            elif content_type == "table":
                parts.append(f"Table: {content}")
        
        return "\n\n".join(parts)
