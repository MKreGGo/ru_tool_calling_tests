"""
LLM Tool Calling Benchmark Application

CLI entry point for running benchmarks on local LLMs.

Usage:
    python main.py --model "model-name" [options]
    
Examples:
    # Quick test with defaults
    python main.py --model "qwen2.5-7b-instruct"
    
    # Full benchmark with all 50 tests
    python main.py --model "llama3.2" --suite all --levels 1,2,3,4,5 --runs 3
    
    # Only BFCL tests in Russian
    python main.py --model "mistral-7b" --suite bfcl --lang ru --runs 1
    
    # Only custom tests in English
    python main.py --model "qwen2.5" --suite custom --lang en --levels 1,2
"""

import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console

from core.config import BenchmarkConfig
from benchmark.unified_runner import UnifiedRunner
from benchmark_logging.logger import BenchmarkLogger
from benchmark_logging.reporter import BenchmarkReporter


console = Console()


def parse_list(ctx, param, value: str) -> list:
    """Parse comma-separated values into a list."""
    if not value:
        return []
    return [item.strip() for item in value.split(",")]


def parse_int_list(ctx, param, value: str) -> list[int]:
    """Parse comma-separated integers."""
    if not value:
        return []
    return [int(item.strip()) for item in value.split(",")]


def parse_float_list(ctx, param, value: str) -> list[float]:
    """Parse comma-separated floats."""
    if not value:
        return []
    return [float(item.strip()) for item in value.split(",")]


@click.command()
@click.option(
    "--model", "-m",
    required=True,
    help="Name of the model to test (as it appears in LM Studio)"
)
@click.option(
    "--api-url", "-u",
    default="http://172.26.16.1:8000/v1",
    help="LM Studio API URL (default: http://172.26.16.1:8000/v1)"
)
@click.option(
    "--format", "-f",
    "response_format",
    default="auto",
    type=click.Choice(["auto", "openai", "anthropic", "mistral", "hermes", "raw_json"]),
    help="Response format to expect (default: auto-detect)"
)
@click.option(
    "--suite", "-s",
    default="all",
    type=click.Choice(["custom", "bfcl", "all"]),
    help="Test suite to run: custom (25 original), bfcl (25 official BFCL-V4), all (50 tests)"
)
@click.option(
    "--lang", "-L",
    default="en",
    type=click.Choice(["en", "ru"]),
    help="Language for test prompts (default: en)"
)
@click.option(
    "--levels", "-l",
    default="1,2,3,4,5",
    callback=parse_int_list,
    help="Comma-separated difficulty levels to test (default: 1,2,3,4,5)"
)
@click.option(
    "--runs", "-r",
    default=3,
    type=int,
    help="Number of runs per test per temperature (default: 3)"
)
@click.option(
    "--temperatures", "-t",
    default="0.2,0.5,0.8",
    callback=parse_float_list,
    help="Comma-separated temperatures for testing cycles (default: 0.2,0.5,0.8)"
)
@click.option(
    "--output", "-o",
    default="",
    help="Output JSONL log file path (default: auto-generated in ./logs/)"
)
@click.option(
    "--skip-connection-test",
    is_flag=True,
    help="Skip the initial connection test"
)
@click.option(
    "--show-report/--no-report",
    default=True,
    help="Show summary report after benchmark (default: show)"
)
@click.option(
    "--max-tokens",
    default=32000,
    type=int,
    help="Maximum tokens in response (default: 32000)"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose output"
)
def main(
    model: str,
    api_url: str,
    response_format: str,
    suite: str,
    lang: str,
    levels: list[int],
    runs: int,
    temperatures: list[float],
    output: str,
    skip_connection_test: bool,
    show_report: bool,
    max_tokens: int,
    verbose: bool
):
    """
    LLM Tool Calling Benchmark
    
    Test local LLMs on their ability to correctly use tools/functions.
    Supports multiple difficulty levels, temperature cycles, response formats,
    test suites (custom/bfcl/all), and bilingual prompts (en/ru).
    """
    # Generate output path if not provided
    if not output:
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_safe = model.replace("/", "_").replace(":", "_")
        # Include suite and lang in filename for clarity
        output = str(logs_dir / f"benchmark_{model_safe}_{suite}_{lang}_{timestamp}.jsonl")
    
    # Create configuration
    config = BenchmarkConfig(
        api_url=api_url,
        model=model,
        runs_per_test=runs,
        temperatures=temperatures,
        levels=levels,
        test_suite=suite,
        language=lang,
        response_format=response_format,
        max_tokens=max_tokens,
        output_path=output,
        verbose=verbose
    )
    
    # Print banner
    console.print("\n[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║         LLM Tool Calling Benchmark                           ║[/bold cyan]")
    console.print("[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]\n")
    
    # Print configuration summary
    suite_names = {"custom": "Custom (25 tests)", "bfcl": "BFCL-V4 (25 tests)", "all": "All (50 tests)"}
    lang_names = {"en": "English", "ru": "Russian"}
    multi_turn_levels = [l for l in levels if l in {3, 5}]
    single_turn_levels = [l for l in levels if l not in {3, 5}]
    console.print(f"[dim]Suite: {suite_names[suite]} | Language: {lang_names[lang]}[/dim]")
    console.print(f"[dim]Single-turn levels: {single_turn_levels or 'none'} | Multi-turn levels: {multi_turn_levels or 'none'}[/dim]\n")
    
    # Initialize logger
    logger = BenchmarkLogger(output)
    
    try:
        # Create unified runner (auto single/multi-turn)
        runner = UnifiedRunner(config, logger)
        
        # Test connection
        if not skip_connection_test:
            console.print("[dim]Testing connection to LM Studio...[/dim]")
            if not runner.test_connection():
                console.print("\n[red]Failed to connect to LM Studio. Please ensure:[/red]")
                console.print("  1. LM Studio is running")
                console.print("  2. A model is loaded")
                console.print(f"  3. API server is enabled at {api_url}")
                console.print("\nUse --skip-connection-test to bypass this check.\n")
                sys.exit(1)
            console.print()
        
        # Run benchmark
        report = runner.run_full_benchmark()
        
        # Show report
        if show_report:
            reporter = BenchmarkReporter()
            stats = reporter.load_from_jsonl(output)
            reporter.print_report(stats)
            
            # Save summary
            summary = reporter.generate_summary(stats)
            summary_path = Path(output).with_suffix(".summary.md")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(summary)
            console.print(f"[dim]Summary saved to: {summary_path}[/dim]\n")
    
    finally:
        logger.close()


@click.command()
@click.argument("log_file", type=click.Path(exists=True))
def report(log_file: str):
    """
    Generate a report from an existing benchmark log file.
    
    Usage:
        python main.py report logs/benchmark_xxx.jsonl
    """
    reporter = BenchmarkReporter()
    stats = reporter.load_from_jsonl(log_file)
    reporter.print_report(stats)


# Create CLI group if we want multiple commands
@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """LLM Tool Calling Benchmark CLI"""
    if ctx.invoked_subcommand is None:
        # Default to main command
        ctx.invoke(main)


if __name__ == "__main__":
    # Simple single-command interface
    main()
