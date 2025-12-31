"""
LLM Client for LM Studio.

OpenAI-compatible API client for making stateless tool calling requests.
"""

import time
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from core.config import BenchmarkConfig
from parsers.base import BaseResponseParser
from tools.schemas import ToolSchema


@dataclass
class LLMResponse:
    """Response from LLM API."""
    
    content: str
    raw_response: dict
    tool_calls_raw: list[dict]
    model: str
    usage: dict
    timing_ms: int
    error: str | None = None
    
    @property
    def prompt_tokens(self) -> int:
        """Get number of prompt (input) tokens."""
        return self.usage.get("prompt_tokens", 0)
    
    @property
    def completion_tokens(self) -> int:
        """Get number of completion (output) tokens."""
        return self.usage.get("completion_tokens", 0)
    
    @property
    def reasoning_tokens(self) -> int:
        """Get number of reasoning tokens (if available from API)."""
        # Some APIs like OpenAI o1 return this separately
        return self.usage.get("reasoning_tokens", 0)
    
    @property
    def total_tokens(self) -> int:
        """Get total tokens used."""
        return self.usage.get("total_tokens", 0)


class LLMClient:
    """Client for LM Studio (OpenAI-compatible) API."""
    
    def __init__(self, config: BenchmarkConfig):
        """
        Initialize LLM client.
        
        Args:
            config: Benchmark configuration with API settings
        """
        self.config = config
        self.client = OpenAI(
            base_url=config.api_url,
            api_key=config.api_key,
            timeout=config.request_timeout
        )
    
    def call_with_tools(
        self,
        user_prompt: str,
        tools: list[ToolSchema],
        system_prompt: str,
        temperature: float,
        parser: BaseResponseParser
    ) -> LLMResponse:
        """
        Make a single stateless call to the LLM.
        
        Each call is completely isolated - no conversation history is maintained.
        
        Args:
            user_prompt: The user's request
            tools: Available tools for this call
            system_prompt: System prompt (format-specific)
            temperature: Sampling temperature
            parser: Parser to format tools for API
            
        Returns:
            LLMResponse with content and metadata
        """
        start_time = time.time()
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Format tools for API
        tools_formatted = parser.format_tools_for_api(tools)
        
        try:
            # Make API call
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                tools=tools_formatted if tools_formatted else None,
                temperature=temperature,
                max_tokens=self.config.max_tokens
            )
            
            timing_ms = int((time.time() - start_time) * 1000)
            
            # Extract response data
            choice = response.choices[0]
            message = choice.message
            
            # Get content
            content = message.content or ""
            
            # Get tool calls if present
            tool_calls_raw = []
            if message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls_raw.append({
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    })
            
            # Build raw response dict
            raw_response = {
                "id": response.id,
                "model": response.model,
                "choices": [
                    {
                        "index": choice.index,
                        "message": {
                            "role": message.role,
                            "content": content,
                            "tool_calls": tool_calls_raw if tool_calls_raw else None
                        },
                        "finish_reason": choice.finish_reason
                    }
                ],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                } if response.usage else {}
            }
            
            return LLMResponse(
                content=content,
                raw_response=raw_response,
                tool_calls_raw=tool_calls_raw,
                model=response.model,
                usage=raw_response.get("usage", {}),
                timing_ms=timing_ms
            )
            
        except Exception as e:
            timing_ms = int((time.time() - start_time) * 1000)
            
            return LLMResponse(
                content="",
                raw_response={},
                tool_calls_raw=[],
                model=self.config.model,
                usage={},
                timing_ms=timing_ms,
                error=str(e)
            )
    
    def call_with_context(
        self,
        messages: list[dict],
        tools: list[ToolSchema],
        temperature: float,
        parser: BaseResponseParser
    ) -> LLMResponse:
        """
        Make a call to the LLM with full conversation context.
        
        Used for multi-turn testing where tool results need to be included.
        
        Args:
            messages: Full conversation history including tool results
            tools: Available tools for this call
            temperature: Sampling temperature
            parser: Parser to format tools for API
            
        Returns:
            LLMResponse with content and metadata
        """
        start_time = time.time()
        
        # Format tools for API
        tools_formatted = parser.format_tools_for_api(tools)
        
        try:
            # Make API call with full context
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                tools=tools_formatted if tools_formatted else None,
                temperature=temperature,
                max_tokens=self.config.max_tokens
            )
            
            timing_ms = int((time.time() - start_time) * 1000)
            
            # Extract response data
            choice = response.choices[0]
            message = choice.message
            
            # Get content
            content = message.content or ""
            
            # Get tool calls if present
            tool_calls_raw = []
            if message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls_raw.append({
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    })
            
            # Build raw response dict
            raw_response = {
                "id": response.id,
                "model": response.model,
                "choices": [
                    {
                        "index": choice.index,
                        "message": {
                            "role": message.role,
                            "content": content,
                            "tool_calls": tool_calls_raw if tool_calls_raw else None
                        },
                        "finish_reason": choice.finish_reason
                    }
                ],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                } if response.usage else {}
            }
            
            return LLMResponse(
                content=content,
                raw_response=raw_response,
                tool_calls_raw=tool_calls_raw,
                model=response.model,
                usage=raw_response.get("usage", {}),
                timing_ms=timing_ms
            )
            
        except Exception as e:
            timing_ms = int((time.time() - start_time) * 1000)
            
            return LLMResponse(
                content="",
                raw_response={},
                tool_calls_raw=[],
                model=self.config.model,
                usage={},
                timing_ms=timing_ms,
                error=str(e)
            )
    
    def test_connection(self) -> tuple[bool, str]:
        """
        Test connection to the LLM API.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Try to list models
            models = self.client.models.list()
            model_names = [m.id for m in models.data]
            
            if self.config.model in model_names:
                return True, f"Connected. Model '{self.config.model}' is available."
            else:
                available = ", ".join(model_names[:5])
                return True, f"Connected but model '{self.config.model}' not found. Available: {available}..."
                
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

