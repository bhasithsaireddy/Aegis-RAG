"""Advanced PDF document processor with text, table, image, and OCR extraction"""
from pathlib import Path
from typing import List, Optional, Dict, Any
import tempfile
import logging

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from .base import BaseProcessor, Chunk
from ..chunking import Chunker
from ..config import config

logger = logging.getLogger(__name__)


class PDFProcessor(BaseProcessor):
    """
    Advanced PDF processor with:
    - Native text extraction with layout
    - OCR fallback for scanned pages
    - Table detection and markdown conversion
    - Embedded image extraction with OCR
    - Metadata extraction
    """
    
    @property
    def supported_extensions(self) -> List[str]:
        return [".pdf"]
    
    @property
    def doc_type(self) -> str:
        return "pdf"
    
    def __init__(
        self,
        chunker: Optional[Chunker] = None,
        use_ocr: bool = True,
        extract_images: bool = True,
        extract_tables: bool = True
    ):
        """
        Initialize PDF processor.
        
        Args:
            chunker: Text chunker instance (uses default if not provided)
            use_ocr: Whether to use OCR for scanned pages
            extract_images: Whether to extract and OCR embedded images
            extract_tables: Whether to extract tables as markdown
        """
        if fitz is None:
            raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")
        
        self.chunker = chunker or Chunker()
        self.use_ocr = use_ocr
        self.extract_images = extract_images
        self.extract_tables = extract_tables
        self._ocr = None
    
    def _get_ocr(self):
        """Lazy load OCR engine"""
        if self._ocr is None and self.use_ocr:
            try:
                from ..ocr import DeepSeekOCR
                self._ocr = DeepSeekOCR()
                if not self._ocr.is_available():
                    logger.warning(f"DeepSeek model not found, OCR disabled")
                    self._ocr = None
            except ImportError as e:
                logger.warning(f"OCR not available: {e}")
                self._ocr = None
            except Exception as e:
                logger.warning(f"OCR initialization failed: {e}")
                self._ocr = None
        return self._ocr
    
    def process(self, file_path: Path, document_id: Optional[str] = None) -> List[Chunk]:
        """Process a PDF file and extract chunks."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        document_id = document_id or self._generate_document_id(file_path)
        chunks: List[Chunk] = []
        
        doc = fitz.open(file_path)
        
        # Extract document metadata
        doc_metadata = self._extract_metadata(doc, file_path)
        
        for page_num, page in enumerate(doc, start=1):
            # Extract native text
            text = page.get_text("text")
            is_scanned = not text.strip()
            ocr_content = {"text": "", "tables": []}
            
            # OCR fallback for scanned pages
            if is_scanned and self.use_ocr:
                ocr_content = self._ocr_page(page)
                text = ocr_content.get("text", "")
            
            # Process text content
            if text.strip():
                text_chunks = self.chunker.chunk(text)
                for idx, chunk_text in enumerate(text_chunks):
                    chunks.append(Chunk(
                        content=chunk_text,
                        document_id=document_id,
                        doc_type=self.doc_type,
                        source_file=str(file_path),
                        page=page_num,
                        metadata={
                            **doc_metadata,
                            "chunk_index": idx,
                            "total_page_chunks": len(text_chunks),
                            "extraction_method": "ocr" if is_scanned else "native"
                        }
                    ))
            
            # Extract tables (native PyMuPDF)
            if self.extract_tables and not is_scanned:
                table_chunks = self._extract_page_tables(page, document_id, file_path, page_num)
                chunks.extend(table_chunks)
            
            # Add OCR-extracted tables
            for table_idx, table_md in enumerate(ocr_content.get("tables", [])):
                # Chunk large tables
                table_chunks = self.chunker.chunk(table_md)
                
                for chunk_idx, chunk_text in enumerate(table_chunks):
                    chunks.append(Chunk(
                        content=f"[Table from scanned page]\n{chunk_text}",
                        document_id=document_id,
                        doc_type=self.doc_type,
                        source_file=str(file_path),
                        page=page_num,
                        metadata={
                            **doc_metadata,
                            "content_type": "table",
                            "table_index": table_idx,
                            "chunk_index": chunk_idx,
                            "extraction_method": "ocr"
                        }
                    ))
            
            # Extract embedded images
            if self.extract_images:
                image_chunks = self._extract_page_images(page, document_id, file_path, page_num, doc_metadata)
                chunks.extend(image_chunks)
        
        doc.close()
        return chunks
    
    def _extract_metadata(self, doc, file_path: Path) -> Dict[str, Any]:
        """Extract document metadata."""
        metadata = doc.metadata or {}
        return {
            "title": metadata.get("title", file_path.stem),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creator": metadata.get("creator", ""),
            "page_count": len(doc),
            "creation_date": metadata.get("creationDate", ""),
        }
    
    def _ocr_page(self, page) -> Dict[str, Any]:
        """Run OCR on a scanned page."""
        ocr = self._get_ocr()
        if ocr is None:
            return {"text": "", "tables": []}
        
        try:
            # Render page to image
            pix = page.get_pixmap(dpi=200)
            
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = Path(tmp.name)
                pix.save(str(tmp_path))
            
            try:
                content = ocr.extract_full_content(tmp_path)
                return {
                    "text": content.get("text", ""),
                    "tables": content.get("tables", [])
                }
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()
        
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return {"text": "", "tables": []}
    
    def _extract_page_tables(
        self, 
        page, 
        document_id: str, 
        file_path: Path, 
        page_num: int
    ) -> List[Chunk]:
        """Extract tables from page using PyMuPDF."""
        chunks = []
        
        try:
            tabs = page.find_tables()
            
            for table_idx, tab in enumerate(tabs):
                try:
                    df = tab.to_pandas()
                    if not df.empty:
                        md = df.to_markdown(index=False)
                        # Chunk large tables
                        table_chunks = self.chunker.chunk(md)
                        
                        for chunk_idx, chunk_text in enumerate(table_chunks):
                            chunks.append(Chunk(
                                content=f"[Table {table_idx + 1}]\n{chunk_text}",
                                document_id=document_id,
                                doc_type=self.doc_type,
                                source_file=str(file_path),
                                page=page_num,
                                metadata={
                                    "content_type": "table",
                                    "table_index": table_idx,
                                    "chunk_index": chunk_idx,
                                    "rows": len(df),
                                    "columns": len(df.columns),
                                    "extraction_method": "native"
                                }
                            ))
                except Exception:
                    pass
        except Exception:
            pass
        
        return chunks
    
    def _extract_page_images(
        self, 
        page, 
        document_id: str, 
        file_path: Path, 
        page_num: int,
        doc_metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """Extract and OCR embedded images from page."""
        chunks = []
        ocr = self._get_ocr()
        
        if ocr is None:
            return chunks
        
        try:
            image_list = page.get_images(full=True)
            
            for img_idx, img_info in enumerate(image_list):
                try:
                    xref = img_info[0]
                    base_image = page.parent.extract_image(xref)
                    
                    if base_image:
                        image_bytes = base_image["image"]
                        ext = base_image.get("ext", "png")
                        
                        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
                            tmp.write(image_bytes)
                            tmp_path = Path(tmp.name)
                        
                        try:
                            # Extract text from image
                            content = ocr.extract_full_content(tmp_path)
                            text = content.get("text", "").strip()
                            
                            if text:
                                # Chunk extracted text
                                text_chunks = self.chunker.chunk(text)
                                for idx, chunk_text in enumerate(text_chunks):
                                    chunks.append(Chunk(
                                        content=f"[Embedded Image Text]\n{chunk_text}",
                                        document_id=document_id,
                                        doc_type=self.doc_type,
                                        source_file=str(file_path),
                                        page=page_num,
                                        metadata={
                                            **doc_metadata,
                                            "content_type": "embedded_image_text",
                                            "image_index": img_idx,
                                            "chunk_index": idx,
                                            "extraction_method": "ocr"
                                        }
                                    ))
                            
                            # Get visual description
                            description = ocr.get_visual_description(tmp_path)
                            if description:
                                # Chunk description
                                desc_chunks = self.chunker.chunk(description)
                                for idx, chunk_text in enumerate(desc_chunks):
                                    chunks.append(Chunk(
                                        content=f"[Image Description]\n{chunk_text}",
                                        document_id=document_id,
                                        doc_type=self.doc_type,
                                        source_file=str(file_path),
                                        page=page_num,
                                        metadata={
                                            **doc_metadata,
                                            "content_type": "image_description",
                                            "image_index": img_idx,
                                            "chunk_index": idx,
                                            "extraction_method": "vision"
                                        }
                                    ))
                        finally:
                            if tmp_path.exists():
                                tmp_path.unlink()
                except Exception as e:
                    logger.debug(f"Failed to process image {img_idx}: {e}")
        except Exception as e:
            logger.debug(f"Failed to extract images: {e}")
        
        return chunks
