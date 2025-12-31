"""
Test case generator.

Provides access to test cases by level, ID, tags, or suite with language support.
"""

from .test_cases import (
    TestCase,
    ALL_TESTS,
    CUSTOM_TESTS,
    LEVEL_1_TESTS,
    LEVEL_2_TESTS,
    LEVEL_3_TESTS,
    LEVEL_4_TESTS,
    LEVEL_5_TESTS,
)
from .bfcl_tests import (
    BFCL_TESTS,
    BFCL_LEVEL_1,
    BFCL_LEVEL_2,
    BFCL_LEVEL_3,
    BFCL_LEVEL_4,
)


class TestCaseGenerator:
    """Generator for accessing and filtering test cases with suite and language support."""
    
    def __init__(self, suite: str = "all", language: str = "en"):
        """
        Initialize with test suite and language selection.
        
        Args:
            suite: Test suite to use - "custom", "bfcl", or "all"
            language: Prompt language - "en" or "ru"
        """
        self.suite = suite
        self.language = language
        
        # Select tests based on suite
        if suite == "custom":
            self._all_tests = CUSTOM_TESTS
            self._tests_by_level = {
                1: LEVEL_1_TESTS,
                2: LEVEL_2_TESTS,
                3: LEVEL_3_TESTS,
                4: LEVEL_4_TESTS,
                5: LEVEL_5_TESTS,
            }
        elif suite == "bfcl":
            self._all_tests = BFCL_TESTS
            self._tests_by_level = {
                1: BFCL_LEVEL_1,
                2: BFCL_LEVEL_2,
                3: BFCL_LEVEL_3,
                4: BFCL_LEVEL_4,
            }
        else:  # "all"
            self._all_tests = CUSTOM_TESTS + BFCL_TESTS
            self._tests_by_level = {
                1: LEVEL_1_TESTS + BFCL_LEVEL_1,
                2: LEVEL_2_TESTS + BFCL_LEVEL_2,
                3: LEVEL_3_TESTS + BFCL_LEVEL_3,
                4: LEVEL_4_TESTS + BFCL_LEVEL_4,
                5: LEVEL_5_TESTS,  # Only custom tests have level 5
            }
        
        self._tests_by_id = {test.id: test for test in self._all_tests}
    
    def get_prompt(self, test: TestCase) -> str:
        """
        Get the prompt for a test in the configured language.
        
        Args:
            test: TestCase to get prompt from
            
        Returns:
            Prompt string in the configured language
        """
        if self.language == "ru":
            return test.prompt_ru
        return test.prompt_en
    
    def get_all_tests(self) -> list[TestCase]:
        """Get all test cases ordered by level."""
        return self._all_tests.copy()
    
    def get_tests_by_level(self, level: int) -> list[TestCase]:
        """Get test cases for a specific level."""
        return self._tests_by_level.get(level, []).copy()
    
    def get_tests_by_levels(self, levels: list[int]) -> list[TestCase]:
        """Get test cases for multiple levels, ordered by level."""
        tests = []
        for level in sorted(levels):
            tests.extend(self.get_tests_by_level(level))
        return tests
    
    def get_test_by_id(self, test_id: str) -> TestCase | None:
        """Get a single test case by ID."""
        return self._tests_by_id.get(test_id)
    
    def get_tests_by_tag(self, tag: str) -> list[TestCase]:
        """Get all test cases with a specific tag."""
        return [test for test in self._all_tests if tag in test.tags]
    
    def get_tests_by_source(self, source: str) -> list[TestCase]:
        """Get all test cases from a specific source (custom or bfcl)."""
        return [test for test in self._all_tests if test.source == source]
    
    def get_level_count(self, level: int) -> int:
        """Get the number of tests in a level."""
        return len(self._tests_by_level.get(level, []))
    
    def get_total_count(self) -> int:
        """Get total number of test cases."""
        return len(self._all_tests)
    
    def get_available_levels(self) -> list[int]:
        """Get list of available levels."""
        return sorted([level for level, tests in self._tests_by_level.items() if tests])
    
    def get_level_descriptions(self) -> dict[int, str]:
        """Get descriptions for each level."""
        descriptions = {
            1: "Simple Single Tool - Direct tool call with explicit parameters",
            2: "Tool Selection - Choose correct tool from multiple options",
            3: "Sequential Calls - Multiple tools called in order",
            4: "Parallel Calls - Multiple independent tool calls",
            5: "Complex Chains - Combination of sequential and parallel calls",
        }
        # Only return descriptions for available levels
        return {level: desc for level, desc in descriptions.items() 
                if level in self._tests_by_level and self._tests_by_level[level]}
    
    def get_suite_info(self) -> dict[str, int]:
        """Get information about tests by source."""
        custom_count = len([t for t in self._all_tests if t.source == "custom"])
        bfcl_count = len([t for t in self._all_tests if t.source == "bfcl"])
        return {
            "custom": custom_count,
            "bfcl": bfcl_count,
            "total": len(self._all_tests)
        }
