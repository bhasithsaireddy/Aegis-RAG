"""DeepSeek OCR using Ollama vision model for text, image, and table extraction"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import base64
import logging
import time

try:
    import ollama
except ImportError:
    ollama = None

from ..config import config

logger = logging.getLogger(__name__)


class DeepSeekOCR:
    """
    DeepSeek OCR wrapper using Ollama for text, image, and table extraction.
    
    This class provides a unified interface for OCR operations using DeepSeek
    vision model running locally via Ollama.
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        host: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3
    ):
        """
        Initialize DeepSeek OCR.
        
        Args:
            model_name: DeepSeek model name in Ollama (default from config)
            host: Ollama host URL (default from config)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        if ollama is None:
            raise ImportError(
                "Ollama package not installed. Install with: pip install ollama"
            )
        
        self.model_name = model_name or getattr(config, 'DEEPSEEK_MODEL', 'deepseek-ocr')
        self.host = host or getattr(config, 'OLLAMA_HOST', 'http://localhost:11434')
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None
    
    def _get_client(self):
        """Lazy initialize Ollama client"""
        if self._client is None:
            self._client = ollama.Client(host=self.host)
        return self._client
    
    def _encode_image(self, image_path: Path) -> str:
        """Encode image to base64 string."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _call_vision_model(
        self,
        image_path: Path,
        prompt: str,
        retry_count: int = 0
    ) -> str:
        """Call DeepSeek vision model via Ollama with retry logic."""
        try:
            client = self._get_client()
            image_b64 = self._encode_image(image_path)
            
            options = {
                "temperature": 0.1,
                "num_predict": 4096,
                **getattr(config, 'OLLAMA_OPTIONS', {})
            }

            response = client.chat(
                model=self.model_name,
                messages=[{
                    "role": "user",
                    "content": prompt,
                    "images": [image_b64]
                }],
                options=options
            )
            
            return response["message"]["content"]
        
        except Exception as e:
            if retry_count < self.max_retries:
                logger.warning(f"OCR attempt {retry_count + 1} failed: {e}. Retrying...")
                time.sleep(1 * (retry_count + 1))
                return self._call_vision_model(image_path, prompt, retry_count + 1)
            else:
                logger.error(f"OCR failed after {self.max_retries} retries: {e}")
                raise
    
    def extract_text(self, image_path: Path) -> str:
        """Extract plain text from an image."""
        prompt = (
            "Extract all text from this image. "
            "Return only the extracted text without any additional commentary. "
            "Maintain the original text layout and structure. "
            "If there is no text, return an empty response."
        )
        
        try:
            text = self._call_vision_model(image_path, prompt)
            return text.strip()
        except Exception as e:
            logger.error(f"Text extraction failed for {image_path}: {e}")
            return ""
    
    def extract_tables(self, image_path: Path) -> List[str]:
        """Extract tables from an image in markdown format."""
        prompt = (
            "Identify and extract all tables from this image. "
            "For each table, convert it to markdown format with proper alignment. "
            "Return each table separately with a blank line between them. "
            "If there are no tables, return an empty response."
        )
        
        try:
            result = self._call_vision_model(image_path, prompt)
            
            if not result.strip():
                return []
            
            tables = [
                table.strip()
                for table in result.split("\n\n")
                if "|" in table
            ]
            
            return tables
        
        except Exception as e:
            logger.error(f"Table extraction failed for {image_path}: {e}")
            return []
    
    def extract_full_content(self, image_path: Path) -> Dict[str, any]:
        """
        Extract comprehensive content including text, tables, and structure.
        
        Returns:
            Dictionary with 'text', 'tables', and 'has_tables' keys
        """
        prompt = (
            "Analyze this image and extract all content:\n\n"
            "1. If there are tables, extract them in markdown format\n"
            "2. Extract all other text content\n\n"
            "Format your response as:\n"
            "TABLES:\n[markdown tables or 'None']\n\n"
            "TEXT:\n[all other text]\n\n"
            "Be precise and maintain structure."
        )
        
        try:
            result = self._call_vision_model(image_path, prompt)
            
            content = {"text": "", "tables": [], "has_tables": False}
            
            if "TABLES:" in result and "TEXT:" in result:
                parts = result.split("TEXT:")
                table_section = parts[0].replace("TABLES:", "").strip()
                text_section = parts[1].strip() if len(parts) > 1 else ""
                
                if table_section.lower() != "none" and "|" in table_section:
                    tables = [t.strip() for t in table_section.split("\n\n") if "|" in t]
                    content["tables"] = tables
                    content["has_tables"] = len(tables) > 0
                
                content["text"] = text_section
            else:
                content["text"] = result
            
            return content
        
        except Exception as e:
            logger.error(f"Full content extraction failed for {image_path}: {e}")
            return {"text": "", "tables": [], "has_tables": False}
    
    def get_visual_description(self, image_path: Path) -> str:
        """
        Get detailed visual description of an image for context understanding.
        
        Returns a rich description of what's in the image beyond just text.
        """
        prompt = (
            "Describe this image in detail for a document retrieval system. Include:\n"
            "1. Main subject/content of the image\n"
            "2. Any diagrams, charts, or visualizations\n"
            "3. Colors, layout, and visual structure\n"
            "4. Any text visible (summarize, don't transcribe)\n"
            "5. Context clues about what this image represents\n\n"
            "Be concise but comprehensive."
        )
        
        try:
            return self._call_vision_model(image_path, prompt)
        except Exception as e:
            logger.error(f"Visual description failed for {image_path}: {e}")
            return ""
    
    def extract_with_confidence(self, image_path: Path) -> Tuple[str, float]:
        """Extract text and estimate confidence level."""
        text = self.extract_text(image_path)
        
        confidence = 0.0
        if text:
            confidence = 0.7
            if any(char in text for char in ".!?"):
                confidence += 0.1
            if len(text.split()) > 5:
                confidence += 0.1
            if len(text.split()) < 3:
                confidence -= 0.2
            confidence = max(0.0, min(1.0, confidence))
        
        return text, confidence
    
    def is_available(self) -> bool:
        """Check if DeepSeek model is available in Ollama."""
        try:
            client = self._get_client()
            models = client.list()
            
            model_names = []
            for m in getattr(models, 'models', []):
                if hasattr(m, 'model'):
                    model_names.append(m.model)
                elif isinstance(m, dict):
                    model_names.append(m.get('name', ''))
            return any(self.model_name in name for name in model_names)
        
        except Exception as e:
            logger.error(f"Failed to check availability: {e}")
            return False
