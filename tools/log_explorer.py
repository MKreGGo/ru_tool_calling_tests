import json
import os
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import Any, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax
from rich.live import Live

# Ensure we're in the right directory context
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
LOGS_DIR = PROJECT_ROOT / "logs"

import sys

# Force UTF-8 encoding for stdout/stderr to avoid crashes in Windows terminals
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

console = Console(force_terminal=True)

class LogExplorer:
    def __init__(self):
        pass

    def _load_metadata(self, log_path: Path) -> dict:
        """Read the first few lines to find metadata."""
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line)
                    if data.get("_type") == "metadata":
                        return data
                    # If we hit a normal entry, we might have missed metadata
                    if "test_id" in data:
                        return {"model": data.get("model", "unknown")}
        except Exception:
            pass
        return {"model": "unknown"}

    def _get_entries(self, log_path: Path):
        """Generator for log entries skipping metadata."""
        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get("_type") == "metadata":
                        continue
                    yield data
                except json.JSONDecodeError:
                    continue

    def list_logs(self):
        """List available logs with some stats."""
        if not LOGS_DIR.exists():
            console.print(f"[red]Logs directory not found: {LOGS_DIR}[/red]")
            return

        logs = sorted(LOGS_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        
        if not logs:
            console.print(f"[yellow]No logs found in {LOGS_DIR}[/yellow]")
            return

        table = Table(title="Available Benchmark Logs", box=None)
        table.add_column("Filename", style="cyan", no_wrap=True)
        table.add_column("Model", style="green")
        table.add_column("Date", style="blue")
        table.add_column("Size", justify="right")
        
        for log_path in logs:
            meta = self._load_metadata(log_path)
            # Find model in meta or entries
            model = meta.get("config", {}).get("model", meta.get("model", "unknown"))
            mtime = datetime.fromtimestamp(log_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            size_kb = log_path.stat().st_size / 1024
            
            table.add_row(
                log_path.name,
                model,
                mtime,
                f"{size_kb:.1f} KB"
            )
            
        console.print(table)

    def summary(self, log_name: str):
        """Show summary statistics for a log."""
        log_path = LOGS_DIR / log_name
        if not log_path.exists():
            # Try to find by partial match if not exact
            matches = list(LOGS_DIR.glob(f"*{log_name}*"))
            if not matches:
                console.print(f"[red]Error: Log file '{log_name}' not found.[/red]")
                return
            log_path = matches[0]
            console.print(f"[yellow]Analysing closest match: {log_path.name}[/yellow]")

        stats = {
            "total": 0,
            "success": 0,
            "levels": defaultdict(lambda: {"total": 0, "success": 0}),
            "temps": defaultdict(lambda: {"total": 0, "success": 0}),
            "tokens": {"prompt": 0, "completion": 0, "total": 0},
            "errors": Counter()
        }
        
        model = "unknown"
        for entry in self._get_entries(log_path):
            stats["total"] += 1
            model = entry.get("model", model)
            lvl = entry.get("level", 0)
            tmp = entry.get("temperature", 0.0)
            val = entry.get("validation", {})
            success = val.get("success", False)
            usage = entry.get("usage", {})
            
            stats["levels"][lvl]["total"] += 1
            stats["temps"][tmp]["total"] += 1
            if success:
                stats["success"] += 1
                stats["levels"][lvl]["success"] += 1
                stats["temps"][tmp]["success"] += 1
            else:
                for err in val.get("errors", []):
                    # Clean up error message for categorization
                    category = err.split(":")[0] if ":" in err else err
                    stats["errors"][category] += 1
            
            stats["tokens"]["prompt"] += usage.get("prompt_tokens", 0)
            stats["tokens"]["completion"] += usage.get("completion_tokens", 0)
            stats["tokens"]["total"] += usage.get("total_tokens", 0)

        # Print layout
        console.print(Panel(f"Summary for [bold cyan]{model}[/bold cyan]\nFile: {log_path.name}", title="📊 Benchmark Statistics"))
        
        # Overall Table
        overall_table = Table(show_header=False, box=None)
        overall_table.add_row("Total Runs:", f"{stats['total']}")
        overall_table.add_row("Successful:", f"[green]{stats['success']}[/green]")
        rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        overall_table.add_row("Success Rate:", f"[bold]{rate:.1f}%[/bold]")
        
        # Add tokens to overall table
        overall_table.add_row("Total Tokens:", f"{stats['tokens']['total']:,}")
        console.print(overall_table)
        
        # Levels and Temps
        cols = Table.grid(expand=True)
        cols.add_column()
        cols.add_column()
        
        lvl_table = Table(title="Success by Level")
        lvl_table.add_column("Level", justify="center")
        lvl_table.add_column("Rate", justify="right")
        for lvl in sorted(stats["levels"].keys()):
            s = stats["levels"][lvl]
            r = (s["success"] / s["total"] * 100) if s["total"] > 0 else 0
            lvl_table.add_row(f"L{lvl}", f"{r:.1f}%")
            
        tmp_table = Table(title="Success by Temp")
        tmp_table.add_column("Temp", justify="center")
        tmp_table.add_column("Rate", justify="right")
        for tmp in sorted(stats["temps"].keys()):
            s = stats["temps"][tmp]
            r = (s["success"] / s["total"] * 100) if s["total"] > 0 else 0
            tmp_table.add_row(f"{tmp}", f"{r:.1f}%")
            
        cols.add_row(lvl_table, tmp_table)
        console.print(cols)
        
        # Errors
        if stats["errors"]:
            err_table = Table(title="Common Errors")
            err_table.add_column("Error Type", style="yellow")
            err_table.add_column("Count", justify="right")
            for err, count in stats["errors"].most_common(5):
                err_table.add_row(err, str(count))
            console.print(err_table)

    def failures(self, log_name: str, level: Optional[int] = None):
        """List failed tests with details."""
        log_path = LOGS_DIR / log_name
        if not log_path.exists():
            matches = list(LOGS_DIR.glob(f"*{log_name}*"))
            if not matches: return
            log_path = matches[0]

        table = Table(title=f"Failed Tests in {log_path.name}")
        table.add_column("ID", style="cyan")
        table.add_column("Lvl", justify="center")
        table.add_column("T", justify="center")
        table.add_column("Error Sample", style="red")
        
        failed_count = 0
        for entry in self._get_entries(log_path):
            if level and entry.get("level") != level:
                continue
                
            val = entry.get("validation", {})
            if not val.get("success", False):
                failed_count += 1
                errors = val.get("errors", [])
                error_sample = errors[0][:100] + ("..." if len(errors[0]) > 100 else "") if errors else "Validation failed with no error msg"
                table.add_row(
                    entry.get("test_id", "???"),
                    str(entry.get("level", "?")),
                    str(entry.get("temperature", "?")),
                    error_sample
                )
                if failed_count >= 50:
                    table.add_row("...", "...", "...", "Truncated to 50 failures")
                    break
        
        console.print(table)

    def inspect(self, log_name: str, test_id: str, run_index: int = 0):
        """Inspect a specific test run."""
        log_path = LOGS_DIR / log_name
        if not log_path.exists():
            matches = list(LOGS_DIR.glob(f"*{log_name}*"))
            if not matches: return
            log_path = matches[0]

        found = None
        for entry in self._get_entries(log_path):
            if entry.get("test_id") == test_id and entry.get("run_index", 0) == run_index:
                found = entry
                break
        
        if not found:
            console.print(f"[red]No run found for {test_id} with index {run_index}[/red]")
            return
            
        console.print(Panel(f"Inspection: [bold cyan]{test_id}[/bold cyan] (Run {run_index})", title="🔍 Test Detail"))
        
        # User Prompt
        console.print("[bold yellow]Initial Prompt:[/bold yellow]")
        console.print(found["request"]["user_prompt"])
        console.print()
        
        # Turns (If multi-turn)
        turns = found["response"].get("turns", [])
        if turns:
            for i, turn in enumerate(turns):
                console.print(f"[bold magenta]--- Turn {i+1} ---[/bold magenta]")
                console.print(f"[dim]Response:[/dim]")
                console.print(turn.get("raw_content") or "[Empty]")
                
                calls = turn.get("parsed_tool_calls", [])
                if calls:
                    console.print(f"[dim]Parsed Calls:[/dim]")
                    calls_json = json.dumps(calls, indent=2, ensure_ascii=False)
                    console.print(Syntax(calls_json, "json", theme="monokai", background_color="default"))
                console.print()
        else:
            # Single turn fall-back
            console.print(f"[bold yellow]Raw Response:[/bold yellow]")
            console.print(found["response"].get("raw_content") or "[Empty]")
            console.print()
            
            console.print("[bold yellow]Parsed Tool Calls:[/bold yellow]")
            calls_json = json.dumps(found["response"].get("parsed_tool_calls"), indent=2, ensure_ascii=False)
            console.print(Syntax(calls_json, "json", theme="monokai", background_color="default"))
            console.print()
        
        # Validation
        val = found.get("validation", {})
        status = "[green]PASS[/green]" if val.get("success") else "[red]FAIL[/red]"
        console.print(f"[bold yellow]Validation:[/bold yellow] {status} (Score: {val.get('score', 0)})")
        if val.get("errors"):
            for err in val["errors"]:
                console.print(f" [red]• {err}[/red]")
        
        console.print(f"\n[bold yellow]Expected (FAILING TURN):[/bold yellow]")
        exp_json = json.dumps(val.get("expected"), indent=2, ensure_ascii=False)
        console.print(Syntax(exp_json, "json", theme="shadowfox", background_color="default"))

    def search(self, log_name: str, query: str):
        """Search for a string in logs."""
        log_path = LOGS_DIR / log_name
        if not log_path.exists():
            matches = list(LOGS_DIR.glob(f"*{log_name}*"))
            if not matches: return
            log_path = matches[0]

        console.print(f"Searching for '[bold cyan]{query}[/bold cyan]' in {log_path.name}...")
        
        table = Table()
        table.add_column("Test ID", style="cyan")
        table.add_column("Match Source")
        table.add_column("Preview", style="dim")
        
        count = 0
        for entry in self._get_entries(log_path):
            found_in = []
            preview = ""
            
            user_prompt = entry["request"]["user_prompt"]
            if query.lower() in user_prompt.lower():
                found_in.append("Prompt")
                preview = user_prompt
                
            raw_content = entry["response"].get("raw_content", "")
            if query.lower() in raw_content.lower():
                found_in.append("Response")
                if not preview: preview = raw_content
                
            # Search in tool calls
            calls = entry["response"].get("parsed_tool_calls", [])
            for call in calls:
                if query.lower() in call["name"].lower():
                    found_in.append("ToolName")
                    if not preview: preview = f"Tool: {call['name']}"
                for arg_val in call.get("arguments", {}).values():
                    if query.lower() in str(arg_val).lower():
                        found_in.append("ToolArg")
                        if not preview: preview = f"Arg: {arg_val}"
            
            # Search in turns
            turns = entry["response"].get("turns", [])
            for turn in turns:
                if query.lower() in (turn.get("raw_content") or "").lower():
                    found_in.append("TurnContent")
                for call in turn.get("parsed_tool_calls", []):
                    if query.lower() in call["name"].lower():
                        found_in.append("ToolName")
                        if not preview: preview = f"Tool: {call['name']}"
                    for arg_val in call.get("arguments", {}).values():
                        if query.lower() in str(arg_val).lower():
                            found_in.append("ToolArg")
                            if not preview: preview = f"Arg: {arg_val}"
            
            # Search in validation errors
            valid_errors = entry.get("validation", {}).get("errors", [])
            for err in valid_errors:
                if query.lower() in str(err).lower():
                    found_in.append("ValidationError")
                    if not preview: preview = f"Err: {err}"
            
            if found_in:
                count += 1
                table.add_row(
                    entry.get("test_id", "???"),
                    ", ".join(list(set(found_in))),
                    preview[:80].replace("\n", " ") + "..."
                )
                if count >= 30:
                    table.add_row("...", "Truncated", "Search limit reached")
                    break
                    
        if count == 0:
            console.print("No matches found.")
        else:
            console.print(table)

    def compare(self, log1_name: str, log2_name: str):
        """Compare two logs."""
        path1 = LOGS_DIR / log1_name
        if not path1.exists():
            matches = list(LOGS_DIR.glob(f"*{log1_name}*"))
            if matches: path1 = matches[0]
            else: return

        path2 = LOGS_DIR / log2_name
        if not path2.exists():
            matches = list(LOGS_DIR.glob(f"*{log2_name}*"))
            if matches: path2 = matches[0]
            else: return

        def get_stats(path):
            s = defaultdict(lambda: {"total": 0, "success": 0})
            m = "unknown"
            for e in self._get_entries(path):
                m = e.get("model", m)
                lvl = e.get("level", 0)
                s[lvl]["total"] += 1
                if e.get("validation", {}).get("success", False):
                    s[lvl]["success"] += 1
            return m, s

        m1, s1 = get_stats(path1)
        m2, s2 = get_stats(path2)

        table = Table(title=f"Comparison: {m1} vs {m2}")
        table.add_column("Level", justify="center")
        table.add_column(m1, justify="right")
        table.add_column(m2, justify="right")
        table.add_column("Diff", justify="right")

        all_lvls = sorted(set(s1.keys()) | set(s2.keys()))
        for lvl in all_lvls:
            r1 = (s1[lvl]["success"] / s1[lvl]["total"] * 100) if s1[lvl]["total"] > 0 else 0
            r2 = (s2[lvl]["success"] / s2[lvl]["total"] * 100) if s2[lvl]["total"] > 0 else 0
            diff = r2 - r1
            diff_str = f"[green]+{diff:.1f}%[/green]" if diff > 0 else f"[red]{diff:.1f}%[/red]" if diff < 0 else "0.0%"
            table.add_row(f"L{lvl}", f"{r1:.1f}%", f"{r2:.1f}%", diff_str)

        # Overall
        t1 = sum(x["total"] for x in s1.values())
        sc1 = sum(x["success"] for x in s1.values())
        t2 = sum(x["total"] for x in s2.values())
        sc2 = sum(x["success"] for x in s2.values())
        
        o1 = (sc1 / t1 * 100) if t1 > 0 else 0
        o2 = (sc2 / t2 * 100) if t2 > 0 else 0
        odiff = o2 - o1
        odiff_str = f"[green]+{odiff:.1f}%[/green]" if odiff > 0 else f"[red]{odiff:.1f}%[/red]" if odiff < 0 else "0.0%"
        
        table.add_row("OVERALL", f"[bold]{o1:.1f}%[/bold]", f"[bold]{o2:.1f}%[/bold]", f"[bold]{odiff_str}[/bold]", style="bold bright_white")
        
        console.print(table)

def main():
    parser = argparse.ArgumentParser(description="Universal Benchmark Log Explorer")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # LS
    subparsers.add_parser("ls", help="List available logs")
    
    # Summary
    sum_p = subparsers.add_parser("summary", help="Show log summary")
    sum_p.add_argument("log", help="Log filename or partial name")
    
    # Failures
    fail_p = subparsers.add_parser("failures", help="List failed test cases")
    fail_p.add_argument("log", help="Log filename or partial name")
    fail_p.add_argument("--level", type=int, help="Filter by level")
    
    # Inspect
    ins_p = subparsers.add_parser("inspect", help="Detailed view of a specific run")
    ins_p.add_argument("log", help="Log filename or partial name")
    ins_p.add_argument("test_id", help="Test case ID (e.g., L3-01)")
    ins_p.add_argument("--run", type=int, default=0, help="Run index (default 0)")
    
    # Search
    srch_p = subparsers.add_parser("search", help="Search text in prompts or responses")
    srch_p.add_argument("log", help="Log filename or partial name")
    srch_p.add_argument("query", help="Text to search for")

    # Compare
    cmp_p = subparsers.add_parser("compare", help="Compare two logs")
    cmp_p.add_argument("log1", help="First log")
    cmp_p.add_argument("log2", help="Second log")

    # Last
    subparsers.add_parser("last", help="Show summary of the latest log")
    
    args = parser.parse_args()
    explorer = LogExplorer()
    
    if args.command == "ls":
        explorer.list_logs()
    elif args.command == "summary":
        explorer.summary(args.log)
    elif args.command == "failures":
        explorer.failures(args.log, args.level)
    elif args.command == "inspect":
        explorer.inspect(args.log, args.test_id, args.run)
    elif args.command == "search":
        explorer.search(args.log, args.query)
    elif args.command == "compare":
        explorer.compare(args.log1, args.log2)
    elif args.command == "last":
        # Find latest log
        logs = sorted(LOGS_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        if logs:
            explorer.summary(logs[0].name)
        else:
            console.print("[yellow]No logs found.[/yellow]")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
