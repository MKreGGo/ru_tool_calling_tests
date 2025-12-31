from core.config import SYSTEM_PROMPTS, SYSTEM_PROMPTS_RU
from tools.schemas import ParsedToolCalls, ToolCall, ToolSchema

from .base import BaseResponseParser, ParseResult


class OpenAIParser(BaseResponseParser):
    """Parser for OpenAI function calling format."""
    
    format_name = "openai"
    
    def parse(self, response_content: str, raw_response: dict | None = None) -> ParseResult:
        """
        Parse OpenAI format tool calls.
        
        Expected format in raw_response:
        {
            "choices": [{
                "message": {
                    "tool_calls": [
                        {
                            "id": "call_abc123",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": "{\"city\": \"Moscow\"}"
                            }
                        }
                    ]
                }
            }]
        }
        """
        errors = []
        calls = []
        
        # Try to extract from structured response first
        if raw_response:
            try:
                choices = raw_response.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    tool_calls = message.get("tool_calls", [])
                    
                    for tc in tool_calls:
                        if tc.get("type") == "function":
                            func = tc.get("function", {})
                            name = func.get("name", "")
                            args_str = func.get("arguments", "{}")
                            
                            # Parse arguments JSON
                            args, err = self._safe_json_parse(args_str)
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
        
        # If no structured tool calls, try parsing from content
        if not calls and response_content:
            # Sometimes models put tool calls in content as JSON
            json_str = self._extract_json_from_text(response_content)
            if json_str:
                data, err = self._safe_json_parse(json_str)
                if data and not err:
                    if isinstance(data, dict) and "name" in data:
                        calls.append(ToolCall(
                            name=data.get("name", ""),
                            arguments=data.get("arguments", data.get("args", {}))
                        ))
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and "name" in item:
                                calls.append(ToolCall(
                                    name=item.get("name", ""),
                                    arguments=item.get("arguments", item.get("args", {}))
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
        """Generate OpenAI format system prompt."""
        prompts = SYSTEM_PROMPTS_RU if language == "ru" else SYSTEM_PROMPTS
        return prompts["openai"]
    
    def format_tools_for_api(self, tools: list[ToolSchema], language: str = "en") -> list[dict]:
        """Format tools for OpenAI API."""
        return [tool.to_openai_format(language=language) for tool in tools]
