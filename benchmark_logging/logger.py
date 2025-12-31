"""
JSONL Logger for benchmark runs.

Logs each test run with full details for analysis.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class LogEntry:
    """A single log entry for one test run."""
    
    # Metadata
    timestamp: str
    model: str
    test_id: str
    level: int
    temperature: float
    run_index: int
    
    # Request details
    request: dict = field(default_factory=dict)
    # Expected: {system_prompt, user_prompt, tools}
    
    # Response details
    response: dict = field(default_factory=dict)
    # Expected: {raw_content, format_detected, parsed_tool_calls, parse_errors, timing_ms}
    
    # Validation details
    validation: dict = field(default_factory=dict)
    # Expected: {success, expected, actual, errors, score}
    
    # Token usage
    usage: dict = field(default_factory=dict)
    # Expected: {prompt_tokens, completion_tokens, reasoning_tokens, total_tokens}
    
    # Timing
    timing_ms: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class BenchmarkLogger:
    """JSONL logger for benchmark runs."""
    
    def __init__(self, output_path: str | Path):
        """
        Initialize logger.
        
        Args:
            output_path: Path to the JSONL log file
        """
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Open file for appending
        self._file = open(self.output_path, 'w', encoding='utf-8')
        self._entry_count = 0
    
    def log_run(
        self,
        model: str,
        test_id: str,
        level: int,
        temperature: float,
        run_index: int,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict],
        raw_content: str,
        format_detected: str,
        parsed_tool_calls: list[dict],
        parse_errors: list[str],
        validation_success: bool,
        expected_calls: list[dict],
        actual_calls: list[dict],
        validation_errors: list[str],
        validation_score: float,
        timing_ms: int,
        usage: dict = None  # NEW: Token usage
    ):
        """
        Log a single test run.
        
        Args:
            model: Model name
            test_id: Test case ID
            level: Difficulty level
            temperature: Sampling temperature
            run_index: Run number (0-indexed)
            system_prompt: System prompt sent
            user_prompt: User prompt sent
            tools: Tool schemas sent
            raw_content: Raw response content
            format_detected: Detected response format
            parsed_tool_calls: Parsed tool calls
            parse_errors: Parsing errors
            validation_success: Whether validation passed
            expected_calls: Expected tool calls
            actual_calls: Actual tool calls
            validation_errors: Validation errors
            validation_score: Validation score (0-1)
            timing_ms: API call timing in milliseconds
        """
        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            model=model,
            test_id=test_id,
            level=level,
            temperature=temperature,
            run_index=run_index,
            request={
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "tools": tools
            },
            response={
                "raw_content": raw_content,
                "format_detected": format_detected,
                "parsed_tool_calls": parsed_tool_calls,
                "parse_errors": parse_errors
            },
            validation={
                "success": validation_success,
                "expected": expected_calls,
                "actual": actual_calls,
                "errors": validation_errors,
                "score": validation_score
            },
            usage=usage or {},
            timing_ms=timing_ms
        )
        
        self._write_entry(entry)
    
    def log_entry(self, entry: LogEntry):
        """Log a pre-built entry."""
        self._write_entry(entry)
    
    def _write_entry(self, entry: LogEntry):
        """Write entry to file."""
        self._file.write(entry.to_json() + "\n")
        self._file.flush()
        self._entry_count += 1
    
    def log_metadata(self, metadata: dict):
        """Log benchmark metadata as first entry."""
        meta_entry = {
            "_type": "metadata",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **metadata
        }
        self._file.write(json.dumps(meta_entry, ensure_ascii=False) + "\n")
        self._file.flush()
    
    def get_entry_count(self) -> int:
        """Get number of entries logged."""
        return self._entry_count
    
    def close(self):
        """Close the log file."""
        if self._file:
            self._file.close()
            self._file = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
