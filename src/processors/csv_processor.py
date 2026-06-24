"""CSV file processor with schema detection and row chunking"""
from pathlib import Path
from typing import List, Optional, Dict, Any
import csv
import logging

from .base import BaseProcessor, Chunk

logger = logging.getLogger(__name__)


class CSVProcessor(BaseProcessor):
    """
    CSV processor with:
    - Schema detection (column names, types)
    - Row-based chunking with column context
    - Summary chunk with statistics
    - Large file streaming support
    """
    
    @property
    def supported_extensions(self) -> List[str]:
        return [".csv", ".tsv"]
    
    @property
    def doc_type(self) -> str:
        return "csv"
    
    def __init__(
        self,
        rows_per_chunk: int = 20,
        include_schema_chunk: bool = True,
        include_stats_chunk: bool = True,
        max_rows: Optional[int] = None
    ):
        """
        Initialize CSV processor.
        
        Args:
            rows_per_chunk: Number of rows per chunk
            include_schema_chunk: Add a schema description chunk
            include_stats_chunk: Add a statistics summary chunk
            max_rows: Maximum rows to process (None = all)
        """
        self.rows_per_chunk = rows_per_chunk
        self.include_schema_chunk = include_schema_chunk
        self.include_stats_chunk = include_stats_chunk
        self.max_rows = max_rows
    
    def process(self, file_path: Path, document_id: Optional[str] = None) -> List[Chunk]:
        """Process a CSV file and extract chunks."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        document_id = document_id or self._generate_document_id(file_path)
        chunks: List[Chunk] = []
        
        # Detect delimiter
        delimiter = "\t" if file_path.suffix.lower() == ".tsv" else ","
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                # Sniff the dialect
                sample = f.read(8192)
                f.seek(0)
                
                try:
                    dialect = csv.Sniffer().sniff(sample)
                    delimiter = dialect.delimiter
                except csv.Error:
                    pass
                
                reader = csv.DictReader(f, delimiter=delimiter)
                headers = reader.fieldnames or []
                
                if not headers:
                    return chunks
                
                # Collect metadata
                meta = {
                    "columns": headers,
                    "column_count": len(headers),
                    "delimiter": delimiter
                }
                
                # Schema chunk
                if self.include_schema_chunk:
                    schema_desc = self._create_schema_description(headers, file_path)
                    chunks.append(Chunk(
                        content=schema_desc,
                        document_id=document_id,
                        doc_type=self.doc_type,
                        source_file=str(file_path),
                        metadata={
                            **meta,
                            "content_type": "schema",
                            "chunk_index": 0
                        }
                    ))
                
                # Process rows in chunks
                row_buffer = []
                chunk_idx = 1
                total_rows = 0
                column_samples: Dict[str, List[str]] = {h: [] for h in headers}
                
                for row in reader:
                    if self.max_rows and total_rows >= self.max_rows:
                        break
                    
                    row_buffer.append(row)
                    total_rows += 1
                    
                    # Collect samples for stats
                    for h in headers:
                        val = row.get(h, "")
                        if val and len(column_samples[h]) < 100:
                            column_samples[h].append(val)
                    
                    # Chunk when buffer is full
                    if len(row_buffer) >= self.rows_per_chunk:
                        chunk_content = self._rows_to_markdown(headers, row_buffer, chunk_idx)
                        chunks.append(Chunk(
                            content=chunk_content,
                            document_id=document_id,
                            doc_type=self.doc_type,
                            source_file=str(file_path),
                            metadata={
                                **meta,
                                "content_type": "data",
                                "chunk_index": chunk_idx,
                                "row_start": (chunk_idx - 1) * self.rows_per_chunk + 1,
                                "row_end": total_rows
                            }
                        ))
                        row_buffer = []
                        chunk_idx += 1
                
                # Don't forget the last partial chunk
                if row_buffer:
                    chunk_content = self._rows_to_markdown(headers, row_buffer, chunk_idx)
                    chunks.append(Chunk(
                        content=chunk_content,
                        document_id=document_id,
                        doc_type=self.doc_type,
                        source_file=str(file_path),
                        metadata={
                            **meta,
                            "content_type": "data",
                            "chunk_index": chunk_idx,
                            "row_start": (chunk_idx - 1) * self.rows_per_chunk + 1,
                            "row_end": total_rows
                        }
                    ))
                
                # Stats chunk
                if self.include_stats_chunk:
                    stats_desc = self._create_stats_description(
                        headers, total_rows, column_samples, file_path
                    )
                    chunks.append(Chunk(
                        content=stats_desc,
                        document_id=document_id,
                        doc_type=self.doc_type,
                        source_file=str(file_path),
                        metadata={
                            **meta,
                            "content_type": "statistics",
                            "total_rows": total_rows,
                            "chunk_index": -1
                        }
                    ))
        
        except Exception as e:
            logger.error(f"CSV processing error: {e}")
        
        return chunks
    
    def _create_schema_description(self, headers: List[str], file_path: Path) -> str:
        """Create a schema description chunk."""
        lines = [
            f"[CSV Schema: {file_path.name}]",
            "",
            f"This CSV file has {len(headers)} columns:",
            ""
        ]
        
        for i, h in enumerate(headers, 1):
            lines.append(f"{i}. **{h}**")
        
        return "\n".join(lines)
    
    def _rows_to_markdown(
        self, 
        headers: List[str], 
        rows: List[Dict[str, str]], 
        chunk_idx: int
    ) -> str:
        """Convert rows to markdown table format."""
        lines = [f"[Data Chunk {chunk_idx}]", ""]
        
        # Header row
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        # Data rows
        for row in rows:
            cells = [str(row.get(h, "")).replace("|", "\\|")[:100] for h in headers]
            lines.append("| " + " | ".join(cells) + " |")
        
        return "\n".join(lines)
    
    def _create_stats_description(
        self,
        headers: List[str],
        total_rows: int,
        column_samples: Dict[str, List[str]],
        file_path: Path
    ) -> str:
        """Create a statistics summary chunk."""
        lines = [
            f"[CSV Statistics: {file_path.name}]",
            "",
            f"- **Total Rows**: {total_rows}",
            f"- **Columns**: {len(headers)}",
            "",
            "## Column Summary",
            ""
        ]
        
        for h in headers:
            samples = column_samples.get(h, [])
            
            # Infer type
            col_type = self._infer_column_type(samples)
            
            # Get unique count
            unique_count = len(set(samples))
            
            # Sample values
            sample_vals = list(set(samples))[:3]
            sample_str = ", ".join(f'"{v}"' for v in sample_vals) if sample_vals else "N/A"
            
            lines.append(f"### {h}")
            lines.append(f"- Type: {col_type}")
            lines.append(f"- Unique values: {unique_count}")
            lines.append(f"- Examples: {sample_str}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _infer_column_type(self, samples: List[str]) -> str:
        """Infer column data type from samples."""
        if not samples:
            return "unknown"
        
        # Check numeric
        numeric_count = 0
        for s in samples:
            try:
                float(s.replace(",", ""))
                numeric_count += 1
            except ValueError:
                pass
        
        if numeric_count > len(samples) * 0.8:
            return "numeric"
        
        # Check if mostly short (categorical)
        avg_len = sum(len(s) for s in samples) / len(samples)
        if avg_len < 20 and len(set(samples)) < len(samples) * 0.5:
            return "categorical"
        
        return "text"
