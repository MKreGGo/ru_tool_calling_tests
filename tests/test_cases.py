"""
Test case definitions.

25+ test cases across 5 difficulty levels with bilingual support (EN/RU).
"""

from dataclasses import dataclass, field
from typing import Any

from tools.validator import ExpectedCalls, ExpectedCall


@dataclass
class TestCase:
    """A single test case with bilingual prompts and expectations."""
    
    id: str
    level: int
    prompt_en: str
    prompt_ru: str
    available_tools: list[str]
    expected_en: "ExpectedCalls"  # Expected calls for English prompt
    expected_ru: "ExpectedCalls | None" = None  # Expected calls for Russian prompt (None = same as EN)
    description: str = ""
    tags: list[str] = field(default_factory=list)
    source: str = "custom"  # "custom" | "bfcl"
    
    @property
    def expected(self) -> "ExpectedCalls":
        """Backward compatibility: returns expected_en."""
        return self.expected_en
    
    def get_expected(self, lang: str = "en") -> "ExpectedCalls":
        """Get expected calls for specified language."""
        if lang == "ru" and self.expected_ru is not None:
            return self.expected_ru
        return self.expected_en



# =============================================================================
# LEVEL 1: Simple Single Tool
# Direct tool call with explicit parameters
# =============================================================================

LEVEL_1_TESTS = [
    TestCase(
        id="L1-01",
        level=1,
        prompt_en="What is the weather in Moscow?",
        prompt_ru="Какая погода в Москве?",
        available_tools=["get_weather"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(name="get_weather", args={"city": "Moscow"})],
            mode="exact"
        ),
        expected_ru=ExpectedCalls(
            calls=[ExpectedCall(name="get_weather", args={"city": "Москва"})],
            mode="exact"
        ),
        description="Simple weather query for a single city",
        tags=["simple", "weather"]
    ),
    TestCase(
        id="L1-02",
        level=1,
        prompt_en="Calculate 15 multiplied by 23",
        prompt_ru="Вычислить 15 умножить на 23",
        available_tools=["calculate"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(name="calculate", args={"expression": "15 * 23"})],
            mode="exact"
        ),
        # No expected_ru - mathematical expressions are language-neutral
        description="Simple mathematical calculation",
        tags=["simple", "math"]
    ),
    TestCase(
        id="L1-03",
        level=1,
        prompt_en="What time is it in Tokyo?",
        prompt_ru="Который час в Токио?",
        available_tools=["get_time"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(name="get_time", args={"timezone": "Asia/Tokyo"})],
            mode="exact"
        ),
        # No expected_ru - timezone is a technical identifier
        description="Get time in a specific timezone",
        tags=["simple", "time"]
    ),
    TestCase(
        id="L1-04",
        level=1,
        prompt_en="Get the current stock price for Apple (AAPL)",
        prompt_ru="Получить текущую цену акций Apple (AAPL)",
        available_tools=["get_stock_price"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(name="get_stock_price", args={"symbol": "AAPL"})],
            mode="exact"
        ),
        # No expected_ru - stock symbol is technical
        description="Get stock price by ticker",
        tags=["simple", "stocks"]
    ),
    TestCase(
        id="L1-05",
        level=1,
        prompt_en="Read the contents of the file config.json",
        prompt_ru="Прочитать содержимое файла config.json",
        available_tools=["read_file"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(name="read_file", args={"path": "config.json"})],
            mode="exact"
        ),
        # No expected_ru - filename is technical
        description="Read a single file",
        tags=["simple", "file"]
    ),
    # =============================================================================
    # L1-06, L1-07: Parameter extraction with noise
    # =============================================================================
    TestCase(
        id="L1-06",
        level=1,
        prompt_en="Book a flight from Moscow to Paris on 2024-06-15. My passport number is AB1234567.",
        prompt_ru="Забронировать рейс из Москвы в Париж на 2024-06-15. Мой номер паспорта AB1234567.",
        available_tools=["book_flight"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(
                name="book_flight",
                args={"origin": "Moscow", "destination": "Paris", "date": "2024-06-15"}
            )],
            mode="exact"
        ),
        expected_ru=ExpectedCalls(
            calls=[ExpectedCall(
                name="book_flight",
                args={"origin": "Москва", "destination": "Париж", "date": "2024-06-15"}
            )],
            mode="exact"
        ),
        description="Extract 3 params, ignore 1 irrelevant (passport)",
        tags=["simple", "parameter-extraction", "noise"]
    ),
    TestCase(
        id="L1-07",
        level=1,
        prompt_en="Register a conference called 'AI Summit 2024' on 2024-09-20 in Berlin for up to 500 participants. The organizer is John Smith and the budget is $50000.",
        prompt_ru="Зарегистрировать конференцию 'AI Summit 2024' на 2024-09-20 в Берлине на максимум 500 участников. Организатор — Иван Смирнов, бюджет — $50000.",
        available_tools=["register_event"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(
                name="register_event",
                args={
                    "event_name": "AI Summit 2024",
                    "date": "2024-09-20",
                    "location": "Berlin",
                    "max_participants": 500,
                    "category": "conference"
                }
            )],
            mode="exact"
        ),
        expected_ru=ExpectedCalls(
            calls=[ExpectedCall(
                name="register_event",
                args={
                    "event_name": "AI Summit 2024",
                    "date": "2024-09-20",
                    "location": "Берлин",
                    "max_participants": 500,
                    "category": "conference"
                }
            )],
            mode="exact"
        ),
        description="Extract 5 params, ignore 2 irrelevant (organizer, budget)",
        tags=["simple", "parameter-extraction", "noise"]
    ),
]

# =============================================================================
# LEVEL 2: Tool Selection
# Choose the correct tool from multiple available options
# =============================================================================

LEVEL_2_TESTS = [
    TestCase(
        id="L2-01",
        level=2,
        prompt_en="Translate 'Hello, how are you?' to French",
        prompt_ru="Переведи 'Привет, как дела?' на французский",
        available_tools=["translate_text", "get_weather", "calculate"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(
                name="translate_text",
                args={"text": "Hello, how are you?", "target_language": "fr"}
            )],
            mode="exact"
        ),
        expected_ru=ExpectedCalls(
            calls=[ExpectedCall(
                name="translate_text",
                args={"text": "Привет, как дела?", "target_language": "fr"}
            )],
            mode="exact"
        ),
        description="Select translation tool among unrelated tools",
        tags=["selection", "translation"]
    ),
    TestCase(
        id="L2-02",
        level=2,
        prompt_en="Find all users named John in the database",
        prompt_ru="Найти всех пользователей с именем John в базе данных",
        available_tools=["search_database", "send_email", "create_file", "delete_file"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(
                name="search_database",
                args={"query": "John", "table": "users"}
            )],
            mode="exact"
        ),
        # No expected_ru - "John" is a proper name, stays same
        description="Select database search among file/email tools",
        tags=["selection", "database"]
    ),
    TestCase(
        id="L2-03",
        level=2,
        prompt_en="Convert 100 USD to EUR",
        prompt_ru="Конвертировать 100 USD в EUR",
        available_tools=["convert_currency", "calculate", "get_stock_price"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(
                name="convert_currency",
                args={"amount": 100, "from_currency": "USD", "to_currency": "EUR"}
            )],
            mode="exact"
        ),
        # No expected_ru - currency codes are technical
        description="Select currency converter among financial tools",
        tags=["selection", "currency"]
    ),
    TestCase(
        id="L2-04",
        level=2,
        prompt_en="List all files in the /home/user/documents directory",
        prompt_ru="Показать все файлы в директории /home/user/documents",
        available_tools=["list_directory", "read_file", "create_file", "delete_file"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(
                name="list_directory",
                args={"path": "/home/user/documents"}
            )],
            mode="exact"
        ),
        # No expected_ru - file path is technical
        description="Select list directory among file operation tools",
        tags=["selection", "file"]
    ),
    TestCase(
        id="L2-05",
        level=2,
        prompt_en="Create a new task: 'Review PR #123' with high priority",
        prompt_ru="Создать новую задачу: 'Ревью PR #123' с высоким приоритетом",
        available_tools=["create_task", "schedule_meeting", "send_email", "search_database"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(
                name="create_task",
                args={"title": "Review PR #123", "priority": "high"}
            )],
            mode="exact"
        ),
        expected_ru=ExpectedCalls(
            calls=[ExpectedCall(
                name="create_task",
                args={"title": "Ревью PR #123", "priority": "high"}
            )],
            mode="exact"
        ),
        description="Select task creation among productivity tools",
        tags=["selection", "task"]
    ),
    # =============================================================================
    # L2-06: Similar tool disambiguation
    # =============================================================================
    TestCase(
        id="L2-06",
        level=2,
        prompt_en="Send a text message to +7-999-123-4567 saying 'Meeting at 5pm'.",
        prompt_ru="Отправить текстовое сообщение на номер +7-999-123-4567 с текстом 'Встреча в 17:00'.",
        available_tools=["send_email", "send_sms", "send_push_notification"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(
                name="send_sms",
                args={"phone_number": "+7-999-123-4567", "message": "Meeting at 5pm"}
            )],
            mode="exact"
        ),
        expected_ru=ExpectedCalls(
            calls=[ExpectedCall(
                name="send_sms",
                args={"phone_number": "+7-999-123-4567", "message": "Встреча в 17:00"}
            )],
            mode="exact"
        ),
        description="Distinguish SMS from email and push among similar tools",
        tags=["selection", "disambiguation", "messaging"]
    ),
]

# =============================================================================
# LEVEL 3: Sequential Calls - MOVED TO multi_turn_tests.py
# These tests now use multi-turn execution for realistic sequential behavior
# =============================================================================

LEVEL_3_TESTS = []  # See tests/multi_turn_tests.py for multi-turn L3 tests

# =============================================================================
# LEVEL 4: Parallel Calls
# Multiple independent tool calls that can be made simultaneously
# =============================================================================

LEVEL_4_TESTS = [
    TestCase(
        id="L4-01",
        level=4,
        prompt_en="Get the weather in Moscow, Paris, and Tokyo",
        prompt_ru="Получить погоду в Москве, Париже и Токио",
        available_tools=["get_weather"],
        expected_en=ExpectedCalls(
            calls=[
                ExpectedCall(name="get_weather", args={"city": "Moscow"}),
                ExpectedCall(name="get_weather", args={"city": "Paris"}),
                ExpectedCall(name="get_weather", args={"city": "Tokyo"})
            ],
            mode="parallel"
        ),
        expected_ru=ExpectedCalls(
            calls=[
                ExpectedCall(name="get_weather", args={"city": "Москва"}),
                ExpectedCall(name="get_weather", args={"city": "Париж"}),
                ExpectedCall(name="get_weather", args={"city": "Токио"})
            ],
            mode="parallel"
        ),
        description="Get weather for multiple cities",
        tags=["parallel", "weather"]
    ),
    TestCase(
        id="L4-02",
        level=4,
        prompt_en="Read the files a.txt, b.txt, and c.txt",
        prompt_ru="Прочитать файлы a.txt, b.txt и c.txt",
        available_tools=["read_file"],
        expected_en=ExpectedCalls(
            calls=[
                ExpectedCall(name="read_file", args={"path": "a.txt"}),
                ExpectedCall(name="read_file", args={"path": "b.txt"}),
                ExpectedCall(name="read_file", args={"path": "c.txt"})
            ],
            mode="parallel"
        ),
        # No expected_ru - filenames are technical
        description="Read multiple files",
        tags=["parallel", "file"]
    ),
    TestCase(
        id="L4-03",
        level=4,
        prompt_en="Get stock prices for AAPL, GOOGL, and MSFT",
        prompt_ru="Получить цены акций AAPL, GOOGL и MSFT",
        available_tools=["get_stock_price"],
        expected_en=ExpectedCalls(
            calls=[
                ExpectedCall(name="get_stock_price", args={"symbol": "AAPL"}),
                ExpectedCall(name="get_stock_price", args={"symbol": "GOOGL"}),
                ExpectedCall(name="get_stock_price", args={"symbol": "MSFT"})
            ],
            mode="parallel"
        ),
        # No expected_ru - stock symbols are technical
        description="Get multiple stock prices",
        tags=["parallel", "stocks"]
    ),
    TestCase(
        id="L4-04",
        level=4,
        prompt_en="Translate 'Good morning' to French, German, and Spanish",
        prompt_ru="Перевести 'Доброе утро' на французский, немецкий и испанский",
        available_tools=["translate_text"],
        expected_en=ExpectedCalls(
            calls=[
                ExpectedCall(name="translate_text", args={"text": "Good morning", "target_language": "fr"}),
                ExpectedCall(name="translate_text", args={"text": "Good morning", "target_language": "de"}),
                ExpectedCall(name="translate_text", args={"text": "Good morning", "target_language": "es"})
            ],
            mode="parallel"
        ),
        expected_ru=ExpectedCalls(
            calls=[
                ExpectedCall(name="translate_text", args={"text": "Доброе утро", "target_language": "fr"}),
                ExpectedCall(name="translate_text", args={"text": "Доброе утро", "target_language": "de"}),
                ExpectedCall(name="translate_text", args={"text": "Доброе утро", "target_language": "es"})
            ],
            mode="parallel"
        ),
        description="Translate text to multiple languages",
        tags=["parallel", "translation"]
    ),
    TestCase(
        id="L4-05",
        level=4,
        prompt_en="Get the current time in New York, London, and Sydney",
        prompt_ru="Получить текущее время в Нью-Йорке, Лондоне и Сиднее",
        available_tools=["get_time"],
        expected_en=ExpectedCalls(
            calls=[
                ExpectedCall(name="get_time", args={"timezone": "America/New_York"}),
                ExpectedCall(name="get_time", args={"timezone": "Europe/London"}),
                ExpectedCall(name="get_time", args={"timezone": "Australia/Sydney"})
            ],
            mode="parallel"
        ),
        # No expected_ru - timezones are technical identifiers
        description="Get time in multiple timezones",
        tags=["parallel", "time"]
    ),
]

# =============================================================================
# LEVEL 5: Complex Chains - MOVED TO multi_turn_tests.py
# These tests now use multi-turn execution for realistic sequential behavior
# =============================================================================

LEVEL_5_TESTS = []  # See tests/multi_turn_tests.py for multi-turn L5 tests

# All tests combined (L1, L2, L4 only - single-turn tests)
ALL_TESTS = LEVEL_1_TESTS + LEVEL_2_TESTS + LEVEL_3_TESTS + LEVEL_4_TESTS + LEVEL_5_TESTS
CUSTOM_TESTS = ALL_TESTS  # Alias for clarity

