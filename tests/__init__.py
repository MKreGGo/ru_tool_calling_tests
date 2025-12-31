"""Tests package - test cases and generator with bilingual support."""

from .test_cases import (
    TestCase, 
    ExpectedCalls,
    LEVEL_1_TESTS, 
    LEVEL_2_TESTS, 
    LEVEL_3_TESTS, 
    LEVEL_4_TESTS, 
    LEVEL_5_TESTS,
    ALL_TESTS,
    CUSTOM_TESTS,
)
from .bfcl_tests import (
    BFCL_TESTS,
    BFCL_LEVEL_1,
    BFCL_LEVEL_2,
    BFCL_LEVEL_3,
    BFCL_LEVEL_4,
)
from .multi_turn_tests import (
    MultiTurnTestCase,
    ALL_MULTI_TURN_TESTS,
    MULTI_TURN_L3_TESTS,
    MULTI_TURN_L5_TESTS,
)
from .generator import TestCaseGenerator

__all__ = [
    "TestCase",
    "ExpectedCalls",
    "LEVEL_1_TESTS",
    "LEVEL_2_TESTS",
    "LEVEL_3_TESTS",
    "LEVEL_4_TESTS",
    "LEVEL_5_TESTS",
    "ALL_TESTS",
    "CUSTOM_TESTS",
    "BFCL_TESTS",
    "BFCL_LEVEL_1",
    "BFCL_LEVEL_2",
    "BFCL_LEVEL_3",
    "BFCL_LEVEL_4",
    "MultiTurnTestCase",
    "ALL_MULTI_TURN_TESTS",
    "MULTI_TURN_L3_TESTS",
    "MULTI_TURN_L5_TESTS",
    "TestCaseGenerator",
]


def get_all_tests(suite: str = "all") -> list[TestCase]:
    """
    Get tests filtered by suite type.
    
    Args:
        suite: Test suite to return - "custom", "bfcl", or "all"
        
    Returns:
        List of TestCase objects
    """
    if suite == "custom":
        return CUSTOM_TESTS
    elif suite == "bfcl":
        return BFCL_TESTS
    else:  # "all"
        return CUSTOM_TESTS + BFCL_TESTS


def get_prompt(test: TestCase, language: str = "en") -> str:
    """
    Get the prompt for a test in the specified language.
    
    Args:
        test: TestCase to get prompt from
        language: "en" for English, "ru" for Russian
        
    Returns:
        Prompt string in the requested language
    """
    if language == "ru":
        return test.prompt_ru
    return test.prompt_en
