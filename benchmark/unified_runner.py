"""
Unified benchmark runner.

Automatically uses appropriate execution mode based on test level:
- L1, L2, L4: Single-turn (одиночный запрос)
- L3, L5: Multi-turn (два запроса с симулированными результатами)
- BFCL L3 (3.1, 3.2): 3-turn multi-turn
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Union
from datetime import datetime

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from core.config import BenchmarkConfig, get_system_prompt
from core.llm_client import LLMClient, LLMResponse
from parsers import get_parser, BaseResponseParser
from tools import ToolValidator, get_tools_by_names, get_bfcl_tools_by_names, get_unified_registry
from tools.schemas import ToolSchema, ToolCall
from tools.validator import ValidationResult, ExpectedCalls
from tests.generator import TestCaseGenerator
from tests.test_cases import TestCase
from tests.multi_turn_tests import MultiTurnTestCase, MULTI_TURN_L3_TESTS, MULTI_TURN_L5_TESTS
from tests.bfcl_multi_turn_tests import BFCLMultiTurnTestCase, BFCL_MULTI_TURN_TESTS
from benchmark_logging.logger import LogEntry


# Build lookup for multi-turn tests by ID
MULTI_TURN_BY_ID = {t.id: t for t in MULTI_TURN_L3_TESTS + MULTI_TURN_L5_TESTS}
BFCL_MULTI_TURN_BY_ID = {t.id: t for t in BFCL_MULTI_TURN_TESTS}

# Levels that use multi-turn execution
MULTI_TURN_LEVELS = {3, 5}


@dataclass
class UnifiedRunResult:
    """Result of a test run (single or multi-turn)."""
    
    test_id: str
    temperature: float
    run_index: int
    is_multi_turn: bool = False
    num_turns: int = 1  # Track actual number of turns (1, 2, or 3)
    
    # Turn 1 (or single turn)
    turn1_raw_content: str = ""
    turn1_parsed_calls: list[ToolCall] = field(default_factory=list)
    turn1_success: bool = False
    turn1_errors: list[str] = field(default_factory=list)
    turn1_timing_ms: int = 0
    
    # Turn 2 (only for multi-turn)
    turn2_raw_content: str = ""
    turn2_parsed_calls: list[ToolCall] = field(default_factory=list)
    turn2_success: bool = False
    turn2_errors: list[str] = field(default_factory=list)
    turn2_timing_ms: int = 0
    
    # Turn 3 (only for 3-turn tests like BFCL-4.3)
    turn3_raw_content: str = ""
    turn3_parsed_calls: list[ToolCall] = field(default_factory=list)
    turn3_success: bool = False
    turn3_errors: list[str] = field(default_factory=list)
    turn3_timing_ms: int = 0
    
    api_error: str | None = None
    
    @property
    def success(self) -> bool:
        if self.num_turns >= 3:
            return self.turn1_success and self.turn2_success and self.turn3_success
        if self.is_multi_turn or self.num_turns == 2:
            return self.turn1_success and self.turn2_success
        return self.turn1_success
    
    @property
    def timing_ms(self) -> int:
        return self.turn1_timing_ms + self.turn2_timing_ms + self.turn3_timing_ms



@dataclass
class UnifiedTestResult:
    """Aggregated result for a test case."""
    
    test_id: str
    level: int
    source: str = "custom"
    is_multi_turn: bool = False
    
    results_by_temp: dict[float, list[UnifiedRunResult]] = field(default_factory=dict)
    
    @property
    def all_runs(self) -> list[UnifiedRunResult]:
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
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs
    
    @property
    def turn1_success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return sum(1 for r in self.all_runs if r.turn1_success) / self.total_runs
    
    @property
    def turn2_success_rate(self) -> float:
        if not self.is_multi_turn or self.total_runs == 0:
            return 0.0
        return sum(1 for r in self.all_runs if r.turn2_success) / self.total_runs


@dataclass
class UnifiedBenchmarkReport:
    """Complete benchmark report."""
    
    model: str
    config: BenchmarkConfig
    test_results: list[UnifiedTestResult] = field(default_factory=list)
    
    @property
    def total_tests(self) -> int:
        return len(self.test_results)
    
    @property
    def total_runs(self) -> int:
        return sum(r.total_runs for r in self.test_results)
    
    @property
    def overall_success_rate(self) -> float:
        total_success = sum(r.successful_runs for r in self.test_results)
        total_runs = self.total_runs
        if total_runs == 0:
            return 0.0
        return total_success / total_runs
    
    def get_level_success_rate(self, level: int) -> float:
        level_results = [r for r in self.test_results if r.level == level]
        if not level_results:
            return 0.0
        total_success = sum(r.successful_runs for r in level_results)
        total_runs = sum(r.total_runs for r in level_results)
        if total_runs == 0:
            return 0.0
        return total_success / total_runs


class UnifiedRunner:
    """
    Unified benchmark runner.
    
    Automatically uses:
    - Single-turn execution for L1, L2, L4
    - Multi-turn execution for L3, L5
    """
    
    def __init__(
        self,
        config: BenchmarkConfig,
        logger: Any = None
    ):
        self.config = config
        self.logger = logger
        self.console = Console()
        
        self.llm_client = LLMClient(config)
        self.parser = get_parser(config.response_format)
        self.validator = ToolValidator(registry=get_unified_registry())
        self.test_generator = TestCaseGenerator(
            suite=config.test_suite,
            language=config.language
        )
    
    def run_full_benchmark(self) -> UnifiedBenchmarkReport:
        """Run the complete benchmark with automatic mode selection."""
        
        # Get all tests from generator (already filtered by suite/lang)
        all_generator_tests = self.test_generator.get_tests_by_levels(self.config.levels)
        
        # Separate BFCL tests: exclude multi-turn ones from single-turn
        bfcl_multi_turn_ids = set(BFCL_MULTI_TURN_BY_ID.keys())
        single_tests = [t for t in all_generator_tests 
                        if (t.source == "bfcl" and t.id not in bfcl_multi_turn_ids) 
                        or (t.source == "custom" and t.level not in MULTI_TURN_LEVELS)]
        
        # Custom multi-turn tests (2-turn)
        custom_multi_tests = []
        if self.config.test_suite in ["custom", "all"]:
            multi_turn_levels = [l for l in self.config.levels if l in MULTI_TURN_LEVELS]
            for level in multi_turn_levels:
                if level == 3:
                    custom_multi_tests.extend(MULTI_TURN_L3_TESTS)
                elif level == 5:
                    custom_multi_tests.extend(MULTI_TURN_L5_TESTS)
        
        # BFCL multi-turn tests (2-turn or 3-turn)
        # L3: 3.1-3.5, L4: 4.3
        bfcl_multi_tests = []
        if self.config.test_suite in ["bfcl", "all"]:
            for test in BFCL_MULTI_TURN_TESTS:
                if test.level in self.config.levels:
                    bfcl_multi_tests.append(test)
        
        total_tests = len(single_tests) + len(custom_multi_tests) + len(bfcl_multi_tests)
        total_single_runs = len(single_tests) * len(self.config.temperatures) * self.config.runs_per_test
        total_custom_multi_runs = len(custom_multi_tests) * len(self.config.temperatures) * self.config.runs_per_test
        total_bfcl_multi_runs = len(bfcl_multi_tests) * len(self.config.temperatures) * self.config.runs_per_test
        # Custom = 2 calls, BFCL = 2-3 calls (dynamic)
        bfcl_api_calls = sum(t.num_turns for t in bfcl_multi_tests) * len(self.config.temperatures) * self.config.runs_per_test
        total_api_calls = total_single_runs + (total_custom_multi_runs * 2) + bfcl_api_calls
        
        self.console.print(f"\n[bold cyan]Unified Benchmark[/bold cyan]")
        self.console.print(f"Model: [yellow]{self.config.model}[/yellow]")
        self.console.print(f"Language: {self.config.language} | Levels: {self.config.levels}")
        self.console.print(f"Single: {len(single_tests)} | Custom MT: {len(custom_multi_tests)} | BFCL MT: {len(bfcl_multi_tests)}")
        self.console.print(f"Total API calls: [bold]{total_api_calls}[/bold]\n")
        
        report = UnifiedBenchmarkReport(model=self.config.model, config=self.config)
        
        total_runs = total_single_runs + total_custom_multi_runs + total_bfcl_multi_runs
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            # Log metadata
            if self.logger:
                self.logger.log_metadata({
                    "config": asdict(self.config),
                    "runner": "UnifiedRunner"
                })

            task = progress.add_task("Running benchmark...", total=total_runs)
            
            # Run single-turn tests
            for test in single_tests:
                test_result = UnifiedTestResult(
                    test_id=test.id,
                    level=test.level,
                    source=test.source,
                    is_multi_turn=False
                )
                
                for temp in self.config.temperatures:
                    temp_runs = []
                    for run_idx in range(self.config.runs_per_test):
                        progress.update(task, description=f"[cyan]{test.id}[/cyan] T={temp}")
                        run_result = self._run_single_turn(test, temp, run_idx)
                        temp_runs.append(run_result)
                        progress.advance(task)
                    test_result.results_by_temp[temp] = temp_runs
                
                report.test_results.append(test_result)
            
            # Run custom multi-turn tests (2-turn)
            for test in custom_multi_tests:
                test_result = UnifiedTestResult(
                    test_id=test.id,
                    level=test.level,
                    source=test.source,
                    is_multi_turn=True
                )
                
                for temp in self.config.temperatures:
                    temp_runs = []
                    for run_idx in range(self.config.runs_per_test):
                        progress.update(task, description=f"[magenta]{test.id}[/magenta] T={temp} (2-turn)")
                        run_result = self._run_multi_turn(test, temp, run_idx)
                        temp_runs.append(run_result)
                        progress.advance(task)
                    test_result.results_by_temp[temp] = temp_runs
                
                report.test_results.append(test_result)
            
            # Run BFCL multi-turn tests (3-turn)
            for test in bfcl_multi_tests:
                test_result = UnifiedTestResult(
                    test_id=test.id,
                    level=test.level,
                    source=test.source,
                    is_multi_turn=True
                )
                
                for temp in self.config.temperatures:
                    temp_runs = []
                    for run_idx in range(self.config.runs_per_test):
                        progress.update(task, description=f"[yellow]{test.id}[/yellow] T={temp} (3-turn)")
                        run_result = self._run_bfcl_multi_turn(test, temp, run_idx)
                        temp_runs.append(run_result)
                        progress.advance(task)
                    test_result.results_by_temp[temp] = temp_runs
                
                report.test_results.append(test_result)
        

        self.console.print("\n[bold green]✓ Benchmark complete![/bold green]")
        self._print_summary(report)
        
        return report
    
    def _get_prompt(self, test: Union[TestCase, MultiTurnTestCase]) -> str:
        if self.config.language == "ru":
            return test.prompt_ru
        return test.prompt_en
    
    def _get_tools(self, test: Union[TestCase, MultiTurnTestCase]) -> list[ToolSchema]:
        source = getattr(test, 'source', 'custom')
        if source == "bfcl":
            return get_bfcl_tools_by_names(test.available_tools)
        return get_tools_by_names(test.available_tools)
    
    def _get_failed_turn_expected_multi(self, test: MultiTurnTestCase, result: UnifiedRunResult) -> list:
        """Return expected calls for the turn that failed in multi-turn tests."""
        if not result.turn1_success:
            exp = test.get_expected_turn1(self.config.language)
            return [{"name": c.name, "args": c.args} for c in exp.calls]
        if hasattr(result, 'turn2_success') and not result.turn2_success:
            exp = test.get_expected_turn2(self.config.language)
            return [{"name": c.name, "args": c.args} for c in exp.calls] if exp else []
        return []
    
    def _get_failed_turn_actual_multi(self, result: UnifiedRunResult) -> list:
        """Return actual calls for the turn that failed in multi-turn tests."""
        if not result.turn1_success:
            return [c.model_dump() for c in result.turn1_parsed_calls]
        if hasattr(result, 'turn2_success') and not result.turn2_success:
            return [c.model_dump() for c in result.turn2_parsed_calls]
        return []
    
    def _get_failed_turn_expected_bfcl(self, test: BFCLMultiTurnTestCase, result: UnifiedRunResult) -> list:
        """Return expected calls for the turn that failed in BFCL multi-turn tests."""
        if not result.turn1_success:
            exp = test.get_expected_turn1(self.config.language)
            return [{"name": c.name, "args": c.args} for c in exp.calls]
        if hasattr(result, 'turn2_success') and not result.turn2_success:
            exp = test.get_expected_turn2(self.config.language)
            return [{"name": c.name, "args": c.args} for c in exp.calls] if exp else []
        if hasattr(result, 'turn3_success') and not result.turn3_success:
            exp = test.get_expected_turn3(self.config.language)
            return [{"name": c.name, "args": c.args} for c in exp.calls] if exp else []
        return []
    
    def _get_failed_turn_actual_bfcl(self, result: UnifiedRunResult) -> list:
        """Return actual calls for the turn that failed in BFCL multi-turn tests."""
        if not result.turn1_success:
            return [c.model_dump() for c in result.turn1_parsed_calls]
        if hasattr(result, 'turn2_success') and not result.turn2_success:
            return [c.model_dump() for c in result.turn2_parsed_calls]
        if hasattr(result, 'turn3_success') and not result.turn3_success:
            return [c.model_dump() for c in result.turn3_parsed_calls]
        return []

    def _run_single_turn(self, test: TestCase, temp: float, run_idx: int) -> UnifiedRunResult:
        """Run a single-turn test."""
        result = UnifiedRunResult(
            test_id=test.id,
            temperature=temp,
            run_index=run_idx,
            is_multi_turn=False
        )
        
        tools = self._get_tools(test)
        system_prompt = self.parser.get_system_prompt(tools)
        prompt = self._get_prompt(test)
        
        response = self.llm_client.call_with_tools(
            user_prompt=prompt,
            tools=tools,
            system_prompt=system_prompt,
            temperature=temp,
            parser=self.parser
        )
        
        result.turn1_timing_ms = response.timing_ms
        
        if response.error:
            result.api_error = response.error
            result.turn1_errors.append(f"API Error: {response.error}")
        else:
            parse_result = self.parser.parse(response.content, response.raw_response)
            result.turn1_raw_content = response.content
            result.turn1_parsed_calls = parse_result.tool_calls.calls
            
            validation = self.validator.validate_against_expected(
                parse_result.tool_calls,
                test.get_expected(self.config.language)
            )
            
            result.turn1_success = validation.success
            result.turn1_errors = [e.message for e in validation.errors]
        
        # Log result
        if self.logger:
            # Prepare data safely
            parse_result_safe = parse_result if not response.error else None
            parsed_calls_safe = [c.model_dump() for c in result.turn1_parsed_calls]
            parse_errors_safe = parse_result_safe.errors if parse_result_safe else []
            format_detected_safe = parse_result_safe.format_name if parse_result_safe else "unknown"

            self.logger.log_run(
                model=self.config.model,
                test_id=test.id,
                level=test.level,
                temperature=temp,
                run_index=run_idx,
                system_prompt=system_prompt,
                user_prompt=prompt,
                tools=[tool.to_openai_format(language=self.config.language) for tool in tools],
                raw_content=response.content,
                format_detected=format_detected_safe,
                parsed_tool_calls=parsed_calls_safe,
                parse_errors=parse_errors_safe,
                validation_success=result.turn1_success,
                expected_calls=[{"name": c.name, "args": c.args} for c in test.get_expected(self.config.language).calls],
                actual_calls=parsed_calls_safe,
                validation_errors=result.turn1_errors,
                validation_score=1.0 if result.turn1_success else 0.0,
                timing_ms=result.turn1_timing_ms,
                usage=response.usage  # NEW: Token usage
            )

        return result
    
    def _run_multi_turn(self, test: MultiTurnTestCase, temp: float, run_idx: int) -> UnifiedRunResult:
        """Run a multi-turn test."""
        result = UnifiedRunResult(
            test_id=test.id,
            temperature=temp,
            run_index=run_idx,
            is_multi_turn=True
        )
        
        tools = self._get_tools(test)
        system_prompt = get_system_prompt(
            self.config.response_format if self.config.response_format != "auto" else "openai",
            self.config.language,
            sequential=True  # Enable sequential instruction for multi-turn tests
        )
        prompt = self._get_prompt(test)
        
        # ===== TURN 1 =====
        response1 = self.llm_client.call_with_tools(
            user_prompt=prompt,
            tools=tools,
            system_prompt=system_prompt,
            temperature=temp,
            parser=self.parser
        )
        
        result.turn1_timing_ms = response1.timing_ms
        
        # Helper to finish and log
        def finish_and_log():
            if self.logger:
                # Use current state of result/response variables
                # For MT tests, we usually want the last response as the final one
                if result.num_turns >= 2:
                    response_final = response2 if 'response2' in locals() else response1
                else:
                    response_final = response1
                
                # Collect validation info from all turns
                errors = []
                errors.extend(result.turn1_errors)
                errors.extend(result.turn2_errors)
                errors.extend(result.turn3_errors)
                
                # Collect turns
                turns_data = []
                if result.turn1_raw_content or result.turn1_parsed_calls:
                    turns_data.append({
                        "raw_content": result.turn1_raw_content,
                        "parsed_tool_calls": [c.model_dump() for c in result.turn1_parsed_calls]
                    })
                if result.turn2_raw_content or result.turn2_parsed_calls:
                     turns_data.append({
                        "raw_content": result.turn2_raw_content,
                        "parsed_tool_calls": [c.model_dump() for c in result.turn2_parsed_calls]
                    })
                if result.turn3_raw_content or result.turn3_parsed_calls:
                     turns_data.append({
                        "raw_content": result.turn3_raw_content,
                        "parsed_tool_calls": [c.model_dump() for c in result.turn3_parsed_calls]
                    })

                # Determine format
                format_detected = "unknown"
                if 'parse_result2' in locals():
                    format_detected = parse_result2.format_name
                elif 'parse_result1' in locals():
                    format_detected = parse_result1.format_name

                # Collect parse errors
                parse_errors = []
                if 'parse_result1' in locals():
                    parse_errors.extend(parse_result1.errors)
                if 'parse_result2' in locals():
                    parse_errors.extend(parse_result2.errors)

                # Usage and Timing are already aggregated in result or can be derived
                total_usage = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "reasoning_tokens": 0,
                    "total_tokens": 0
                }
                if 'response1' in locals():
                    for key in total_usage:
                        total_usage[key] += response1.usage.get(key, 0)
                if 'response2' in locals():
                    for key in total_usage:
                        total_usage[key] += response2.usage.get(key, 0)

                entry = LogEntry(
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    model=self.config.model,
                    test_id=test.id,
                    level=test.level,
                    temperature=temp,
                    run_index=run_idx,
                    request={
                        "system_prompt": system_prompt,
                        "user_prompt": prompt,
                        "tools": [tool.to_openai_format(language=self.config.language) for tool in tools],
                        "turn2_context": turn2_context if 'turn2_context' in locals() else None
                    },
                    response={
                        "raw_content": response_final.content,
                        "format_detected": format_detected,
                        "parsed_tool_calls": [c.model_dump() for c in (result.turn2_parsed_calls if result.num_turns >= 2 else result.turn1_parsed_calls)],
                        "parse_errors": parse_errors,
                        "turns": turns_data
                    },
                    validation={
                        "success": result.success,
                        "expected": self._get_failed_turn_expected_multi(test, result),
                        "actual": self._get_failed_turn_actual_multi(result),
                        "errors": errors,
                        "score": 1.0 if result.success else 0.0
                    },
                    usage=total_usage,
                    timing_ms=result.timing_ms
                )
                self.logger.log_entry(entry)
            return result

        if response1.error:
            result.api_error = response1.error
            result.turn1_errors.append(f"API Error: {response1.error}")
            return finish_and_log()
        
        parse_result1 = self.parser.parse(response1.content, response1.raw_response)
        result.turn1_raw_content = response1.content
        result.turn1_parsed_calls = parse_result1.tool_calls.calls
        
        validation1 = self.validator.validate_against_expected(
            parse_result1.tool_calls,
            test.get_expected_turn1(self.config.language)
        )
        result.turn1_success = validation1.success
        result.turn1_errors = [e.message for e in validation1.errors]
        
        expected_turn2 = test.get_expected_turn2(self.config.language)
        if not result.turn1_success or expected_turn2 is None:
            result.turn2_success = expected_turn2 is None
            return finish_and_log()
        
        # ===== TURN 2 =====
        turn2_context = test.turn2_context_ru if self.config.language == "ru" else test.turn2_context_en
        messages = self._build_turn2_messages(
            system_prompt, prompt, response1,
            result.turn1_parsed_calls, test.simulated_results, turn2_context
        )
        
        response2 = self.llm_client.call_with_context(
            messages=messages,
            tools=tools,
            temperature=temp,
            parser=self.parser
        )
        
        result.turn2_timing_ms = response2.timing_ms
        
        if response2.error:
            result.turn2_errors.append(f"API Error: {response2.error}")
            return finish_and_log()
        
        parse_result2 = self.parser.parse(response2.content, response2.raw_response)
        result.turn2_raw_content = response2.content
        result.turn2_parsed_calls = parse_result2.tool_calls.calls
        
        validation2 = self.validator.validate_against_expected(
            parse_result2.tool_calls,
            expected_turn2
        )
        result.turn2_success = validation2.success
        result.turn2_errors = [e.message for e in validation2.errors]
        
        return finish_and_log()
    
    def _run_bfcl_multi_turn(self, test: BFCLMultiTurnTestCase, temp: float, run_idx: int) -> UnifiedRunResult:
        """Run a BFCL 2-turn or 3-turn multi-turn test."""
        result = UnifiedRunResult(
            test_id=test.id,
            temperature=temp,
            run_index=run_idx,
            is_multi_turn=True
        )
        
        tools = get_bfcl_tools_by_names(test.available_tools)
        system_prompt = get_system_prompt(
            self.config.response_format if self.config.response_format != "auto" else "openai",
            self.config.language,
            sequential=True  # Enable sequential instruction for multi-turn tests
        )
        
        # Get prompts in configured language
        t1_prompt = test.turn1_prompt_ru if self.config.language == "ru" else test.turn1_prompt_en
        t2_prompt = test.turn2_prompt_ru if self.config.language == "ru" else test.turn2_prompt_en
        
        # ===== TURN 1 =====
        response1 = self.llm_client.call_with_tools(
            user_prompt=t1_prompt,
            tools=tools,
            system_prompt=system_prompt,
            temperature=temp,
            parser=self.parser
        )
        
        result.turn1_timing_ms = response1.timing_ms
        
        # Helper to finish and log
        def finish_and_log_bfcl():
            if self.logger:
                # Determine final response
                if result.num_turns >= 3 and 'response3' in locals():
                    response_final = response3
                    final_calls = result.turn3_parsed_calls
                elif result.num_turns >= 2 and 'response2' in locals():
                    response_final = response2
                    final_calls = result.turn2_parsed_calls
                else:
                    response_final = response1
                    final_calls = result.turn1_parsed_calls
                
                # Collect turns
                turns_data = []
                if result.turn1_raw_content or result.turn1_parsed_calls:
                    turns_data.append({"raw_content": result.turn1_raw_content, "parsed_tool_calls": [c.model_dump() for c in result.turn1_parsed_calls]})
                if result.turn2_raw_content or result.turn2_parsed_calls:
                    turns_data.append({"raw_content": result.turn2_raw_content, "parsed_tool_calls": [c.model_dump() for c in result.turn2_parsed_calls]})
                if result.turn3_raw_content or result.turn3_parsed_calls:
                    turns_data.append({"raw_content": result.turn3_raw_content, "parsed_tool_calls": [c.model_dump() for c in result.turn3_parsed_calls]})

                # Determine format
                format_detected = "unknown"
                if 'parse_result3' in locals(): format_detected = parse_result3.format_name
                elif 'parse_result2' in locals(): format_detected = parse_result2.format_name
                elif 'parse_result1' in locals(): format_detected = parse_result1.format_name

                # Aggregate errors
                all_errors = result.turn1_errors + result.turn2_errors + result.turn3_errors

                # Aggregate token usage
                total_usage = {
                    "prompt_tokens": 0, "completion_tokens": 0, "reasoning_tokens": 0, "total_tokens": 0
                }
                for resp in ['response1', 'response2', 'response3']:
                    if resp in locals():
                        r = locals()[resp]
                        for key in total_usage:
                            total_usage[key] += r.usage.get(key, 0)

                entry = LogEntry(
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    model=self.config.model,
                    test_id=test.id,
                    level=test.level,
                    temperature=temp,
                    run_index=run_idx,
                    request={
                        "system_prompt": system_prompt,
                        "user_prompt": t1_prompt,
                        "tools": [tool.to_openai_format(language=self.config.language) for tool in tools]
                    },
                    response={
                        "raw_content": response_final.content,
                        "format_detected": format_detected,
                        "parsed_tool_calls": [c.model_dump() for c in final_calls],
                        "parse_errors": all_errors, 
                        "turns": turns_data
                    },
                    validation={
                        "success": result.success,
                        "expected": self._get_failed_turn_expected_bfcl(test, result),
                        "actual": self._get_failed_turn_actual_bfcl(result),
                        "errors": all_errors,
                        "score": 1.0 if result.success else 0.0
                    },
                    usage=total_usage,
                    timing_ms=result.timing_ms
                )
                self.logger.log_entry(entry)
            return result

        if response1.error:
            result.api_error = response1.error
            result.turn1_errors.append(f"API Error: {response1.error}")
            return finish_and_log_bfcl()
        
        parse_result1 = self.parser.parse(response1.content, response1.raw_response)
        result.turn1_raw_content = response1.content
        result.turn1_parsed_calls = parse_result1.tool_calls.calls
        
        validation1 = self.validator.validate_against_expected(
            parse_result1.tool_calls,
            test.get_expected_turn1(self.config.language)
        )
        result.turn1_success = validation1.success
        result.turn1_errors = [e.message for e in validation1.errors]
        
        if not result.turn1_success:
            return finish_and_log_bfcl()
        
        # ===== TURN 2 =====
        messages2 = self._build_3turn_messages(
            system_prompt, t1_prompt, response1, 
            result.turn1_parsed_calls, test.simulated_result1, t2_prompt
        )
        
        response2 = self.llm_client.call_with_context(
            messages=messages2,
            tools=tools,
            temperature=temp,
            parser=self.parser
        )
        
        result.turn2_timing_ms = response2.timing_ms
        
        if response2.error:
            result.turn2_errors.append(f"API Error: {response2.error}")
            return finish_and_log_bfcl()
        
        parse_result2 = self.parser.parse(response2.content, response2.raw_response)
        result.turn2_raw_content = response2.content
        result.turn2_parsed_calls = parse_result2.tool_calls.calls
        
        validation2 = self.validator.validate_against_expected(
            parse_result2.tool_calls,
            test.get_expected_turn2(self.config.language)
        )
        result.turn2_success = validation2.success
        result.turn2_errors = [e.message for e in validation2.errors]
        
        if not result.turn2_success:
            return finish_and_log_bfcl()
        
        # ===== TURN 3 (only for 3-turn tests) =====
        # Prepare for logging
        final_response = response2
        final_parse_result = parse_result2
        
        # ===== TURN 3 (only for 3-turn tests) =====
        expected_turn3 = test.get_expected_turn3(self.config.language)
        if test.num_turns >= 3 and expected_turn3:
            result.num_turns = 3  # Mark as 3-turn test
            
            t3_prompt = test.turn3_prompt_ru if self.config.language == "ru" else test.turn3_prompt_en
            messages3 = self._extend_messages_for_turn3(
                messages2, response2, result.turn2_parsed_calls, test.simulated_result2, t3_prompt
            )
            
            response3 = self.llm_client.call_with_context(
                messages=messages3,
                tools=tools,
                temperature=temp,
                parser=self.parser
            )
            
            result.turn3_timing_ms = response3.timing_ms
            
            parse_result3 = self.parser.parse(response3.content, response3.raw_response)
            result.turn3_raw_content = response3.content
            result.turn3_parsed_calls = parse_result3.tool_calls.calls
            
            validation3 = self.validator.validate_against_expected(
                parse_result3.tool_calls,
                expected_turn3
            )
            
            result.turn3_success = validation3.success
            result.turn3_errors = [e.message for e in validation3.errors]
            
            final_response = response3
            final_parse_result = parse_result3
        
        return finish_and_log_bfcl()
    
    def _build_3turn_messages(
        self,
        system_prompt: str,
        user_prompt: str,
        turn1_response: LLMResponse,
        parsed_calls: list[ToolCall],
        simulated_result: str,
        turn2_prompt: str
    ) -> list[dict]:
        """Build message history for turn 2 of 3-turn test."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        assistant_msg = {"role": "assistant", "content": turn1_response.content or None}
        if turn1_response.tool_calls_raw:
            assistant_msg["tool_calls"] = turn1_response.tool_calls_raw
        messages.append(assistant_msg)
        
        # Add tool results
        for i, call in enumerate(parsed_calls):
            tool_call_id = f"call_{i}"
            if turn1_response.tool_calls_raw and i < len(turn1_response.tool_calls_raw):
                tool_call_id = turn1_response.tool_calls_raw[i].get("id", tool_call_id)
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": simulated_result
            })
        
        messages.append({"role": "user", "content": turn2_prompt})
        return messages
    
    def _extend_messages_for_turn3(
        self,
        messages2: list[dict],
        turn2_response: LLMResponse,
        parsed_calls: list[ToolCall],
        simulated_result: str,
        turn3_prompt: str
    ) -> list[dict]:
        """Extend messages for turn 3."""
        messages = messages2.copy()
        
        assistant_msg = {"role": "assistant", "content": turn2_response.content or None}
        if turn2_response.tool_calls_raw:
            assistant_msg["tool_calls"] = turn2_response.tool_calls_raw
        messages.append(assistant_msg)
        
        for i, call in enumerate(parsed_calls):
            tool_call_id = f"call_t2_{i}"
            if turn2_response.tool_calls_raw and i < len(turn2_response.tool_calls_raw):
                tool_call_id = turn2_response.tool_calls_raw[i].get("id", tool_call_id)
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": simulated_result
            })
        
        messages.append({"role": "user", "content": turn3_prompt})
        return messages
    
    def _build_turn2_messages(
        self,
        system_prompt: str,
        user_prompt: str,
        turn1_response: LLMResponse,
        parsed_calls: list[ToolCall],
        simulated_results: dict[str, str],
        turn2_context: str
    ) -> list[dict]:
        """Build message history for turn 2."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        assistant_msg = {"role": "assistant", "content": turn1_response.content or None}
        if turn1_response.tool_calls_raw:
            assistant_msg["tool_calls"] = turn1_response.tool_calls_raw
        messages.append(assistant_msg)
        
        for i, call in enumerate(parsed_calls):
            tool_call_id = f"call_{i}"
            if turn1_response.tool_calls_raw and i < len(turn1_response.tool_calls_raw):
                tool_call_id = turn1_response.tool_calls_raw[i].get("id", tool_call_id)
            
            result_content = simulated_results.get(call.name, "")
            if not result_content:
                for key, value in simulated_results.items():
                    if key.startswith(call.name):
                        result_content = value
                        break
            if not result_content:
                result_content = f'{{"status": "success"}}'
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": result_content
            })
        
        messages.append({"role": "user", "content": turn2_context})
        return messages
    
    def _print_summary(self, report: UnifiedBenchmarkReport):
        """Print summary."""
        self.console.print("\n[bold]Results by Level:[/bold]")
        
        for level in sorted(set(r.level for r in report.test_results)):
            rate = report.get_level_success_rate(level) * 100
            mode = "multi-turn" if level in MULTI_TURN_LEVELS else "single"
            status = "[green]✓[/green]" if rate >= 50 else "[red]✗[/red]"
            self.console.print(f"  {status} L{level} ({mode}): {rate:.1f}%")
        
        self.console.print(f"\n[bold]Overall: {report.overall_success_rate*100:.1f}%[/bold]")
    
    def test_connection(self) -> bool:
        success, message = self.llm_client.test_connection()
        if success:
            self.console.print(f"[green]✓[/green] {message}")
        else:
            self.console.print(f"[red]✗[/red] {message}")
        return success
