"""
Base response parser interface.

Abstract base class for all response format parsers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from tools.schemas import ParsedToolCalls, ToolSchema


@dataclass
class ParseResult:
    """Result of parsing an LLM response."""
    
    tool_calls: ParsedToolCalls
    success: bool
    format_name: str
    errors: list[str] = field(default_factory=list)


class BaseResponseParser(ABC):
    """Abstract base class for response parsers."""
    
    format_name: str = "base"
    
    @abstractmethod
    def parse(self, response_content: str, raw_response: dict | None = None) -> ParseResult:
        """
        Parse tool calls from LLM response.
        
        Args:
            response_content: The text content of the response
            raw_response: The full raw response dict (for structured formats)
            
        Returns:
            ParseResult with extracted tool calls
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self, tools: list[ToolSchema], language: str = "en") -> str:
        """
        Generate format-specific system prompt with tool definitions.
        
        Args:
            tools: List of tool schemas to include
            language: Language code ("en" or "ru")
            
        Returns:
            System prompt string
        """
        pass
    
    @abstractmethod
    def format_tools_for_api(self, tools: list[ToolSchema], language: str = "en") -> list[dict]:
        """
        Format tool schemas for the API request.
        
        Args:
            tools: List of tool schemas
            language: Language code ("en" or "ru")
            
        Returns:
            List of tool definitions in API format
        """
        pass
    
    def _safe_json_parse(self, text: str) -> tuple[Any, str | None]:
        """
        Safely parse JSON from text.
        
        Returns:
            Tuple of (parsed_data, error_message)
        """
        import json
        
        try:
            return json.loads(text), None
        except json.JSONDecodeError as e:
            return None, f"JSON parse error: {str(e)}"
    
    def _extract_json_from_text(self, text: str) -> str | None:
        """
        Try to extract JSON from text that may have other content.
        
        Looks for:
        - Content between ``` markers
        - Content between { } or [ ]
        """
        import re
        
        # Try to find JSON in code blocks
        code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if code_block_match:
            return code_block_match.group(1).strip()
        
        # Try to find JSON object
        brace_match = re.search(r'\{[\s\S]*\}', text)
        if brace_match:
            return brace_match.group(0)
        
        # Try to find JSON array
        bracket_match = re.search(r'\[[\s\S]*\]', text)
        if bracket_match:
            return bracket_match.group(0)
        
        return None
