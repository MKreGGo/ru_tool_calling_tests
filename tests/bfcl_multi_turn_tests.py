"""
BFCL Multi-Turn Test Cases.

Multi-turn test cases for BFCL Level 3 and Level 4 tests that require
multiple conversation turns with state persistence.
"""

from dataclasses import dataclass, field
from typing import Optional

from tools.validator import ExpectedCalls, ExpectedCall


@dataclass
class BFCLMultiTurnTestCase:
    """
    BFCL multi-turn test case with 2 or 3 turns and bilingual support.
    
    For 2-turn tests: turn3 fields are None.
    For 3-turn tests: all fields are populated.
    """
    
    id: str
    level: int
    
    # Available tools for all turns
    available_tools: list[str]
    
    # Turn 1
    turn1_prompt_en: str
    turn1_prompt_ru: str
    expected_turn1_en: "ExpectedCalls"
    expected_turn1_ru: "ExpectedCalls | None" = None
    simulated_result1: str = ""
    
    # Turn 2
    turn2_prompt_en: str = ""
    turn2_prompt_ru: str = ""
    expected_turn2_en: "ExpectedCalls | None" = None
    expected_turn2_ru: "ExpectedCalls | None" = None
    simulated_result2: str = ""  # Empty for 2-turn tests
    
    # Turn 3 (optional for 2-turn tests)
    turn3_prompt_en: Optional[str] = None
    turn3_prompt_ru: Optional[str] = None
    expected_turn3_en: Optional["ExpectedCalls"] = None
    expected_turn3_ru: Optional["ExpectedCalls"] = None
    
    description: str = ""
    tags: list[str] = field(default_factory=list)
    source: str = "bfcl"
    
    @property
    def num_turns(self) -> int:
        return 3 if self.turn3_prompt_en else 2
    
    # Backward compatibility properties
    @property
    def expected_turn1(self) -> "ExpectedCalls":
        return self.expected_turn1_en
    
    @property
    def expected_turn2(self) -> "ExpectedCalls | None":
        return self.expected_turn2_en
    
    @property
    def expected_turn3(self) -> Optional["ExpectedCalls"]:
        return self.expected_turn3_en
    
    # Language-aware getters
    def get_expected_turn1(self, lang: str = "en") -> "ExpectedCalls":
        """Get expected turn 1 calls for specified language."""
        if lang == "ru" and self.expected_turn1_ru is not None:
            return self.expected_turn1_ru
        return self.expected_turn1_en
    
    def get_expected_turn2(self, lang: str = "en") -> "ExpectedCalls | None":
        """Get expected turn 2 calls for specified language."""
        if lang == "ru" and self.expected_turn2_ru is not None:
            return self.expected_turn2_ru
        return self.expected_turn2_en
    
    def get_expected_turn3(self, lang: str = "en") -> Optional["ExpectedCalls"]:
        """Get expected turn 3 calls for specified language."""
        if lang == "ru" and self.expected_turn3_ru is not None:
            return self.expected_turn3_ru
        return self.expected_turn3_en


# =============================================================================
# BFCL Level 3 & 4: Multi-Turn Tests (6 tests total)
# =============================================================================

BFCL_MULTI_TURN_TESTS = [
    # =========================================================================
    # TEST 3.1: File Management (3 turns)
    # =========================================================================
    BFCLMultiTurnTestCase(
        id="BFCL-3.1",
        level=3,
        available_tools=["file_copy", "list_directory", "file_archive"],
        
        turn1_prompt_en="Create a backup of report.txt",
        turn1_prompt_ru="Создать резервную копию report.txt",
        expected_turn1_en=ExpectedCalls(
            calls=[ExpectedCall(name="file_copy", args={"source": "report.txt"}, strict_args=False)],
            mode="exact"
        ),
        simulated_result1='{"success": true, "source": "report.txt", "destination": "report_backup.txt"}',
        
        turn2_prompt_en="Show me the file list",
        turn2_prompt_ru="Покажи список файлов",
        expected_turn2_en=ExpectedCalls(
            calls=[ExpectedCall(name="list_directory", args={"path": "."})],
            mode="exact"
        ),
        simulated_result2='{"files": ["report.txt", "report_backup.txt", "notes.md"]}',
        
        turn3_prompt_en="Archive the backup file",
        turn3_prompt_ru="Архивировать резервную копию",
        expected_turn3_en=ExpectedCalls(
            calls=[ExpectedCall(name="file_archive", strict_args=False)],
            mode="exact"
        ),
        
        description="Multi-turn file management: backup → list → archive",
        tags=["bfcl", "multi-turn", "file", "3-turn"]
    ),
    
    # =========================================================================
    # TEST 3.2: Ticket Management (3 turns)
    # =========================================================================
    BFCLMultiTurnTestCase(
        id="BFCL-3.2",
        level=3,
        available_tools=["create_ticket", "assign_ticket", "update_priority"],
        
        turn1_prompt_en="Create a support ticket for server downtime",
        turn1_prompt_ru="Создать тикет поддержки по простою сервера",
        expected_turn1_en=ExpectedCalls(
            calls=[ExpectedCall(name="create_ticket")],  # Only check tool name, not exact issue text
            mode="exact"
        ),
        expected_turn1_ru=ExpectedCalls(
            calls=[ExpectedCall(name="create_ticket")],  # Only check tool name, not exact issue text
            mode="exact"
        ),
        simulated_result1='{"ticket_id": "TKT-001", "status": "open"}',
        
        turn2_prompt_en="Assign it to the senior engineer",
        turn2_prompt_ru="Назначить его старшему инженеру",
        expected_turn2_en=ExpectedCalls(
            calls=[ExpectedCall(name="assign_ticket", args={"ticket_id": "TKT-001", "assignee": "senior engineer"})],
            mode="exact"
        ),
        expected_turn2_ru=ExpectedCalls(
            # Strict: model must use exact Russian text from prompt, no translation allowed
            calls=[ExpectedCall(name="assign_ticket", args={"ticket_id": "TKT-001", "assignee": "старший инженер"})],
            mode="exact"
        ),
        simulated_result2='{"ticket_id": "TKT-001", "assigned_to": "senior_engineer"}',
        
        turn3_prompt_en="Change priority to high",
        turn3_prompt_ru="Изменить приоритет на высокий",
        expected_turn3_en=ExpectedCalls(
            calls=[ExpectedCall(name="update_priority", args={"ticket_id": "TKT-001", "priority": "high"})],
            mode="exact"
        ),
        expected_turn3_ru=ExpectedCalls(
            # Strict: model must use exact Russian text from prompt
            calls=[ExpectedCall(name="update_priority", args={"ticket_id": "TKT-001", "priority": "высокий"})],
            mode="exact"
        ),
        
        description="Multi-turn ticket management: create → assign → priority",
        tags=["bfcl", "multi-turn", "ticket", "3-turn"]
    ),
    
    # =========================================================================
    # TEST 3.3: Long Context Robustness (3 turns, same as 3.1 but with distractors)
    # =========================================================================
    BFCLMultiTurnTestCase(
        id="BFCL-3.3",
        level=3,
        # More tools = distraction, model must focus on relevant ones
        available_tools=["file_copy", "list_directory", "file_archive", 
                        "send_email", "create_task", "search_database", "get_weather"],
        
        turn1_prompt_en="Create a backup of report.txt",
        turn1_prompt_ru="Создать резервную копию report.txt",
        expected_turn1_en=ExpectedCalls(
            calls=[ExpectedCall(name="file_copy", args={"source": "report.txt"}, strict_args=False)],
            mode="exact"
        ),
        simulated_result1='{"success": true, "source": "report.txt", "destination": "report_backup.txt"}',
        
        turn2_prompt_en="Show me the file list",
        turn2_prompt_ru="Покажи список файлов",
        expected_turn2_en=ExpectedCalls(
            calls=[ExpectedCall(name="list_directory", args={"path": "."})],
            mode="exact"
        ),
        simulated_result2='{"files": ["report.txt", "report_backup.txt", "notes.md"]}',
        
        turn3_prompt_en="Archive the backup file",
        turn3_prompt_ru="Архивировать резервную копию",
        expected_turn3_en=ExpectedCalls(
            calls=[ExpectedCall(name="file_archive", strict_args=False)],
            mode="exact"
        ),
        
        description="Long context robustness: same as 3.1 with distractor tools",
        tags=["bfcl", "multi-turn", "long-context", "3-turn"]
    ),
    
    # =========================================================================
    # TEST 3.4: Missing Tool Documentation (2 turns)
    # Turn 2 expects NO call because tool doc is "missing"
    # =========================================================================
    BFCLMultiTurnTestCase(
        id="BFCL-3.4",
        level=3,
        # Turn 1: find_files available
        # Turn 2: delete_files should NOT be called (doc missing = not in tools)
        available_tools=["find_files"],  # delete_files NOT available
        
        turn1_prompt_en="Find all .log files in the directory",
        turn1_prompt_ru="Найти все файлы .log в директории",
        expected_turn1_en=ExpectedCalls(
            calls=[ExpectedCall(
                name="find_files", 
                keywords={"pattern": [".log"]}
            )],
            mode="exact"
        ),
        simulated_result1='{"files": ["app.log", "error.log", "debug.log"]}',
        
        turn2_prompt_en="Delete those files",
        turn2_prompt_ru="Удалить эти файлы",
        expected_turn2_en=ExpectedCalls(
            calls=[],  # Should refuse - no delete tool available
            mode="exact"
        ),
        # No turn 3
        
        description="Missing tool doc: find files, then refuse delete (tool unavailable)",
        tags=["bfcl", "multi-turn", "refusal", "2-turn"]
    ),
    
    # =========================================================================
    # TEST 3.5: Missing Parameters / Clarification (2 turns)
    # Turn 1: model should NOT call tool (missing filename)
    # Turn 2: model should call with clarified info
    # =========================================================================
    BFCLMultiTurnTestCase(
        id="BFCL-3.5",
        level=3,
        available_tools=["file_archive"],
        
        turn1_prompt_en="I need to move a file to archive storage",
        turn1_prompt_ru="Мне нужно переместить файл в хранилище архива",
        expected_turn1_en=ExpectedCalls(
            calls=[],  # Should ask for clarification, not guess
            mode="exact"
        ),
        simulated_result1='',  # No tool was called
        
        turn2_prompt_en="Specifically, archive the latest backup named backup_2024.zip",
        turn2_prompt_ru="Конкретно, архивировать последнюю резервную копию backup_2024.zip",
        expected_turn2_en=ExpectedCalls(
            calls=[ExpectedCall(name="file_archive", args={"file": "backup_2024.zip"})],
            mode="exact"
        ),
        # No turn 3
        
        description="Missing params: ask clarification first, then execute",
        tags=["bfcl", "multi-turn", "clarification", "2-turn"]
    ),
    
    # =========================================================================
    # TEST 4.3: Web Search Multi-Hop Reasoning (3 turns)
    # =========================================================================
    BFCLMultiTurnTestCase(
        id="BFCL-4.3",
        level=4,
        available_tools=["web_search", "get_webpage"],
        
        turn1_prompt_en="What country produces Da Hong Pao tea?",
        turn1_prompt_ru="Какая страна производит чай Da Hong Pao?",
        expected_turn1_en=ExpectedCalls(
            calls=[ExpectedCall(
                name="web_search", 
                keywords={"query": ["da hong pao"]}
            )],
            mode="exact"
        ),
        expected_turn1_ru=ExpectedCalls(
            calls=[ExpectedCall(
                name="web_search", 
                keywords={"query": [["da hong pao", "да хун пао"]]}
            )],
            mode="exact"
        ),
        simulated_result1='{"results": [{"title": "Da Hong Pao - Wikipedia", "snippet": "Da Hong Pao is a famous oolong tea from Wuyi Mountains, Fujian, China"}]}',
        
        turn2_prompt_en="Who is the richest billionaire in China?",
        turn2_prompt_ru="Кто самый богатый миллиардер в Китае?",
        expected_turn2_en=ExpectedCalls(
            calls=[ExpectedCall(
                name="web_search", 
                keywords={"query": ["richest", "china"]}
            )],
            mode="exact"
        ),
        expected_turn2_ru=ExpectedCalls(
            calls=[ExpectedCall(
                name="web_search", 
                # 'богатый' variants: богатый, богатейший, богаче, богатого, богатым
                # 'Китай' variants: китай, китая, китае, китаем, китаю
                keywords={"query": [
                    ["богат"],
                    ["китай", "китая", "китае", "китаем", "китаю"]
                ]}
            )],
            mode="exact"
        ),
        simulated_result2='{"results": [{"title": "Forbes China Rich List", "snippet": "Zhong Shanshan tops the list with $68 billion"}]}',
        
        turn3_prompt_en="Get more details about the current richest billionaire",
        turn3_prompt_ru="Получить больше информации о нынешнем самом богатом миллиардере",
        expected_turn3_en=ExpectedCalls(
            calls=[ExpectedCall(
                name="web_search", 
                keywords={"query": [["zhong", "shanshan"]]}
            )],
            mode="exact"
        ),
        expected_turn3_ru=ExpectedCalls(
            calls=[ExpectedCall(
                name="web_search", 
                # Accept: name variants OR general terms about billionaire
                # Чжун Шаньшань, Zhong Shanshan, миллиардер, богатейший
                keywords={"query": [[
                    "чжун", "шаньшань", "zhong", "shanshan",
                    "миллиардер", "миллиардера", "миллиардере",
                    "богатейш", "forbes"
                ]]}
            )],
            mode="exact"
        ),
        
        description="Multi-hop web search: tea origin → China billionaires → details",
        tags=["bfcl", "multi-turn", "web-search", "3-turn"]
    ),
]

# Lookup by ID
BFCL_MULTI_TURN_BY_ID = {t.id: t for t in BFCL_MULTI_TURN_TESTS}

