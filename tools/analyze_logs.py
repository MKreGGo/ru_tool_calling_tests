import json
import os
import glob
from collections import Counter

import sys

# Automatically find the latest .jsonl log file or use argument
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
log_dir = os.path.join(project_root, "logs")

if len(sys.argv) > 1:
    latest_log = sys.argv[1]
else:
    jsonl_files = glob.glob(os.path.join(log_dir, "*.jsonl"))
    if not jsonl_files:
        print("No .jsonl files found in logs directory.")
        exit(1)
    latest_log = max(jsonl_files, key=os.path.getmtime)

print(f"Analyzing log: {os.path.basename(latest_log)}")

report_file = os.path.join(project_root, "reports", "analysis_report.txt")

stats = {
    "total_runs": 0,
    "success_total": 0,
    "parse_errors": Counter(),
    "validation_errors": Counter(),
    "parse_error_examples": {},
    "validation_error_examples": {},
    "test_failures": {}
}

with open(latest_log, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
            
        if data.get("_type") == "metadata":
            continue

        stats["total_runs"] += 1
        
        validation = data.get("validation", {})
        success = validation.get("success", False)
        if success:
            stats["success_total"] += 1
        
        # Track parse errors
        pes = data.get("response", {}).get("parse_errors", [])
        for pe in pes:
            stats["parse_errors"][pe] += 1
            if pe not in stats["parse_error_examples"]:
                stats["parse_error_examples"][pe] = {
                    "raw_content": data.get("response", {}).get("raw_content"),
                    "test_id": data.get("test_id")
                }
            
        # Track validation errors
        ves = validation.get("errors", [])
        for ve in ves:
            err_type = ve
            if "arguments mismatch" in ve:
                err_type = "arguments mismatch"
            elif "missing but expected" in ve:
                err_type = "missing call"
            elif "unexpected call" in ve:
                err_type = "unexpected call"
            elif "not found in results" in ve:
                err_type = "call not found"
            
            stats["validation_errors"][err_type] += 1
            if err_type not in stats["validation_error_examples"]:
                stats["validation_error_examples"][err_type] = {
                    "ve": ve,
                    "test_id": data.get("test_id"),
                    "expected": validation.get("expected"),
                    "actual": validation.get("actual"),
                    "prompt": data.get("request", {}).get("user_prompt")
                }
            
        # Track failures per test
        if not success:
            test_id = data.get("test_id", "unknown")
            if test_id not in stats["test_failures"]:
                stats["test_failures"][test_id] = {
                    "count": 0,
                    "errors": Counter(),
                    "example": None
                }
            stats["test_failures"][test_id]["count"] += 1
            for ve in ves:
                stats["test_failures"][test_id]["errors"][ve] += 1
            
            if not stats["test_failures"][test_id]["example"]:
                stats["test_failures"][test_id]["example"] = {
                    "expected": validation.get("expected"),
                    "actual": validation.get("actual"),
                    "prompt": data.get("request", {}).get("user_prompt"),
                    "parse_errors": pes
                }

with open(report_file, 'w', encoding='utf-8') as rf:
    rf.write(f"Analyzed Log: {os.path.basename(latest_log)}\n")
    rf.write(f"Total Runs: {stats['total_runs']}\n")
    rf.write(f"Successful: {stats['success_total']}\n")
    rf.write(f"Overall Success Rate: {stats['success_total'] / stats['total_runs']:.2%}\n")

    rf.write("\n--- Parse Errors ---\n")
    for pe, count in stats["parse_errors"].items():
        rf.write(f"{count}: {pe}\n")
        example = stats["parse_error_examples"][pe]
        rf.write(f"  Example (Test {example['test_id']}):\n")
        rf.write(f"    Raw: {example['raw_content'][:500]}\n")

    rf.write("\n--- Validation Errors ---\n")
    for ve_type, count in stats["validation_errors"].items():
        rf.write(f"{count}: {ve_type}\n")
        example = stats["validation_error_examples"][ve_type]
        rf.write(f"  Example (Test {example['test_id']}):\n")
        rf.write(f"    Prompt: {example['prompt']}\n")
        rf.write(f"    Expected: {json.dumps(example['expected'], ensure_ascii=False)}\n")
        rf.write(f"    Actual:   {json.dumps(example['actual'], ensure_ascii=False)}\n")

    rf.write("\n--- Top Failing Tests ---\n")
    sorted_failures = sorted(stats["test_failures"].items(), key=lambda x: x[1]['count'], reverse=True)
    for test_id, failure_data in sorted_failures[:25]:
        rf.write(f"\nTest: {test_id} (Failures: {failure_data['count']})\n")
        for err, count in failure_data["errors"].most_common(3):
            rf.write(f"  - {count}: {err}\n")
        ex = failure_data["example"]
        rf.write(f"  Sample Prompt: {ex['prompt']}\n")
        rf.write(f"  Expected: {json.dumps(ex['expected'], ensure_ascii=False)}\n")
        rf.write(f"  Actual:   {json.dumps(ex['actual'], ensure_ascii=False)}\n")
        if ex['parse_errors']:
            rf.write(f"  Parse Errors: {ex['parse_errors']}\n")

print(f"Report generated: {report_file}")
