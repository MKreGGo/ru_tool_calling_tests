"""
Benchmark runner.

Main engine for running tool calling benchmarks with temperature cycling.
Supports multiple test suites and bilingual prompts.
"""

from dataclasses import dataclass, field
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from core.config import BenchmarkConfig
from core.llm_client import LLMClient, LLMResponse
from parsers import get_parser, BaseResponseParser
from tools import ToolValidator, get_tools_by_names, get_bfcl_tools_by_names
from tools.schemas import ToolSchema, ToolCall
from tools.validator import ValidationResult, ExpectedCalls
from tests.generator import TestCaseGenerator
from tests.test_cases import TestCase


@dataclass
class SingleRunResult:
    """Result of a single test run."""
    
    test_id: str
    temperature: float
    run_index: int
    
    # Response
    raw_content: str = ""
    format_detected: str = ""
    parsed_calls: list[ToolCall] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)
    
    # Validation
    success: bool = False
    validation_errors: list[str] = field(default_factory=list)
    validation_score: float = 0.0
    
    # Timing & errors
    timing_ms: int = 0
    api_error: str | None = None


@dataclass
class TestResult:
    """Aggregated result for a single test case across all runs."""
    
    test_id: str
    level: int
    source: str = "custom"  # "custom" or "bfcl"
    
    # Results by temperature
    results_by_temp: dict[float, list[SingleRunResult]] = field(default_factory=dict)
    
    @property
    def all_runs(self) -> list[SingleRunResult]:
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
    
    def get_temp_success_rate(self, temp: float) -> float:
        runs = self.results_by_temp.get(temp, [])
        if not runs:
            return 0.0
        return sum(1 for r in runs if r.success) / len(runs)


@dataclass
class BenchmarkReport:
    """Complete benchmark report."""
    
    model: str
    config: BenchmarkConfig
    test_results: list[TestResult] = field(default_factory=list)
    
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
    
    def get_source_success_rate(self, source: str) -> float:
        """Get success rate for tests from a specific source (custom or bfcl)."""
        source_results = [r for r in self.test_results if r.source == source]
        if not source_results:
            return 0.0
        total_success = sum(r.successful_runs for r in source_results)
        total_runs = sum(r.total_runs for r in source_results)
        if total_runs == 0:
            return 0.0
        return total_success / total_runs


class BenchmarkRunner:
    """Main benchmark runner with suite and language support."""
    
    def __init__(
        self,
        config: BenchmarkConfig,
        logger: 'BenchmarkLogger'
    ):
        """
        Initialize benchmark runner.
        
        Args:
            config: Benchmark configuration
            logger: Logger for recording runs
        """
        self.config = config
        self.logger = logger
        self.console = Console()
        
        # Initialize components
        self.llm_client = LLMClient(config)
        self.parser = get_parser(config.response_format)
        self.validator = ToolValidator()
        
        # Initialize test generator with suite and language
        self.test_generator = TestCaseGenerator(
            suite=config.test_suite,
            language=config.language
        )
    
    def run_full_benchmark(self) -> BenchmarkReport:
        """
        Run the complete benchmark suite.
        
        Runs all tests for all configured temperatures and runs per test.
        
        Returns:
            Complete benchmark report
        """
        # Log metadata
        self.logger.log_metadata({
            "model": self.config.model,
            "api_url": self.config.api_url,
            "temperatures": self.config.temperatures,
            "runs_per_test": self.config.runs_per_test,
            "levels": self.config.levels,
            "test_suite": self.config.test_suite,
            "language": self.config.language,
            "response_format": self.config.response_format
        })
        
        # Get tests to run
        tests = self.test_generator.get_tests_by_levels(self.config.levels)
        suite_info = self.test_generator.get_suite_info()
        
        # Calculate total runs
        total_runs = len(tests) * len(self.config.temperatures) * self.config.runs_per_test
        
        self.console.print(f"\n[bold cyan]Starting Benchmark[/bold cyan]")
        self.console.print(f"Model: [yellow]{self.config.model}[/yellow]")
        self.console.print(f"Suite: {self.config.test_suite} ({suite_info['total']} tests) | Language: {self.config.language}")
        self.console.print(f"Tests: {len(tests)} | Temperatures: {self.config.temperatures} | Runs per test: {self.config.runs_per_test}")
        self.console.print(f"Total API calls: [bold]{total_runs}[/bold]\n")
        
        report = BenchmarkReport(model=self.config.model, config=self.config)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task("Running benchmark...", total=total_runs)
            
            for test in tests:
                test_result = TestResult(
                    test_id=test.id, 
                    level=test.level,
                    source=test.source
                )
                
                for temp in self.config.temperatures:
                    temp_runs = []
                    
                    for run_idx in range(self.config.runs_per_test):
                        progress.update(
                            task,
                            description=f"[cyan]{test.id}[/cyan] T={temp} Run {run_idx+1}/{self.config.runs_per_test}"
                        )
                        
                        run_result = self._run_single_test(test, temp, run_idx)
                        temp_runs.append(run_result)
                        
                        # Log the run
                        self._log_run(test, temp, run_idx, run_result)
                        
                        progress.advance(task)
                    
                    test_result.results_by_temp[temp] = temp_runs
                
                report.test_results.append(test_result)
        
        self.console.print("\n[bold green]✓ Benchmark complete![/bold green]")
        self.console.print(f"Results saved to: [cyan]{self.logger.output_path}[/cyan]\n")
        
        return report
    
    def _get_prompt(self, test: TestCase) -> str:
        """Get prompt for test in configured language."""
        return self.test_generator.get_prompt(test)
    
    def _get_tools_for_test(self, test: TestCase) -> list:
        """Get tool schemas for a test, considering its source."""
        if test.source == "bfcl":
            return get_bfcl_tools_by_names(test.available_tools)
        return get_tools_by_names(test.available_tools)
    
    def _run_single_test(
        self,
        test: TestCase,
        temperature: float,
        run_index: int
    ) -> SingleRunResult:
        """
        Run a single test case once.
        
        Args:
            test: Test case to run
            temperature: Sampling temperature
            run_index: Run number (0-indexed)
            
        Returns:
            Result of this run
        """
        result = SingleRunResult(
            test_id=test.id,
            temperature=temperature,
            run_index=run_index
        )
        
        # Get tools for this test (handles both custom and bfcl)
        tools = self._get_tools_for_test(test)
        
        # Generate system prompt
        system_prompt = self.parser.get_system_prompt(tools)
        
        # Get prompt in configured language
        prompt = self._get_prompt(test)
        
        # Make LLM call
        response = self.llm_client.call_with_tools(
            user_prompt=prompt,
            tools=tools,
            system_prompt=system_prompt,
            temperature=temperature,
            parser=self.parser
        )
        
        result.timing_ms = response.timing_ms
        
        # Check for API error
        if response.error:
            result.api_error = response.error
            result.parse_errors.append(f"API Error: {response.error}")
            return result
        
        # Parse response
        parse_result = self.parser.parse(response.content, response.raw_response)
        
        result.raw_content = response.content
        result.format_detected = parse_result.format_name
        result.parsed_calls = parse_result.tool_calls.calls
        result.parse_errors = parse_result.errors + parse_result.tool_calls.parse_errors
        
        # Validate against expected
        validation = self.validator.validate_against_expected(
            parse_result.tool_calls,
            test.expected
        )
        
        result.success = validation.success
        result.validation_score = validation.score
        result.validation_errors = [e.message for e in validation.errors]
        
        return result
    
    def _log_run(
        self,
        test: TestCase,
        temperature: float,
        run_index: int,
        result: SingleRunResult
    ):
        """Log a single test run."""
        # Get tools for logging
        tools = self._get_tools_for_test(test)
        tools_dicts = self.parser.format_tools_for_api(tools)
        system_prompt = self.parser.get_system_prompt(tools)
        
        # Get prompt in configured language
        prompt = self._get_prompt(test)
        
        # Convert expected calls to dicts
        expected_dicts = []
        for ec in test.expected.calls:
            expected_dicts.append({
                "name": ec.name,
                "args": ec.args
            })
        
        # Convert actual calls to dicts
        actual_dicts = []
        for call in result.parsed_calls:
            actual_dicts.append({
                "name": call.name,
                "arguments": call.arguments
            })
        
        self.logger.log_run(
            model=self.config.model,
            test_id=test.id,
            level=test.level,
            temperature=temperature,
            run_index=run_index,
            system_prompt=system_prompt,
            user_prompt=prompt,
            tools=tools_dicts,
            raw_content=result.raw_content,
            format_detected=result.format_detected,
            parsed_tool_calls=actual_dicts,
            parse_errors=result.parse_errors,
            validation_success=result.success,
            expected_calls=expected_dicts,
            actual_calls=actual_dicts,
            validation_errors=result.validation_errors,
            validation_score=result.validation_score,
            timing_ms=result.timing_ms,
            source=test.source,  # Include source in log
            language=self.config.language  # Include language in log
        )
    
    def test_connection(self) -> bool:
        """Test LLM connection before running benchmark."""
        success, message = self.llm_client.test_connection()
        if success:
            self.console.print(f"[green]✓[/green] {message}")
        else:
            self.console.print(f"[red]✗[/red] {message}")
        return success
