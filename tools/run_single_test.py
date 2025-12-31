import sys
import os
import asyncio
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.config import BenchmarkConfig
from benchmark.unified_runner import UnifiedRunner
from tests.bfcl_multi_turn_tests import BFCL_MULTI_TURN_BY_ID
from benchmark_logging.logger import BenchmarkLogger

async def run_test():
    model = "qwen3-4b-instruct-2507"
    test_id = "BFCL-4.3"
    lang = "ru"
    temp = 0.2
    
    config = BenchmarkConfig(
        model=model,
        language=lang,
        temperatures=[temp],
        runs_per_test=1
    )
    
    # Initialize logger
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/temp_test_{test_id}_{timestamp}.jsonl"
    logger = BenchmarkLogger(log_file)
    
    runner = UnifiedRunner(config, logger)
    
    # Get test case
    test = BFCL_MULTI_TURN_BY_ID.get(test_id)
    if not test:
        print(f"Test {test_id} not found!")
        return
        
    print(f"Running test {test_id} for model {model} (lang={lang}, temp={temp})...")
    
    # We call internal method for multi-turn test
    # Because _run_bfcl_multi_turn handles 3 turns correctly
    # Note: 4.3 is a 3-turn test
    
    # BFCL-4.3 is a special multi-turn test (3 turns)
    # UnifiedRunner._run_bfcl_multi_turn handles 2 and 3 turns
    result = runner._run_bfcl_multi_turn(test, temp, 0)
    
    print("\n" + "="*50)
    print(f"RESULTS FOR {test_id}:")
    print(f"Success: {result.success}")
    print(f"Num Turns: {result.num_turns}")
    
    print(f"\nTurn 1 (Success: {result.turn1_success})")
    print(f"  Calls: {[c.name + str(c.arguments) for c in result.turn1_parsed_calls]}")
    if result.turn1_errors:
        print(f"  Errors: {result.turn1_errors}")
        
    print(f"\nTurn 2 (Success: {result.turn2_success})")
    print(f"  Calls: {[c.name + str(c.arguments) for c in result.turn2_parsed_calls]}")
    if result.turn2_errors:
        print(f"  Errors: {result.turn2_errors}")
    
    if result.num_turns >= 3:
        print(f"\nTurn 3 (Success: {result.turn3_success})")
        print(f"  Calls: {[c.name + str(c.arguments) for c in result.turn3_parsed_calls]}")
        if result.turn3_errors:
            print(f"  Errors: {result.turn3_errors}")

if __name__ == "__main__":
    asyncio.run(run_test())
