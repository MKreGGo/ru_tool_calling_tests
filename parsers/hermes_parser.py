"""
Hermes/NousResearch format parser.

Handles the XML-style tool calling format used by Hermes and similar models.
"""

import re

from core.config import SYSTEM_PROMPTS, SYSTEM_PROMPTS_RU
from tools.schemas import ParsedToolCalls, ToolCall, ToolSchema

from .base import BaseResponseParser, ParseResult


class HermesParser(BaseResponseParser):
    """Parser for Hermes/NousResearch XML-style format."""
    
    format_name = "hermes"
    
    def parse(self, response_content: str, raw_response: dict | None = None) -> ParseResult:
        """
        Parse Hermes format tool calls.
        
        Expected format:
        <tool_call>
        {"name": "get_weather", "arguments": {"city": "Moscow"}}
        </tool_call>
        
        Or multiple calls:
        <tool_call>
        {"name": "get_weather", "arguments": {"city": "Moscow"}}
        </tool_call>
        <tool_call>
        {"name": "get_weather", "arguments": {"city": "Paris"}}
        </tool_call>
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
            # Find all <tool_call> blocks
            tool_call_pattern = r'<tool_call>\s*([\s\S]*?)\s*</tool_call>'
            matches = re.findall(tool_call_pattern, response_content, re.IGNORECASE)
            
            for match in matches:
                # Try to parse JSON from the match
                json_str = match.strip()
                
                # Handle case where JSON might be wrapped in quotes or have extra chars
                if not json_str.startswith('{'):
                    json_str = self._extract_json_from_text(json_str)
                
                if json_str:
                    data, err = self._safe_json_parse(json_str)
                    if err:
                        errors.append(f"Failed to parse tool_call content: {err}")
                        continue
                    
                    if isinstance(data, dict):
                        # Handle various key names
                        name = data.get("name", data.get("function", data.get("tool", "")))
                        args = data.get("arguments", data.get("args", data.get("parameters", {})))
                        
                        # If name is a dict (nested function format)
                        if isinstance(name, dict):
                            args = name.get("arguments", args)
                            name = name.get("name", "")
                        
                        # Arguments might be a string
                        if isinstance(args, str):
                            args, _ = self._safe_json_parse(args)
                            args = args or {}
                        
                        if name:
                            calls.append(ToolCall(
                                name=name,
                                arguments=args
                            ))
            
            # Also check for single tool_call without tags (some variations)
            if not calls:
                # Try to find JSON that looks like a tool call
                json_str = self._extract_json_from_text(response_content)
                if json_str:
                    data, err = self._safe_json_parse(json_str)
                    if data and isinstance(data, dict):
                        name = data.get("name", data.get("function", ""))
                        if name:
                            args = data.get("arguments", data.get("args", {}))
                            if isinstance(args, str):
                                args, _ = self._safe_json_parse(args)
                                args = args or {}
                            calls.append(ToolCall(
                                name=name,
                                arguments=args
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
        """Generate Hermes format system prompt with tool definitions in XML."""
        prompts = SYSTEM_PROMPTS_RU if language == "ru" else SYSTEM_PROMPTS
        base_prompt = prompts["hermes"]
        
        # Build tools XML block
        tools_xml = "<tools>\n"
        for tool in tools:
            tools_xml += tool.to_hermes_format(language=language) + "\n"
        tools_xml += "</tools>"
        
        return f"{base_prompt}\n\n{tools_xml}"
    
    def format_tools_for_api(self, tools: list[ToolSchema], language: str = "en") -> list[dict]:
        """
        Format tools for API.
        
        For Hermes, tools are typically passed in the system prompt,
        but we still return OpenAI format for compatibility.
        """
        return [tool.to_openai_format(language=language) for tool in tools]
