"""
Mistral format parser.

Handles Mistral's tool calling format (similar to OpenAI but with variations).
"""

from core.config import SYSTEM_PROMPTS, SYSTEM_PROMPTS_RU
from tools.schemas import ParsedToolCalls, ToolCall, ToolSchema

from .base import BaseResponseParser, ParseResult


class MistralParser(BaseResponseParser):
    """Parser for Mistral tool calling format."""
    
    format_name = "mistral"
    
    def parse(self, response_content: str, raw_response: dict | None = None) -> ParseResult:
        """
        Parse Mistral format tool calls.
        
        Mistral uses a format similar to OpenAI but may have variations:
        - tool_calls in message
        - Sometimes uses [TOOL_CALLS] markers in text
        
        Expected structured format:
        {
            "choices": [{
                "message": {
                    "tool_calls": [
                        {
                            "function": {
                                "name": "get_weather",
                                "arguments": {"city": "Moscow"}  # May be dict, not string
                            }
                        }
                    ]
                }
            }]
        }
        """
        errors = []
        calls = []
        
        # Try structured response first
        if raw_response:
            try:
                choices = raw_response.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    tool_calls = message.get("tool_calls", [])
                    
                    for tc in tool_calls:
                        func = tc.get("function", {})
                        name = func.get("name", "")
                        args = func.get("arguments", {})
                        
                        # Mistral may provide arguments as dict or string
                        if isinstance(args, str):
                            args, err = self._safe_json_parse(args)
                            if err:
                                errors.append(f"Failed to parse arguments for {name}: {err}")
                                args = {}
                        
                        calls.append(ToolCall(
                            name=name,
                            arguments=args or {},
                            id=tc.get("id")
                        ))
            except Exception as e:
                errors.append(f"Error parsing structured response: {str(e)}")
        
        # Parse from text content
        if not calls and response_content:
            import re
            
            # Look for [TOOL_CALLS] markers (Mistral specific)
            tool_calls_pattern = r'\[TOOL_CALLS\]\s*([\s\S]*?)(?:\[/TOOL_CALLS\]|$)'
            match = re.search(tool_calls_pattern, response_content)
            
            if match:
                content = match.group(1).strip()
                data, err = self._safe_json_parse(content)
                if not err and data:
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                func = item.get("function", item)
                                calls.append(ToolCall(
                                    name=func.get("name", ""),
                                    arguments=func.get("arguments", {})
                                ))
                    elif isinstance(data, dict):
                        func = data.get("function", data)
                        calls.append(ToolCall(
                            name=func.get("name", ""),
                            arguments=func.get("arguments", {})
                        ))
            
            # Fallback to generic JSON extraction
            if not calls:
                json_str = self._extract_json_from_text(response_content)
                if json_str:
                    data, err = self._safe_json_parse(json_str)
                    if data:
                        if isinstance(data, dict):
                            # Handle {"name": ..., "arguments": ...} format
                            if "name" in data:
                                calls.append(ToolCall(
                                    name=data.get("name", ""),
                                    arguments=data.get("arguments", {})
                                ))
                            # Handle {"function": {"name": ..., "arguments": ...}} format
                            elif "function" in data:
                                func = data["function"]
                                calls.append(ToolCall(
                                    name=func.get("name", ""),
                                    arguments=func.get("arguments", {})
                                ))
                        elif isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict) and "name" in item:
                                    calls.append(ToolCall(
                                        name=item.get("name", ""),
                                        arguments=item.get("arguments", {})
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
        """Generate Mistral format system prompt."""
        prompts = SYSTEM_PROMPTS_RU if language == "ru" else SYSTEM_PROMPTS
        return prompts["mistral"]
    
    def format_tools_for_api(self, tools: list[ToolSchema], language: str = "en") -> list[dict]:
        """Format tools for Mistral API (OpenAI compatible)."""
        return [tool.to_openai_format(language=language) for tool in tools]
