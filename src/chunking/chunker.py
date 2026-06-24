"""Semantic text chunking with overlap"""
from typing import List, Optional
import re

from ..config import config


class Chunker:
    """Split text into semantic chunks with configurable size and overlap"""
    
    def __init__(
        self, 
        chunk_size: int = None, 
        chunk_overlap: int = None,
        respect_sentences: bool = True
    ):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Target chunk size in tokens (default from config)
            chunk_overlap: Overlap between chunks in tokens (default from config)
            respect_sentences: Try to break at sentence boundaries
        """
        self.chunk_size = chunk_size or config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP
        self.respect_sentences = respect_sentences
        self._tokenizer = None
    
    def _get_tokenizer(self):
        """Lazy load tokenizer"""
        if self._tokenizer is None:
            try:
                import tiktoken
                self._tokenizer = tiktoken.get_encoding("cl100k_base")
            except ImportError:
                # Fallback to simple word-based tokenization
                self._tokenizer = None
        return self._tokenizer
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        tokenizer = self._get_tokenizer()
        if tokenizer:
            return len(tokenizer.encode(text))
        else:
            # Rough approximation: ~4 chars per token
            return len(text) // 4
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Pattern matches sentence endings
        pattern = r'(?<=[.!?])\s+'
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def chunk(self, text: str) -> List[str]:
        """
        Split text into chunks.
        
        Args:
            text: The text to chunk
            
        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []
        
        text = text.strip()
        
        # If text is small enough, return as single chunk
        if self._count_tokens(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        
        if self.respect_sentences:
            chunks = self._chunk_by_sentences(text)
        else:
            chunks = self._chunk_by_tokens(text)
        
        return chunks
    
    def _chunk_by_sentences(self, text: str) -> List[str]:
        """Create chunks respecting sentence boundaries"""
        sentences = self._split_into_sentences(text)
        
        if not sentences:
            return self._chunk_by_tokens(text)
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self._count_tokens(sentence)
            
            # If single sentence exceeds chunk size, split it
            if sentence_tokens > self.chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_tokens = 0
                
                # Split long sentence into smaller parts
                sub_chunks = self._chunk_by_tokens(sentence)
                chunks.extend(sub_chunks)
                continue
            
            # Check if adding this sentence exceeds limit
            if current_tokens + sentence_tokens > self.chunk_size:
                # Save current chunk
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                
                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(current_chunk)
                current_chunk = overlap_sentences + [sentence]
                current_tokens = sum(self._count_tokens(s) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _get_overlap_sentences(self, sentences: List[str]) -> List[str]:
        """Get sentences for overlap from the end of the chunk"""
        if not sentences or self.chunk_overlap <= 0:
            return []
        
        overlap_sentences = []
        overlap_tokens = 0
        
        for sentence in reversed(sentences):
            sentence_tokens = self._count_tokens(sentence)
            if overlap_tokens + sentence_tokens <= self.chunk_overlap:
                overlap_sentences.insert(0, sentence)
                overlap_tokens += sentence_tokens
            else:
                break
        
        return overlap_sentences
    
    def _chunk_by_tokens(self, text: str) -> List[str]:
        """Split text by token count (fallback method)"""
        tokenizer = self._get_tokenizer()
        
        if tokenizer:
            tokens = tokenizer.encode(text)
            chunks = []
            
            i = 0
            while i < len(tokens):
                end = min(i + self.chunk_size, len(tokens))
                chunk_tokens = tokens[i:end]
                chunk_text = tokenizer.decode(chunk_tokens)
                chunks.append(chunk_text)
                
                # Move forward with overlap
                i += self.chunk_size - self.chunk_overlap
            
            return chunks
        else:
            # Word-based fallback
            words = text.split()
            words_per_chunk = self.chunk_size * 4 // 5  # Rough estimate
            overlap_words = self.chunk_overlap * 4 // 5
            
            chunks = []
            i = 0
            while i < len(words):
                end = min(i + words_per_chunk, len(words))
                chunk = " ".join(words[i:end])
                chunks.append(chunk)
                i += words_per_chunk - overlap_words
            
            return chunks
