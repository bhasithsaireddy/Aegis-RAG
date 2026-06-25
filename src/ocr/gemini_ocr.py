"""Gemini OCR wrapper for text extraction in cloud environments"""
from pathlib import Path
from typing import Dict, List, Optional
import logging
from PIL import Image

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

from ..config import config

logger = logging.getLogger(__name__)


class GeminiOCR:
    """
    Gemini OCR wrapper for text, image, and table extraction.
    Used in cloud mode for superior vision capabilities.
    """
    
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        if genai is None:
            raise ImportError(
                "google-genai not installed. Install with: pip install google-genai"
            )
        
        self.model_name = model_name
        self.api_key = config.GEMINI_API_KEY
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. Gemini OCR will fail.")
            
        self.client = genai.Client(api_key=self.api_key)
    
    def is_available(self) -> bool:
        """Check if Gemini API is configured."""
        return bool(self.api_key) and genai is not None
        
    def _call_gemini(self, image_path: Path, prompt: str) -> str:
        """Call Gemini API with an image."""
        try:
            image = Image.open(image_path)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    prompt,
                    image
                ],
                config=types.GenerateContentConfig(
                    temperature=0.0,
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error for {image_path}: {e}")
            raise
    
    def extract_text(self, image_path: Path) -> str:
        """Extract plain text from an image using Gemini."""
        prompt = (
            "Extract all text from this image. "
            "Return only the extracted text without any additional commentary. "
            "Maintain the original text layout and structure. "
            "If there is no text, return an empty response."
        )
        try:
            text = self._call_gemini(image_path, prompt)
            return text.strip()
        except Exception as e:
            logger.error(f"Gemini text extraction failed for {image_path}: {e}")
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
            result = self._call_gemini(image_path, prompt)
            if not result.strip():
                return []
            
            tables = [
                table.strip()
                for table in result.split("\n\n")
                if "|" in table
            ]
            return tables
        except Exception as e:
            logger.error(f"Gemini table extraction failed for {image_path}: {e}")
            return []
        
    def extract_full_content(self, image_path: Path) -> Dict[str, any]:
        """Extract comprehensive content including text, tables, and structure."""
        prompt = (
            "Analyze this image and extract all content. Format your response exactly as follows:\n\n"
            "---TEXT---\n"
            "[All plain text found in the image, maintaining layout]\n\n"
            "---TABLES---\n"
            "[All tables found in the image, formatted as markdown. Separate multiple tables with blank lines]\n\n"
            "If a section (TEXT or TABLES) has no content, leave it blank under the header."
        )
        try:
            result = self._call_gemini(image_path, prompt)
            
            # Parse the response
            text_part = ""
            tables_part = ""
            
            if "---TEXT---" in result and "---TABLES---" in result:
                parts = result.split("---TABLES---")
                text_part = parts[0].replace("---TEXT---", "").strip()
                if len(parts) > 1:
                    tables_part = parts[1].strip()
            else:
                # Fallback if model ignored formatting
                text_part = result.strip()
                
            tables = [
                t.strip() 
                for t in tables_part.split("\n\n") 
                if "|" in t
            ]
            
            return {
                "text": text_part,
                "tables": tables,
                "has_tables": len(tables) > 0,
                "has_text": bool(text_part),
                "source": "gemini"
            }
        except Exception as e:
            logger.error(f"Gemini full extraction failed for {image_path}: {e}")
            return {
                "text": "",
                "tables": [],
                "has_tables": False,
                "has_text": False,
                "source": "gemini-error"
            }

    def get_visual_description(self, image_path: Path) -> str:
        """Extract visual description of the image."""
        prompt = (
            "Describe this image in detail. "
            "Focus on the main subjects, actions, setting, objects, and any notable visual characteristics. "
            "If it's a chart or diagram, explain what it shows. "
            "Do not include any extracted text, only describe the visual elements."
        )
        try:
            return self._call_gemini(image_path, prompt)
        except Exception as e:
            logger.error(f"Gemini visual description failed for {image_path}: {e}")
            return ""
