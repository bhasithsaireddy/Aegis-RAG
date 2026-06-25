"""Tesseract OCR wrapper for text extraction in cloud environments"""
from pathlib import Path
from typing import Dict, List, Optional
import logging

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None

logger = logging.getLogger(__name__)

class TesseractOCR:
    """
    Tesseract OCR wrapper for text extraction.
    Used in cloud mode where Ollama vision models are unavailable.
    """
    
    def __init__(self):
        if pytesseract is None:
            raise ImportError(
                "pytesseract or Pillow not installed. Install with: pip install pytesseract Pillow"
            )
    
    def is_available(self) -> bool:
        """Check if Tesseract OCR is available."""
        return pytesseract is not None
    
    def extract_text(self, image_path: Path) -> str:
        """Extract plain text from an image using Tesseract."""
        try:
            img = Image.open(image_path)
            # Basic OCR
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception as e:
            logger.error(f"Tesseract text extraction failed for {image_path}: {e}")
            return ""
            
    def extract_tables(self, image_path: Path) -> List[str]:
        """Tesseract does not support markdown table extraction out of the box."""
        return []
        
    def extract_full_content(self, image_path: Path) -> Dict[str, any]:
        """
        Extract content. Tesseract only provides text.
        """
        text = self.extract_text(image_path)
        return {
            "text": text,
            "tables": [],
            "has_tables": False,
            "has_text": bool(text.strip()),
            "source": "tesseract"
        }
