"""
Auto-detection parser.

Automatically detects the response format and uses the appropriate parser.
"""

from tools.schemas import ParsedToolCalls, ToolSchema

from .base import BaseResponseParser, ParseResult
from .openai_parser import OpenAIParser
from .anthropic_parser import AnthropicParser
from .mistral_parser import MistralParser
from .hermes_parser import HermesParser
from .raw_json_parser import RawJSONParser


class AutoParser(BaseResponseParser):
    """Parser that auto-detects response format."""
    
    format_name = "auto"
    
    def __init__(self):
        """Initialize with all available parsers."""
        self.parsers = {
            "openai": OpenAIParser(),
            "anthropic": AnthropicParser(),
            "mistral": MistralParser(),
            "hermes": HermesParser(),
            "raw_json": RawJSONParser(),
        }
        # Default parser for API formatting
        self._default_parser = OpenAIParser()
    
    def detect_format(self, response_content: str, raw_response: dict | None = None) -> str:
        """
        Detect the response format.
        
        Detection order:
        1. Check raw_response structure for OpenAI/Anthropic format
        2. Check text content for format-specific markers
        3. Fall back to raw_json
        """
        # Check structured response first
        if raw_response:
            # OpenAI format: choices[].message.tool_calls
            choices = raw_response.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                if "tool_calls" in message:
                    tool_calls = message["tool_calls"]
                    if tool_calls and len(tool_calls) > 0:
                        # Check if it's Mistral (arguments as dict vs string)
                        first_tc = tool_calls[0]
                        func = first_tc.get("function", {})
                        args = func.get("arguments", "")
                        if isinstance(args, dict):
                            return "mistral"
                        return "openai"
            
            # Anthropic format: content[].type == "tool_use"
            content = raw_response.get("content", [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_use":
                        return "anthropic"
        
        # Check text content for markers
        if response_content:
            # Hermes format: <tool_call> tags
            if "<tool_call>" in response_content.lower():
                return "hermes"
            
            # Anthropic text format: <tool_use> tags
            if "<tool_use>" in response_content.lower():
                return "anthropic"
            
            # Mistral format: [TOOL_CALLS] marker
            if "[TOOL_CALLS]" in response_content.upper():
                return "mistral"
        
        # Default to raw_json for generic JSON responses
        return "raw_json"
    
    def parse(self, response_content: str, raw_response: dict | None = None) -> ParseResult:
        """
        Auto-detect format and parse response.
        
        Tries detection first, then falls back to trying all parsers
        if the detected format fails.
        """
        detected_format = self.detect_format(response_content, raw_response)
        
        # Try detected parser first
        parser = self.parsers.get(detected_format, self.parsers["raw_json"])
        result = parser.parse(response_content, raw_response)
        
        if result.tool_calls.calls:
            # Update format name to include detection
            result.tool_calls.format_detected = f"auto:{detected_format}"
            return result
        
        # If detected parser found nothing, try others
        for format_name, other_parser in self.parsers.items():
            if format_name == detected_format:
                continue
            
            other_result = other_parser.parse(response_content, raw_response)
            if other_result.tool_calls.calls:
                other_result.tool_calls.format_detected = f"auto:{format_name}"
                return other_result
        
        # Return the original (empty) result
        result.tool_calls.format_detected = f"auto:{detected_format}:no_calls"
        return result
    
    def get_system_prompt(self, tools: list[ToolSchema], language: str = "en") -> str:
        """Use default (OpenAI) system prompt."""
        return self._default_parser.get_system_prompt(tools, language=language)
    
    def format_tools_for_api(self, tools: list[ToolSchema], language: str = "en") -> list[dict]:
        """Use default (OpenAI) format for API."""
        return self._default_parser.format_tools_for_api(tools, language=language)


def get_parser(format_name: str) -> BaseResponseParser:
    """
    Get a parser by format name.
    
    Args:
        format_name: One of "auto", "openai", "anthropic", "mistral", "hermes", "raw_json"
        
    Returns:
        Appropriate parser instance
    """
    parsers = {
        "auto": AutoParser,
        "openai": OpenAIParser,
        "anthropic": AnthropicParser,
        "mistral": MistralParser,
        "hermes": HermesParser,
        "raw_json": RawJSONParser,
    }
    
    parser_class = parsers.get(format_name.lower(), AutoParser)
    return parser_class()
