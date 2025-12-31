"""
Tool call validator.

Validates parsed tool calls against schemas and expected patterns.
"""

from dataclasses import dataclass, field
from typing import Any

from .schemas import ToolSchema, ToolCall, ParsedToolCalls
from .registry import TOOL_REGISTRY


@dataclass
class ValidationError:
    """A single validation error."""
    
    error_type: str  # "missing_tool", "invalid_arg", "missing_arg", "wrong_type", etc.
    message: str
    tool_name: str | None = None
    argument_name: str | None = None


@dataclass
class ValidationResult:
    """Result of validating tool calls."""
    
    success: bool
    errors: list[ValidationError] = field(default_factory=list)
    matched_calls: int = 0
    expected_calls: int = 0
    extra_calls: int = 0
    
    @property
    def score(self) -> float:
        """Calculate a score from 0.0 to 1.0."""
        if self.expected_calls == 0:
            return 1.0 if self.matched_calls == 0 else 0.0
        return self.matched_calls / self.expected_calls


@dataclass 
class ExpectedCall:
    """Expected tool call specification."""
    
    name: str
    args: dict[str, Any] | None = None
    strict_args: bool = False  # If True, args must match exactly
    keywords: dict[str, list[str | list[str]]] | None = None  # key -> [req1 AND [one of req2 OR]]


@dataclass
class ExpectedCalls:
    """Expected pattern of tool calls."""
    
    calls: list[ExpectedCall]
    mode: str = "exact"  # "exact", "sequential", "parallel", "subset"
    strict_format: bool = False  # If True, no conversational filler allowed
    
    @classmethod
    def from_dicts(cls, calls: list[dict], mode: str = "exact") -> "ExpectedCalls":
        """Create from list of dicts."""
        expected = []
        for c in calls:
            expected.append(ExpectedCall(
                name=c["name"],
                args=c.get("args"),
                strict_args=c.get("strict_args", False),
                keywords=c.get("keywords")
            ))
        return cls(calls=expected, mode=mode, strict_format=kwargs.get("strict_format", False))


class ToolValidator:
    """Validates tool calls against schemas and expected patterns."""
    
    def __init__(self, registry: dict[str, ToolSchema] | None = None):
        """
        Initialize validator.
        
        Args:
            registry: Tool registry to validate against. Uses default if not provided.
        """
        self.registry = registry or TOOL_REGISTRY
    
    def validate_single_call(self, call: ToolCall) -> ValidationResult:
        """
        Validate a single tool call against its schema.
        
        Checks:
        - Tool exists in registry
        - Required parameters are present
        - Parameter types are correct
        - Enum values are valid
        """
        errors = []
        
        # Check if tool exists
        if call.name not in self.registry:
            return ValidationResult(
                success=False,
                errors=[ValidationError(
                    error_type="unknown_tool",
                    message=f"Unknown tool: {call.name}",
                    tool_name=call.name
                )],
                matched_calls=0,
                expected_calls=1
            )
        
        schema = self.registry[call.name]
        
        # Check required parameters
        for param_name, param in schema.parameters.items():
            if param.required and param_name not in call.arguments:
                errors.append(ValidationError(
                    error_type="missing_required_arg",
                    message=f"Missing required argument: {param_name}",
                    tool_name=call.name,
                    argument_name=param_name
                ))
        
        # Validate provided arguments
        for arg_name, arg_value in call.arguments.items():
            if arg_name not in schema.parameters:
                # Extra argument - warning but not error
                continue
            
            param = schema.parameters[arg_name]
            
            # Type checking
            allowed_types = param.type if isinstance(param.type, list) else [param.type]
            type_valid = False
            
            for t in allowed_types:
                if t == "string" and isinstance(arg_value, str):
                    type_valid = True; break
                elif t == "integer" and isinstance(arg_value, int):
                    type_valid = True; break
                elif t == "number" and isinstance(arg_value, (int, float)):
                    type_valid = True; break
                elif t == "boolean" and isinstance(arg_value, bool):
                    type_valid = True; break
                elif t == "array" and isinstance(arg_value, list):
                    type_valid = True; break
                elif t == "object" and isinstance(arg_value, dict):
                    type_valid = True; break

            if not type_valid:
                errors.append(ValidationError(
                    error_type="wrong_type",
                    message=f"Argument '{arg_name}' should be {param.type}, got {type(arg_value).__name__}",
                    tool_name=call.name,
                    argument_name=arg_name
                ))
            
            # Enum validation
            if param.enum and isinstance(arg_value, str):
                if arg_value not in param.enum:
                    errors.append(ValidationError(
                        error_type="invalid_enum",
                        message=f"Argument '{arg_name}' value '{arg_value}' not in allowed values: {param.enum}",
                        tool_name=call.name,
                        argument_name=arg_name
                    ))
        
        return ValidationResult(
            success=len(errors) == 0,
            errors=errors,
            matched_calls=1 if len(errors) == 0 else 0,
            expected_calls=1
        )
    
    def validate_against_expected(
        self,
        parsed: ParsedToolCalls,
        expected: ExpectedCalls
    ) -> ValidationResult:
        """
        Validate parsed tool calls against expected pattern.
        
        Modes:
        - exact: Calls must match exactly in order and content
        - sequential: Calls must appear in order (but may have extras)
        - parallel: All expected calls must be present (order doesn't matter)
        - subset: At least one expected call must be present
        """
        errors = []
        matched = 0
        
        if parsed.is_empty and len(expected.calls) > 0:
            return ValidationResult(
                success=False,
                errors=[ValidationError(
                    error_type="no_tool_calls",
                    message="No tool calls found in response"
                )],
                matched_calls=0,
                expected_calls=len(expected.calls)
            )
        
        if expected.mode == "exact":
            matched, errors = self._validate_exact(parsed.calls, expected.calls)
        elif expected.mode == "sequential":
            matched, errors = self._validate_sequential(parsed.calls, expected.calls)
        elif expected.mode == "parallel":
            matched, errors = self._validate_parallel(parsed.calls, expected.calls)
        elif expected.mode == "subset":
            matched, errors = self._validate_subset(parsed.calls, expected.calls)
        else:
            errors.append(ValidationError(
                error_type="invalid_mode",
                message=f"Unknown validation mode: {expected.mode}"
            ))
        
        # Format Purity Check (for BFCL-4.5 and similar)
        if expected.strict_format and parsed.raw_content:
            # Strip XML tags if present (for Hermes)
            clean_content = parsed.raw_content.replace("<tool_call>", "").replace("</tool_call>", "").strip()
            # If after removing tool calls there is significant text remaining
            # We allow small amount of whitespace or newlines
            if len(clean_content) > 0:
                # Basic check: if the remaining text is not just a JSON-like string
                # This is a bit heuristic, but effective for 'conversational filler'
                # We count alpha-numeric characters outside of tool calls
                import re
                # Remove common JSON structures to see what's left
                text_only = re.sub(r'[\{\}\[\]\"\'\:\,\s\n\t]', '', clean_content)
                if len(text_only) > 5: # Threshold of 5 non-punctuation chars
                    errors.append(ValidationError(
                        error_type="format_pollution",
                        message=f"Response contains conversational filler or extra text: '{clean_content[:50]}...'"
                    ))
        
        # Also validate each call against schema
        for call in parsed.calls:
            schema_result = self.validate_single_call(call)
            if not schema_result.success:
                errors.extend(schema_result.errors)
        
        success = matched == len(expected.calls) and len(errors) == 0
        
        return ValidationResult(
            success=success,
            errors=errors,
            matched_calls=matched,
            expected_calls=len(expected.calls),
            extra_calls=max(0, len(parsed.calls) - len(expected.calls))
        )
    
    def _validate_exact(
        self,
        actual: list[ToolCall],
        expected: list[ExpectedCall]
    ) -> tuple[int, list[ValidationError]]:
        """Validate exact match of calls."""
        errors = []
        matched = 0
        
        if len(actual) != len(expected):
            errors.append(ValidationError(
                error_type="count_mismatch",
                message=f"Expected {len(expected)} calls, got {len(actual)}"
            ))
        
        for i, exp in enumerate(expected):
            if i >= len(actual):
                errors.append(ValidationError(
                    error_type="missing_call",
                    message=f"Missing expected call at position {i}: {exp.name}",
                    tool_name=exp.name
                ))
                continue
            
            act = actual[i]
            if act.matches(exp.name, exp.args, exp.strict_args, exp.keywords):
                matched += 1
            else:
                if act.name != exp.name:
                    errors.append(ValidationError(
                        error_type="wrong_tool",
                        message=f"Position {i}: expected {exp.name}, got {act.name}",
                        tool_name=act.name
                    ))
                else:
                    errors.append(ValidationError(
                        error_type="wrong_args",
                        message=f"Position {i}: {exp.name} arguments mismatch",
                        tool_name=act.name
                    ))
        
        return matched, errors
    
    def _validate_sequential(
        self,
        actual: list[ToolCall],
        expected: list[ExpectedCall]
    ) -> tuple[int, list[ValidationError]]:
        """Validate that expected calls appear in order (may have extras between)."""
        errors = []
        matched = 0
        exp_idx = 0
        
        for act in actual:
            if exp_idx >= len(expected):
                break
            
            exp = expected[exp_idx]
            if act.matches(exp.name, exp.args, exp.strict_args, exp.keywords):
                matched += 1
                exp_idx += 1
        
        if exp_idx < len(expected):
            missing = [e.name for e in expected[exp_idx:]]
            errors.append(ValidationError(
                error_type="missing_sequential",
                message=f"Missing sequential calls: {missing}"
            ))
        
        return matched, errors
    
    def _validate_parallel(
        self,
        actual: list[ToolCall],
        expected: list[ExpectedCall]
    ) -> tuple[int, list[ValidationError]]:
        """Validate that all expected calls are present (order doesn't matter)."""
        errors = []
        matched = 0
        
        expected_remaining = list(expected)
        
        for act in actual:
            for i, exp in enumerate(expected_remaining):
                if act.matches(exp.name, exp.args, exp.strict_args, exp.keywords):
                    matched += 1
                    expected_remaining.pop(i)
                    break
        
        if expected_remaining:
            missing = [e.name for e in expected_remaining]
            errors.append(ValidationError(
                error_type="missing_parallel",
                message=f"Missing parallel calls: {missing}"
            ))
        
        return matched, errors
    
    def _validate_subset(
        self,
        actual: list[ToolCall],
        expected: list[ExpectedCall]
    ) -> tuple[int, list[ValidationError]]:
        """Validate that at least one expected call is present."""
        errors = []
        matched = 0
        
        for exp in expected:
            for act in actual:
                if act.matches(exp.name, exp.args, exp.strict_args, exp.keywords):
                    matched += 1
                    break
        
        if matched == 0:
            errors.append(ValidationError(
                error_type="no_match",
                message="None of the expected calls were found"
            ))
        
        return matched, errors
