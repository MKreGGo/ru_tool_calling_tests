"""
Anthropic Tool Use format parser.

Handles the Anthropic API format for tool calls.
"""

from core.config import SYSTEM_PROMPTS, SYSTEM_PROMPTS_RU
from tools.schemas import ParsedToolCalls, ToolCall, ToolSchema

from .base import BaseResponseParser, ParseResult


class AnthropicParser(BaseResponseParser):
    """Parser for Anthropic tool_use format."""
    
    format_name = "anthropic"
    
    def parse(self, response_content: str, raw_response: dict | None = None) -> ParseResult:
        """
        Parse Anthropic format tool calls.
        
        Expected format:
        {
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_01",
                    "name": "get_weather",
                    "input": {"city": "Moscow"}
                }
            ]
        }
        
        Or in text format (some local models):
        <tool_use>
        {"name": "get_weather", "input": {"city": "Moscow"}}
        </tool_use>
        """
        errors = []
        calls = []
        
        # Try structured response first
        if raw_response:
            try:
                # Direct Anthropic API format
                content = raw_response.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "tool_use":
                            calls.append(ToolCall(
                                name=item.get("name", ""),
                                arguments=item.get("input", {}),
                                id=item.get("id")
                            ))
                
                # OpenAI-compatible wrapper format (LM Studio)
                choices = raw_response.get("choices", [])
                if choices and not calls:
                    message = choices[0].get("message", {})
                    msg_content = message.get("content", "")
                    if msg_content:
                        response_content = msg_content
            except Exception as e:
                errors.append(f"Error parsing structured response: {str(e)}")
        
        # Parse from text content
        if not calls and response_content:
            import re
            
            # Look for <tool_use> tags
            tool_use_pattern = r'<tool_use>\s*([\s\S]*?)\s*</tool_use>'
            matches = re.findall(tool_use_pattern, response_content)
            
            for match in matches:
                data, err = self._safe_json_parse(match)
                if err:
                    # Try to extract JSON from the match
                    json_str = self._extract_json_from_text(match)
                    if json_str:
                        data, err = self._safe_json_parse(json_str)
                
                if data and isinstance(data, dict):
                    calls.append(ToolCall(
                        name=data.get("name", ""),
                        arguments=data.get("input", data.get("arguments", {})),
                        id=data.get("id")
                    ))
                elif err:
                    errors.append(f"Failed to parse tool_use content: {err}")
            
            # Also try standard JSON extraction as fallback
            if not calls:
                json_str = self._extract_json_from_text(response_content)
                if json_str:
                    data, err = self._safe_json_parse(json_str)
                    if data:
                        if isinstance(data, dict) and ("name" in data or "type" in data):
                            if data.get("type") == "tool_use" or "name" in data:
                                calls.append(ToolCall(
                                    name=data.get("name", ""),
                                    arguments=data.get("input", data.get("arguments", {}))
                                ))
                        elif isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict) and item.get("type") == "tool_use":
                                    calls.append(ToolCall(
                                        name=item.get("name", ""),
                                        arguments=item.get("input", {})
                                    ))
        
        parsed = ParsedToolCalls(
            calls=calls,
            raw_content=response_content,
            format_detected=self.format_name,
            parse_errors=errors
        )
        
        return ParseResult(
            tool_calls=parsed,
            success=len(calls) > 0 or len(errors) == 0,
            format_name=self.format_name,
            errors=errors
        )
    
    def get_system_prompt(self, tools: list[ToolSchema], language: str = "en") -> str:
        """Generate Anthropic format system prompt."""
        prompts = SYSTEM_PROMPTS_RU if language == "ru" else SYSTEM_PROMPTS
        return prompts["anthropic"]
    
    def format_tools_for_api(self, tools: list[ToolSchema], language: str = "en") -> list[dict]:
        """Format tools for Anthropic API."""
        return [tool.to_anthropic_format(language=language) for tool in tools]
