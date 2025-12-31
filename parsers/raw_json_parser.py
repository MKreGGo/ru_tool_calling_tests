"""
Raw JSON format parser.

Handles models that respond with plain JSON tool calls.
"""

from core.config import SYSTEM_PROMPTS, SYSTEM_PROMPTS_RU
from tools.schemas import ParsedToolCalls, ToolCall, ToolSchema

from .base import BaseResponseParser, ParseResult


class RawJSONParser(BaseResponseParser):
    """Parser for raw JSON tool call responses."""
    
    format_name = "raw_json"
    
    def parse(self, response_content: str, raw_response: dict | None = None) -> ParseResult:
        """
        Parse raw JSON tool calls.
        
        Supports multiple formats:
        
        1. Single call:
        {"tool": "get_weather", "arguments": {"city": "Moscow"}}
        
        2. Multiple calls:
        [
            {"tool": "get_weather", "arguments": {"city": "Moscow"}},
            {"tool": "get_weather", "arguments": {"city": "Paris"}}
        ]
        
        3. Alternative key names:
        {"name": "...", "args": {...}}
        {"function": "...", "parameters": {...}}
        {"action": "...", "input": {...}}
        """
        errors = []
        calls = []
        
        # Extract content from raw response if needed
        if raw_response:
            try:
                choices = raw_response.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    content = message.get("content", "")
                    if content:
                        response_content = content
            except Exception as e:
                errors.append(f"Error extracting content: {str(e)}")
        
        if response_content:
            # Try to extract and parse JSON
            json_str = self._extract_json_from_text(response_content)
            
            if not json_str:
                # Maybe the entire response is JSON
                json_str = response_content.strip()
            
            if json_str:
                data, err = self._safe_json_parse(json_str)
                
                if err:
                    errors.append(f"Failed to parse JSON: {err}")
                elif data:
                    # Handle array of calls
                    if isinstance(data, list):
                        for item in data:
                            call = self._extract_call_from_dict(item)
                            if call:
                                calls.append(call)
                    # Handle single call
                    elif isinstance(data, dict):
                        # Check if it's a wrapper with "calls" or "tool_calls" key
                        if "calls" in data:
                            for item in data["calls"]:
                                call = self._extract_call_from_dict(item)
                                if call:
                                    calls.append(call)
                        elif "tool_calls" in data:
                            for item in data["tool_calls"]:
                                call = self._extract_call_from_dict(item)
                                if call:
                                    calls.append(call)
                        else:
                            call = self._extract_call_from_dict(data)
                            if call:
                                calls.append(call)
        
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
    
    def _extract_call_from_dict(self, data: dict) -> ToolCall | None:
        """Extract a ToolCall from a dict with various key names."""
        if not isinstance(data, dict):
            return None
        
        # Try various key names for the tool name
        name = None
        for key in ["name", "tool", "function", "action", "tool_name", "function_name"]:
            if key in data:
                name = data[key]
                break
        
        if not name:
            # Maybe it's a nested structure
            if "function" in data and isinstance(data["function"], dict):
                name = data["function"].get("name", "")
            else:
                return None
        
        # Try various key names for arguments
        args = {}
        for key in ["arguments", "args", "parameters", "params", "input", "inputs"]:
            if key in data:
                args = data[key]
                break
        
        # If function is nested, get arguments from there
        if not args and "function" in data and isinstance(data["function"], dict):
            args = data["function"].get("arguments", {})
        
        # Arguments might be a string
        if isinstance(args, str):
            args, _ = self._safe_json_parse(args)
            args = args or {}
        
        if name:
            return ToolCall(name=name, arguments=args)
        
        return None
    
    def get_system_prompt(self, tools: list[ToolSchema], language: str = "en") -> str:
        """Generate system prompt for raw JSON format."""
        prompts = SYSTEM_PROMPTS_RU if language == "ru" else SYSTEM_PROMPTS
        base_prompt = prompts["raw_json"]
        
        # Add tool descriptions
        tools_header = "\n\nДоступные инструменты:\n" if language == "ru" else "\n\nAvailable tools:\n"
        req_label = " (обязательный)" if language == "ru" else " (required)"
        no_params_label = "    Без параметров" if language == "ru" else "    No parameters"
        params_label = "  Параметры:" if language == "ru" else "  Parameters:"
        
        tools_desc = tools_header
        for tool in tools:
            desc = tool.description_ru if language == "ru" and tool.description_ru else tool.description
            params_desc = []
            for pname, param in tool.parameters.items():
                pdesc = param.description_ru if language == "ru" and param.description_ru else param.description
                req = req_label if param.required else ""
                params_desc.append(f"    - {pname}: {param.type}{req} - {pdesc}")
            params_text = "\n".join(params_desc) if params_desc else no_params_label
            tools_desc += f"\n{tool.name}: {desc}\n{params_label}\n{params_text}\n"
        
        return base_prompt + tools_desc
    
    def format_tools_for_api(self, tools: list[ToolSchema], language: str = "en") -> list[dict]:
        """Format tools for API (OpenAI format for compatibility)."""
        return [tool.to_openai_format(language=language) for tool in tools]
