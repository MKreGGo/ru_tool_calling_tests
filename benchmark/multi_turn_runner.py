"""
Multi-turn benchmark runner.

Handles multi-turn test cases where the model must:
1. Call data-gathering tools first
2. Receive simulated results
3. Call action tools using the obtained data
"""

import json
from dataclasses import dataclass, field
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from core.config import BenchmarkConfig, get_system_prompt
from core.llm_client import LLMClient, LLMResponse
from parsers import get_parser, BaseResponseParser
from tools import ToolValidator, get_tools_by_names, get_bfcl_tools_by_names
from tools.schemas import ToolSchema, ToolCall
from tools.validator import ValidationResult, ExpectedCalls
from tests.multi_turn_tests import MultiTurnTestCase, ALL_MULTI_TURN_TESTS


@dataclass
class MultiTurnRunResult:
    """Result of a multi-turn test run."""
    
    test_id: str
    temperature: float
    run_index: int
    
    # Turn 1 results
    turn1_raw_content: str = ""
    turn1_parsed_calls: list[ToolCall] = field(default_factory=list)
    turn1_success: bool = False
    turn1_errors: list[str] = field(default_factory=list)
    turn1_timing_ms: int = 0
    
    # Turn 2 results (if applicable)
    turn2_raw_content: str = ""
    turn2_parsed_calls: list[ToolCall] = field(default_factory=list)
    turn2_success: bool = False
    turn2_errors: list[str] = field(default_factory=list)
    turn2_timing_ms: int = 0
    
    # Overall
    @property
    def success(self) -> bool:
        """Both turns must succeed for overall success."""
        return self.turn1_success and self.turn2_success
    
    @property
    def total_timing_ms(self) -> int:
        return self.turn1_timing_ms + self.turn2_timing_ms
    
    api_error: str | None = None


@dataclass
class MultiTurnTestResult:
    """Aggregated result for a multi-turn test case."""
    
    test_id: str
    level: int
    source: str = "custom"
    
    results_by_temp: dict[float, list[MultiTurnRunResult]] = field(default_factory=dict)
    
    @property
    def all_runs(self) -> list[MultiTurnRunResult]:
        runs = []
        for temp_runs in self.results_by_temp.values():
            runs.extend(temp_runs)
        return runs
    
    @property
    def total_runs(self) -> int:
        return len(self.all_runs)
    
    @property
    def successful_runs(self) -> int:
        return sum(1 for r in self.all_runs if r.success)
    
    @property
    def turn1_success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return sum(1 for r in self.all_runs if r.turn1_success) / self.total_runs
    
    @property
    def turn2_success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return sum(1 for r in self.all_runs if r.turn2_success) / self.total_runs
    
    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs


class MultiTurnRunner:
    """Runner for multi-turn sequential tests."""
    
    def __init__(
        self,
        config: BenchmarkConfig,
        logger: Any = None
    ):
        """
        Initialize multi-turn runner.
        
        Args:
            config: Benchmark configuration
            logger: Optional logger for recording runs
        """
        self.config = config
        self.logger = logger
        self.console = Console()
        
        # Initialize components
        self.llm_client = LLMClient(config)
        self.parser = get_parser(config.response_format)
        self.validator = ToolValidator()
    
    def get_multi_turn_tests(self, levels: list[int] | None = None) -> list[MultiTurnTestCase]:
        """Get multi-turn tests, optionally filtered by level."""
        tests = ALL_MULTI_TURN_TESTS
        if levels:
            tests = [t for t in tests if t.level in levels]
        return tests
    
    def run_multi_turn_benchmark(
        self,
        levels: list[int] | None = None
    ) -> list[MultiTurnTestResult]:
        """
        Run multi-turn benchmark.
        
        Args:
            levels: Optional list of levels to test (default: all)
            
        Returns:
            List of test results
        """
        tests = self.get_multi_turn_tests(levels)
        
        total_runs = len(tests) * len(self.config.temperatures) * self.config.runs_per_test
        
        self.console.print(f"\n[bold cyan]Multi-Turn Sequential Benchmark[/bold cyan]")
        self.console.print(f"Model: [yellow]{self.config.model}[/yellow]")
        self.console.print(f"Tests: {len(tests)} | Language: {self.config.language}")
        self.console.print(f"Total API calls: [bold]{total_runs * 2}[/bold] (2 turns per test)\n")
        
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task("Running multi-turn tests...", total=total_runs)
            
            for test in tests:
                test_result = MultiTurnTestResult(
                    test_id=test.id,
                    level=test.level,
                    source=test.source
                )
                
                for temp in self.config.temperatures:
                    temp_runs = []
                    
                    for run_idx in range(self.config.runs_per_test):
                        progress.update(
                            task,
                            description=f"[cyan]{test.id}[/cyan] T={temp} Run {run_idx+1}"
                        )
                        
                        run_result = self._run_multi_turn_test(test, temp, run_idx)
                        temp_runs.append(run_result)
                        
                        progress.advance(task)
                    
                    test_result.results_by_temp[temp] = temp_runs
                
                results.append(test_result)
        
        self.console.print("\n[bold green]✓ Multi-turn benchmark complete![/bold green]\n")
        self._print_summary(results)
        
        return results
    
    def _get_prompt(self, test: MultiTurnTestCase) -> str:
        """Get prompt in configured language."""
        if self.config.language == "ru":
            return test.prompt_ru
        return test.prompt_en
    
    def _get_turn2_context(self, test: MultiTurnTestCase) -> str:
        """Get turn 2 context in configured language."""
        if self.config.language == "ru":
            return test.turn2_context_ru
        return test.turn2_context_en
    
    def _run_multi_turn_test(
        self,
        test: MultiTurnTestCase,
        temperature: float,
        run_index: int
    ) -> MultiTurnRunResult:
        """Run a single multi-turn test."""
        result = MultiTurnRunResult(
            test_id=test.id,
            temperature=temperature,
            run_index=run_index
        )
        
        # Get tools
        tools = get_tools_by_names(test.available_tools)
        system_prompt = get_system_prompt(
            self.config.response_format if self.config.response_format != "auto" else "openai",
            self.config.language
        )
        prompt = self._get_prompt(test)
        
        # ===== TURN 1 =====
        response1 = self.llm_client.call_with_tools(
            user_prompt=prompt,
            tools=tools,
            system_prompt=system_prompt,
            temperature=temperature,
            parser=self.parser
        )
        
        result.turn1_timing_ms = response1.timing_ms
        
        if response1.error:
            result.api_error = response1.error
            result.turn1_errors.append(f"API Error: {response1.error}")
            return result
        
        # Parse turn 1 response
        parse_result1 = self.parser.parse(response1.content, response1.raw_response)
        result.turn1_raw_content = response1.content
        result.turn1_parsed_calls = parse_result1.tool_calls.calls
        
        # Validate turn 1
        validation1 = self.validator.validate_against_expected(
            parse_result1.tool_calls,
            test.expected_turn1
        )
        result.turn1_success = validation1.success
        result.turn1_errors = [e.message for e in validation1.errors]
        
        # If turn 1 failed or no turn 2 expected, stop here
        if not result.turn1_success or test.expected_turn2 is None:
            result.turn2_success = test.expected_turn2 is None  # Consider success if no turn 2
            return result
        
        # ===== TURN 2 =====
        # Build conversation context with simulated tool results
        messages = self._build_turn2_messages(
            system_prompt=system_prompt,
            user_prompt=prompt,
            turn1_response=response1,
            parsed_calls=result.turn1_parsed_calls,
            simulated_results=test.simulated_results,
            turn2_context=self._get_turn2_context(test)
        )
        
        response2 = self.llm_client.call_with_context(
            messages=messages,
            tools=tools,
            temperature=temperature,
            parser=self.parser
        )
        
        result.turn2_timing_ms = response2.timing_ms
        
        if response2.error:
            result.turn2_errors.append(f"API Error: {response2.error}")
            return result
        
        # Parse turn 2 response
        parse_result2 = self.parser.parse(response2.content, response2.raw_response)
        result.turn2_raw_content = response2.content
        result.turn2_parsed_calls = parse_result2.tool_calls.calls
        
        # Validate turn 2
        validation2 = self.validator.validate_against_expected(
            parse_result2.tool_calls,
            test.expected_turn2
        )
        result.turn2_success = validation2.success
        result.turn2_errors = [e.message for e in validation2.errors]
        
        return result
    
    def _build_turn2_messages(
        self,
        system_prompt: str,
        user_prompt: str,
        turn1_response: LLMResponse,
        parsed_calls: list[ToolCall],
        simulated_results: dict[str, str],
        turn2_context: str
    ) -> list[dict]:
        """Build message history for turn 2 including tool results."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Add assistant response with tool calls
        assistant_msg = {
            "role": "assistant",
            "content": turn1_response.content or None
        }
        
        if turn1_response.tool_calls_raw:
            assistant_msg["tool_calls"] = turn1_response.tool_calls_raw
        
        messages.append(assistant_msg)
        
        # Add simulated tool results
        for i, call in enumerate(parsed_calls):
            tool_call_id = f"call_{i}"
            if turn1_response.tool_calls_raw and i < len(turn1_response.tool_calls_raw):
                tool_call_id = turn1_response.tool_calls_raw[i].get("id", tool_call_id)
            
            # Find matching result (try exact match, then with suffix)
            result_content = simulated_results.get(call.name, "")
            if not result_content:
                # Try with argument-based suffix (e.g., get_weather_Moscow)
                for key, value in simulated_results.items():
                    if key.startswith(call.name):
                        result_content = value
                        break
            
            if not result_content:
                result_content = f'{{"status": "success", "result": "Simulated result for {call.name}"}}'
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": result_content
            })
        
        # Add context for continuing
        messages.append({
            "role": "user",
            "content": turn2_context
        })
        
        return messages
    
    def _print_summary(self, results: list[MultiTurnTestResult]):
        """Print summary of multi-turn results."""
        self.console.print("[bold]Multi-Turn Test Results:[/bold]")
        self.console.print()
        
        for r in results:
            status = "[green]✓[/green]" if r.success_rate > 0.5 else "[red]✗[/red]"
            self.console.print(
                f"  {status} {r.test_id}: "
                f"Turn1 {r.turn1_success_rate*100:.0f}% | "
                f"Turn2 {r.turn2_success_rate*100:.0f}% | "
                f"Overall {r.success_rate*100:.0f}%"
            )
        
        self.console.print()
        total_t1 = sum(r.turn1_success_rate for r in results) / len(results) * 100
        total_t2 = sum(r.turn2_success_rate for r in results) / len(results) * 100
        total = sum(r.success_rate for r in results) / len(results) * 100
        self.console.print(f"[bold]Average: Turn1 {total_t1:.1f}% | Turn2 {total_t2:.1f}% | Overall {total:.1f}%[/bold]")
