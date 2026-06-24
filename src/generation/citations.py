"""Citation engine for source attribution"""
from typing import List, Dict, Any, Optional
import re
from pathlib import Path


class CitationEngine:
    """Extract and format citations from RAG responses"""
    
    def __init__(self):
        """Initialize citation engine"""
        # Pattern to match source citations like [Source 1]
        self.citation_pattern = re.compile(r'\[Source (\d+)\]')
    
    def extract_citations(self, response: str) -> List[int]:
        """
        Extract source numbers from response.
        
        Args:
            response: LLM response text
            
        Returns:
            List of unique source numbers referenced
        """
        matches = self.citation_pattern.findall(response)
        return sorted(set(int(m) for m in matches))
    
    def format_sources(
        self,
        sources: List[Dict[str, Any]],
        cited_only: bool = False,
        response: str = None
    ) -> List[Dict[str, Any]]:
        """
        Format source information for display.
        
        Args:
            sources: List of source dictionaries
            cited_only: Only return sources that were cited
            response: Response text (required if cited_only=True)
            
        Returns:
            Formatted sources with citation info
        """
        if cited_only and response:
            cited_indices = self.extract_citations(response)
            sources = [s for s in sources if s.get("index") in cited_indices]
        
        formatted = []
        for source in sources:
            formatted_source = {
                "index": source.get("index"),
                "file": self._format_filename(source.get("source_file")),
                "type": source.get("doc_type", "unknown"),
                "similarity": round(source.get("similarity", 0) * 100, 1)
            }
            
            # Add location info
            location = self._format_location(source)
            if location:
                formatted_source["location"] = location
            
            formatted.append(formatted_source)
        
        return formatted
    
    def _format_filename(self, path: Optional[str]) -> str:
        """Extract filename from path"""
        if not path:
            return "Unknown"
        return Path(path).name
    
    def _format_location(self, source: Dict[str, Any]) -> Optional[str]:
        """Format location information"""
        parts = []
        
        if source.get("page"):
            parts.append(f"Page {source['page']}")
        
        if source.get("timestamp"):
            ts = source["timestamp"]
            start = ts.get("start", 0)
            end = ts.get("end")
            
            if end:
                parts.append(f"{self._format_time(start)} - {self._format_time(end)}")
            else:
                parts.append(f"at {self._format_time(start)}")
        
        if source.get("speaker"):
            parts.append(f"Speaker: {source['speaker']}")
        
        return ", ".join(parts) if parts else None
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as mm:ss"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    def add_citations_to_response(
        self,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> str:
        """
        Add source citations section to response.
        
        Args:
            response: LLM response
            sources: List of source info
            
        Returns:
            Response with citations section appended
        """
        cited = self.extract_citations(response)
        
        if not cited:
            return response
        
        # Build citations section
        lines = ["\n\n---\n**Sources:**"]
        
        for source in sources:
            if source.get("index") in cited:
                location = self._format_location(source)
                loc_str = f" ({location})" if location else ""
                lines.append(
                    f"[{source['index']}] {self._format_filename(source.get('source_file'))}{loc_str}"
                )
        
        return response + "\n".join(lines)
    
    def create_context_with_sources(
        self,
        results: List[Dict[str, Any]]
    ) -> tuple[str, List[Dict[str, Any]]]:
        """
        Create context string with source markers.
        
        Args:
            results: Retrieval results
            
        Returns:
            Tuple of (context string, sources list)
        """
        context_parts = []
        sources = []
        
        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            
            # Build source info
            source = {
                "index": i,
                "source_file": metadata.get("source_file"),
                "doc_type": metadata.get("doc_type"),
                "document_id": metadata.get("document_id"),
                "similarity": result.get("similarity", 0)
            }
            
            if metadata.get("page"):
                source["page"] = metadata["page"]
            if metadata.get("timestamp_start"):
                source["timestamp"] = {
                    "start": metadata["timestamp_start"],
                    "end": metadata.get("timestamp_end")
                }
            if metadata.get("speaker"):
                source["speaker"] = metadata["speaker"]
            
            sources.append(source)
            
            # Build context entry
            context_parts.append(f"[Source {i}]\n{result['content']}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        return context, sources
