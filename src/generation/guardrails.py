"""Lightweight guardrails for response validation"""
from typing import Dict, Any, List, Optional
import re


class Guardrails:
    """Lightweight guardrails for validating LLM responses"""
    
    def __init__(self):
        """Initialize guardrails"""
        # Patterns that might indicate hallucination
        self.uncertainty_phrases = [
            "i think",
            "i believe", 
            "probably",
            "might be",
            "could be",
            "i'm not sure",
            "i don't know"
        ]
        
        # Phrases indicating no context support
        self.no_info_phrases = [
            "i don't have enough information",
            "the context doesn't contain",
            "not mentioned in the context",
            "cannot find information"
        ]
    
    def validate(
        self,
        response: str,
        context: str = None,
        query: str = None
    ) -> Dict[str, Any]:
        """
        Validate a response.
        
        Args:
            response: The LLM response
            context: The context used (optional)
            query: The original query (optional)
            
        Returns:
            Validation result with passed status and warnings
        """
        result = {
            "passed": True,
            "warnings": [],
            "confidence": 1.0
        }
        
        response_lower = response.lower()
        
        # Check for empty response
        if not response.strip():
            result["passed"] = False
            result["warnings"].append("Empty response")
            result["confidence"] = 0.0
            return result
        
        # Check for uncertainty
        uncertainty_count = sum(
            1 for phrase in self.uncertainty_phrases 
            if phrase in response_lower
        )
        
        if uncertainty_count > 0:
            result["confidence"] -= 0.1 * uncertainty_count
            result["warnings"].append(f"Contains {uncertainty_count} uncertainty phrases")
        
        # Check if response indicates no information
        has_no_info = any(
            phrase in response_lower 
            for phrase in self.no_info_phrases
        )
        
        if has_no_info:
            result["warnings"].append("Response indicates insufficient context")
        
        # Check for citations if context was provided
        if context:
            has_citations = bool(re.search(r'\[Source \d+\]', response))
            if not has_citations and not has_no_info:
                result["warnings"].append("Response lacks source citations")
                result["confidence"] -= 0.1
        
        # Ensure confidence stays in bounds
        result["confidence"] = max(0.0, min(1.0, result["confidence"]))
        
        return result
    
    def filter_response(self, response: str) -> str:
        """
        Clean/filter a response.
        
        Args:
            response: The LLM response
            
        Returns:
            Filtered response
        """
        # Remove any markdown code blocks that shouldn't be there
        response = response.strip()
        
        # Remove excessive newlines
        response = re.sub(r'\n{3,}', '\n\n', response)
        
        return response
    
    def check_relevance(
        self,
        response: str,
        query: str,
        threshold: float = 0.3
    ) -> bool:
        """
        Basic relevance check between response and query.
        
        Args:
            response: The LLM response
            query: The original query
            threshold: Word overlap threshold
            
        Returns:
            True if response seems relevant
        """
        # Simple word overlap check
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        
        # Remove common words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "what", "how", "why", "when", "where", "who", "which"}
        query_words -= stop_words
        
        if not query_words:
            return True
        
        overlap = len(query_words.intersection(response_words))
        overlap_ratio = overlap / len(query_words)
        
        return overlap_ratio >= threshold
