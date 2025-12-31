"""
Tool schemas and data models.

Pydantic models for tool definitions and parsed tool calls.
"""

from typing import Any
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Definition of a single tool parameter."""
    
    type: str | list[str] = Field(description="Parameter type or list of types (union)")
    description: str = Field(description="Human-readable description of the parameter")
    description_ru: str | None = Field(default=None, description="Russian description")
    required: bool = Field(default=False, description="Whether the parameter is required")
    enum: list[str] | None = Field(default=None, description="Allowed values for enum parameters")
    default: Any = Field(default=None, description="Default value if not provided")
    items: dict | None = Field(default=None, description="Schema for array items")
    
    def get_description(self, language: str = "en") -> str:
        """Get description in specified language."""
        if language == "ru" and self.description_ru:
            return self.description_ru
        return self.description


class ToolSchema(BaseModel):
    """Schema definition for a fake tool."""
    
    name: str = Field(description="Unique tool name")
    description: str = Field(description="Human-readable description of what the tool does")
    description_ru: str | None = Field(default=None, description="Russian description")
    parameters: dict[str, ToolParameter] = Field(
        default_factory=dict,
        description="Map of parameter names to their definitions"
    )
    
    def get_description(self, language: str = "en") -> str:
        """Get description in specified language."""
        if language == "ru" and self.description_ru:
            return self.description_ru
        return self.description
    
    def to_openai_format(self, language: str = "en") -> dict:
        """Convert to OpenAI function calling format."""
        properties = {}
        required = []
        
        for param_name, param in self.parameters.items():
            prop = {
                "type": param.type,
                "description": param.get_description(language),
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default
            if param.items:
                prop["items"] = param.items
                
            properties[param_name] = prop
            
            if param.required:
                required.append(param_name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.get_description(language),
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }
            }
        }
    
    def to_anthropic_format(self, language: str = "en") -> dict:
        """Convert to Anthropic tool format."""
        properties = {}
        required = []
        
        for param_name, param in self.parameters.items():
            prop = {
                "type": param.type,
                "description": param.get_description(language),
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.items:
                prop["items"] = param.items
                
            properties[param_name] = prop
            
            if param.required:
                required.append(param_name)
        
        return {
            "name": self.name,
            "description": self.get_description(language),
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            }
        }
    
    def to_hermes_format(self, language: str = "en") -> str:
        """Convert to Hermes XML format for system prompt."""
        req_label = " (обязательный)" if language == "ru" else " (required)"
        enum_prefix = ", допустимые значения: " if language == "ru" else ", allowed values: "
        no_params = "  Без параметров" if language == "ru" else "  No parameters"
        
        params_desc = []
        for param_name, param in self.parameters.items():
            req_str = req_label if param.required else ""
            enum_str = f"{enum_prefix}{param.enum}" if param.enum else ""
            pdesc = param.get_description(language)
            params_desc.append(f"  - {param_name}: {param.type}{req_str} - {pdesc}{enum_str}")
        
        params_text = "\n".join(params_desc) if params_desc else no_params
        desc = self.get_description(language)
        
        return f"""<tool>
  <name>{self.name}</name>
  <description>{desc}</description>
  <parameters>
{params_text}
  </parameters>
</tool>"""


class ToolCall(BaseModel):
    """A single parsed tool call."""
    
    name: str = Field(description="Name of the tool being called")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Arguments passed to the tool")
    id: str | None = Field(default=None, description="Optional call ID from the LLM")
    
    def matches(self, expected_name: str, expected_args: dict[str, Any] | None = None, strict: bool = False, keywords: dict[str, Any] | None = None) -> bool:
        """
        Check if this call matches expected name and arguments.
        
        Args:
            expected_name: Expected tool name
            expected_args: Expected arguments (if None, only name is checked)
            strict: If True, arguments must match exactly. If False, expected args must be subset.
            keywords: If provided, checks if arguments contain specified keywords.
        """
        if self.name != expected_name:
            return False
        
        if expected_args is None and keywords is None:
            return True
        
        if strict:
            return self.arguments == expected_args
        
        # Check keywords if provided
        if keywords:
            for key, kws in keywords.items():
                if key not in self.arguments:
                    return False
                actual_val = str(self.arguments[key]).lower()
                for kw in kws:
                    if isinstance(kw, str):
                        # Required keyword (AND)
                        if kw.lower() not in actual_val:
                            return False
                    elif isinstance(kw, list):
                        # One of keywords required (OR)
                        if not any(sub_kw.lower() in actual_val for sub_kw in kw):
                            return False

        # Non-strict: check that all expected args are present with correct values
        if expected_args:
            for key, value in expected_args.items():
                if keywords and key in keywords:
                    continue # Skip if already checked by keywords
                
                if key not in self.arguments:
                    return False
                # Flexible string matching (case-insensitive, trimmed)
                if isinstance(value, str) and isinstance(self.arguments[key], str):
                    if value.lower().strip() != self.arguments[key].lower().strip():
                        return False
                elif self.arguments[key] != value:
                    return False
        
        return True


class ParsedToolCalls(BaseModel):
    """Collection of parsed tool calls from an LLM response."""
    
    calls: list[ToolCall] = Field(default_factory=list, description="List of parsed tool calls")
    raw_content: str = Field(default="", description="Original response content")
    format_detected: str = Field(default="unknown", description="Detected response format")
    parse_errors: list[str] = Field(default_factory=list, description="Any errors during parsing")
    
    @property
    def is_empty(self) -> bool:
        """Check if no tool calls were parsed."""
        return len(self.calls) == 0
    
    @property
    def has_errors(self) -> bool:
        """Check if there were parsing errors."""
        return len(self.parse_errors) > 0
    
    def get_tool_names(self) -> list[str]:
        """Get list of tool names called."""
        return [call.name for call in self.calls]
