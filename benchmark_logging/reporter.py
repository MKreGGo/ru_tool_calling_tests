"""
Benchmark reporter.

Generates console and summary reports from benchmark results.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


@dataclass
class LevelStats:
    """Statistics for a single level."""
    
    level: int
    total_runs: int = 0
    successful_runs: int = 0
    
    # Token usage for this level
    total_tokens: int = 0
    
    # By temperature
    stats_by_temp: dict[float, dict] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs
    
    def get_temp_success_rate(self, temp: float) -> float:
        stats = self.stats_by_temp.get(temp, {})
        total = stats.get("total", 0)
        success = stats.get("success", 0)
        if total == 0:
            return 0.0
        return success / total


@dataclass
class SourceStats:
    """Statistics for a test source (custom or bfcl)."""
    
    source: str
    total_runs: int = 0
    successful_runs: int = 0
    levels: dict[int, LevelStats] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs


@dataclass
class DifficultyStats:
    """Statistics by difficulty category."""
    
    difficulty: str  # "simple", "medium", "hard"
    total_runs: int = 0
    successful_runs: int = 0
    
    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs


@dataclass
class BenchmarkStats:
    """Overall benchmark statistics."""
    
    model: str
    total_tests: int = 0
    total_runs: int = 0  # tests × temps × runs_per_test
    successful_runs: int = 0
    
    levels: dict[int, LevelStats] = field(default_factory=dict)
    temperatures: list[float] = field(default_factory=list)
    
    # Timing
    total_time_ms: int = 0
    avg_time_ms: float = 0.0
    
    # Token usage
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_reasoning_tokens: int = 0
    total_all_tokens: int = 0
    
    # Stats by source (custom vs bfcl)
    stats_by_source: dict[str, SourceStats] = field(default_factory=dict)
    
    # Stats by difficulty
    stats_by_difficulty: dict[str, DifficultyStats] = field(default_factory=dict)
    
    # Errors
    parse_errors: int = 0
    validation_errors: int = 0
    api_errors: int = 0
    
    @property
    def overall_success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs


class BenchmarkReporter:
    """Generates reports from benchmark results."""
    
    def __init__(self):
        self.console = Console()
    
    def _get_difficulty(self, level: int) -> str:
        """Map level to difficulty category."""
        if level == 1:
            return "simple"
        elif level in [2, 3]:
            return "medium"
        else:  # 4, 5
            return "hard"
    
    def _get_source_from_test_id(self, test_id: str) -> str:
        """Determine source from test_id pattern."""
        if test_id.startswith("BFCL"):
            return "bfcl"
        return "custom"
    
    def load_from_jsonl(self, log_path: str | Path) -> BenchmarkStats:
        """
        Load and aggregate statistics from JSONL log file.
        
        Args:
            log_path: Path to the log file
            
        Returns:
            Aggregated benchmark statistics
        """
        log_path = Path(log_path)
        
        if not log_path.exists():
            raise FileNotFoundError(f"Log file not found: {log_path}")
        
        stats = BenchmarkStats(model="unknown")
        temperatures = set()
        test_ids = set()
        
        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                # Skip metadata entries
                if entry.get("_type") == "metadata":
                    config = entry.get("config", {})
                    stats.model = config.get("model", entry.get("model", "unknown"))
                    continue
                
                # Aggregate stats
                test_id = entry.get("test_id", "")
                level = entry.get("level", 0)
                temp = entry.get("temperature", 0.0)
                validation = entry.get("validation", {})
                success = validation.get("success", False)
                timing = entry.get("timing_ms", 0)
                usage = entry.get("usage", {})
                
                # Determine source and difficulty
                source = self._get_source_from_test_id(test_id)
                difficulty = self._get_difficulty(level)
                
                test_ids.add(test_id)
                temperatures.add(temp)
                stats.total_runs += 1
                stats.total_time_ms += timing
                
                # Aggregate token usage
                stats.total_prompt_tokens += usage.get("prompt_tokens", 0)
                stats.total_completion_tokens += usage.get("completion_tokens", 0)
                stats.total_reasoning_tokens += usage.get("reasoning_tokens", 0)
                stats.total_all_tokens += usage.get("total_tokens", 0)
                
                if success:
                    stats.successful_runs += 1
                
                # Level stats
                if level not in stats.levels:
                    stats.levels[level] = LevelStats(level=level)
                
                level_stats = stats.levels[level]
                level_stats.total_runs += 1
                level_stats.total_tokens += usage.get("total_tokens", 0)
                if success:
                    level_stats.successful_runs += 1
                
                # Temperature-specific stats within level
                if temp not in level_stats.stats_by_temp:
                    level_stats.stats_by_temp[temp] = {"total": 0, "success": 0}
                level_stats.stats_by_temp[temp]["total"] += 1
                if success:
                    level_stats.stats_by_temp[temp]["success"] += 1
                
                # Source stats (custom vs bfcl)
                if source not in stats.stats_by_source:
                    stats.stats_by_source[source] = SourceStats(source=source)
                
                source_stats = stats.stats_by_source[source]
                source_stats.total_runs += 1
                if success:
                    source_stats.successful_runs += 1
                
                # Level stats within source
                if level not in source_stats.levels:
                    source_stats.levels[level] = LevelStats(level=level)
                
                source_level_stats = source_stats.levels[level]
                source_level_stats.total_runs += 1
                source_level_stats.total_tokens += usage.get("total_tokens", 0)
                if success:
                    source_level_stats.successful_runs += 1
                
                # Temperature stats within source level
                if temp not in source_level_stats.stats_by_temp:
                    source_level_stats.stats_by_temp[temp] = {"total": 0, "success": 0}
                source_level_stats.stats_by_temp[temp]["total"] += 1
                if success:
                    source_level_stats.stats_by_temp[temp]["success"] += 1
                
                # Difficulty stats
                if difficulty not in stats.stats_by_difficulty:
                    stats.stats_by_difficulty[difficulty] = DifficultyStats(difficulty=difficulty)
                
                diff_stats = stats.stats_by_difficulty[difficulty]
                diff_stats.total_runs += 1
                if success:
                    diff_stats.successful_runs += 1
                
                # Count errors
                parse_errors = entry.get("response", {}).get("parse_errors", [])
                val_errors = validation.get("errors", [])
                
                if parse_errors:
                    stats.parse_errors += 1
                if val_errors and not success:
                    stats.validation_errors += 1
        
        stats.total_tests = len(test_ids)
        stats.temperatures = sorted(temperatures)
        
        if stats.total_runs > 0:
            stats.avg_time_ms = stats.total_time_ms / stats.total_runs
        
        return stats
    
    def print_report(self, stats: BenchmarkStats):
        """
        Print formatted report to console.
        
        Args:
            stats: Benchmark statistics
        """
        self._print_header(stats)
        self._print_token_summary(stats)
        self._print_source_table(stats, "custom", "Custom Tests Results")
        self._print_source_table(stats, "bfcl", "BFCL Tests Results")
        self._print_difficulty_summary(stats)
        self._print_error_summary(stats)
    
    def _print_header(self, stats: BenchmarkStats):
        """Print report header."""
        header = Panel(
            Text.assemble(
                ("LLM Tool Calling Benchmark Report\n", "bold cyan"),
                (f"Model: {stats.model}\n", "white"),
                (f"Total Tests: {stats.total_tests} | ", "white"),
                (f"Total Runs: {stats.total_runs} | ", "white"),
                (f"Avg Time: {stats.avg_time_ms:.0f}ms", "white")
            ),
            title="📊 Benchmark Results",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
    
    def _print_token_summary(self, stats: BenchmarkStats):
        """Print token usage summary."""
        if stats.total_all_tokens == 0:
            return
        
        content = (
            f"Prompt Tokens:     {stats.total_prompt_tokens:,}\n"
            f"Completion Tokens: {stats.total_completion_tokens:,}\n"
        )
        if stats.total_reasoning_tokens > 0:
            content += f"Reasoning Tokens:  {stats.total_reasoning_tokens:,}\n"
        content += f"Total Tokens:      {stats.total_all_tokens:,}"
        
        panel = Panel(
            content,
            title="🔢 Token Usage",
            border_style="blue"
        )
        self.console.print(panel)
        self.console.print()
    
    def _print_source_table(self, stats: BenchmarkStats, source: str, title: str):
        """Print results table for a specific source."""
        if source not in stats.stats_by_source:
            return
        
        source_stats = stats.stats_by_source[source]
        
        table = Table(title=title)
        
        # Add columns
        table.add_column("Level", style="cyan", justify="center")
        for temp in stats.temperatures:
            table.add_column(f"T={temp}", justify="center")
        table.add_column("Overall", style="bold", justify="center")
        table.add_column("Tokens", style="blue", justify="right")
        
        # Add rows for each level
        sorted_levels = sorted(source_stats.levels.keys())
        for level in sorted_levels:
            level_stats = source_stats.levels[level]
            
            level_name = self._get_level_name(level)
            row = [f"L{level} {level_name}"]
            
            for temp in stats.temperatures:
                rate = level_stats.get_temp_success_rate(temp)
                row.append(self._format_rate(rate))
            
            overall_rate = level_stats.success_rate
            row.append(self._format_rate(overall_rate))
            
            # Token count for this level
            row.append(f"{level_stats.total_tokens:,}")
            
            table.add_row(*row)
        
        # Total row
        total_row = ["[bold]TOTAL[/bold]"]
        for temp in stats.temperatures:
            total_temp = sum(
                ls.stats_by_temp.get(temp, {}).get("total", 0)
                for ls in source_stats.levels.values()
            )
            success_temp = sum(
                ls.stats_by_temp.get(temp, {}).get("success", 0)
                for ls in source_stats.levels.values()
            )
            rate = success_temp / total_temp if total_temp > 0 else 0.0
            total_row.append(self._format_rate(rate))
        
        total_row.append(f"[bold]{self._format_rate(source_stats.success_rate)}[/bold]")
        
        # Total tokens for this source
        total_source_tokens = sum(ls.total_tokens for ls in source_stats.levels.values())
        total_row.append(f"[bold]{total_source_tokens:,}[/bold]")
        
        table.add_row(*total_row)
        
        self.console.print(table)
        self.console.print()

    
    def _print_difficulty_summary(self, stats: BenchmarkStats):
        """Print success rates by difficulty."""
        if not stats.stats_by_difficulty:
            return
        
        table = Table(title="Results by Difficulty")
        table.add_column("Difficulty", style="cyan", justify="left")
        table.add_column("Success Rate", justify="center")
        table.add_column("Runs", justify="center")
        
        # Order: simple, medium, hard
        for diff in ["simple", "medium", "hard"]:
            if diff in stats.stats_by_difficulty:
                ds = stats.stats_by_difficulty[diff]
                table.add_row(
                    diff.capitalize(),
                    self._format_rate(ds.success_rate),
                    str(ds.total_runs)
                )
        
        self.console.print(table)
        self.console.print()
    
    def _print_error_summary(self, stats: BenchmarkStats):
        """Print error summary."""
        if stats.parse_errors > 0 or stats.validation_errors > 0:
            self.console.print(Panel(
                f"Parse Errors: {stats.parse_errors} | Validation Errors: {stats.validation_errors}",
                title="⚠️ Errors",
                border_style="yellow"
            ))
    
    def _get_level_name(self, level: int) -> str:
        """Get short name for level."""
        names = {
            1: "Simple",
            2: "Select",
            3: "Seq",
            4: "Par",
            5: "Chain"
        }
        return names.get(level, "")
    
    def _format_rate(self, rate: float) -> str:
        """Format success rate with color coding."""
        pct = rate * 100
        if pct >= 90:
            return f"[green]{pct:.0f}%[/green]"
        elif pct >= 70:
            return f"[yellow]{pct:.0f}%[/yellow]"
        elif pct >= 50:
            return f"[orange1]{pct:.0f}%[/orange1]"
        else:
            return f"[red]{pct:.0f}%[/red]"
    
    def generate_summary(self, stats: BenchmarkStats) -> str:
        """
        Generate text summary of results.
        
        Args:
            stats: Benchmark statistics
            
        Returns:
            Summary string
        """
        lines = [
            f"# Benchmark Summary: {stats.model}",
            "",
        ]
        
        # Token usage
        if stats.total_all_tokens > 0:
            lines.extend([
                "## Token Usage",
                f"- Prompt tokens: {stats.total_prompt_tokens:,}",
                f"- Completion tokens: {stats.total_completion_tokens:,}",
            ])
            if stats.total_reasoning_tokens > 0:
                lines.append(f"- Reasoning tokens: {stats.total_reasoning_tokens:,}")
            lines.extend([
                f"- Total tokens: {stats.total_all_tokens:,}",
                "",
            ])
        
        # Overall stats
        lines.extend([
            "## Overall Results",
            f"- Total tests: {stats.total_tests}",
            f"- Total runs: {stats.total_runs}",
            f"- Overall success rate: {stats.overall_success_rate*100:.1f}%",
            f"- Average response time: {stats.avg_time_ms:.0f}ms",
            "",
        ])
        
        # Results by source
        for source in ["custom", "bfcl"]:
            if source in stats.stats_by_source:
                ss = stats.stats_by_source[source]
                lines.append(f"## {source.upper()} Tests Results:")
                for level in sorted(ss.levels.keys()):
                    level_stats = ss.levels[level]
                    level_name = self._get_level_name(level)
                    lines.append(f"- Level {level} ({level_name}): {level_stats.success_rate*100:.1f}%")
                lines.append("")
        
        # Results by difficulty
        lines.append("## Results by Difficulty:")
        for diff in ["simple", "medium", "hard"]:
            if diff in stats.stats_by_difficulty:
                ds = stats.stats_by_difficulty[diff]
                lines.append(f"- {diff.capitalize()}: {ds.success_rate*100:.1f}%")
        lines.append("")
        
        # Results by temperature
        lines.append("## Results by Temperature:")
        for temp in stats.temperatures:
            total_temp = sum(
                ls.stats_by_temp.get(temp, {}).get("total", 0)
                for ls in stats.levels.values()
            )
            success_temp = sum(
                ls.stats_by_temp.get(temp, {}).get("success", 0)
                for ls in stats.levels.values()
            )
            rate = success_temp / total_temp if total_temp > 0 else 0.0
            lines.append(f"- T={temp}: {rate*100:.1f}%")
        
        return "\n".join(lines)
