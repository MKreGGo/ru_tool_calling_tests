"""
Multi-turn test case definitions.

Test cases for sequential multi-turn tool calling where the model
must first gather data and then use it in subsequent calls.
"""

from dataclasses import dataclass, field
from typing import Any

from tools.validator import ExpectedCalls, ExpectedCall


@dataclass
class MultiTurnTestCase:
    """
    A multi-turn test case with simulated tool results and bilingual support.
    
    Tests the model's ability to:
    1. Call the correct data-gathering tool first
    2. Process the simulated result
    3. Call the action tool with the obtained data
    """
    
    id: str
    level: int
    
    # Turn 1: Initial request
    prompt_en: str
    prompt_ru: str
    available_tools: list[str]
    expected_turn1_en: "ExpectedCalls"  # Expected for English prompt
    expected_turn1_ru: "ExpectedCalls | None" = None  # Expected for Russian prompt (None = same as EN)
    
    # Simulated result from turn 1 tool calls
    simulated_results: dict[str, str] = field(default_factory=dict)  # tool_name -> result
    
    # Turn 2: Follow-up after receiving tool results
    turn2_context_en: str = "Here are the results. Please continue with the task."
    turn2_context_ru: str = "Вот результаты. Продолжай выполнение задачи."
    expected_turn2_en: "ExpectedCalls | None" = None
    expected_turn2_ru: "ExpectedCalls | None" = None
    
    description: str = ""
    tags: list[str] = field(default_factory=list)
    source: str = "custom"
    
    @property
    def expected_turn1(self) -> "ExpectedCalls":
        """Backward compatibility."""
        return self.expected_turn1_en
    
    @property
    def expected_turn2(self) -> "ExpectedCalls | None":
        """Backward compatibility."""
        return self.expected_turn2_en
    
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


# =============================================================================
# LEVEL 3: Multi-Turn Sequential Tests
# =============================================================================

MULTI_TURN_L3_TESTS = [
    MultiTurnTestCase(
        id="L3-01",
        level=3,
        prompt_en="Read the file config.json and then email its contents to admin@example.com with subject 'Config File'",
        prompt_ru="Прочитать файл config.json и отправить его содержимое на admin@example.com с темой 'Config File'",
        available_tools=["read_file", "send_email", "create_file"],
        expected_turn1_en=ExpectedCalls(
            calls=[ExpectedCall(name="read_file", args={"path": "config.json"})],
            mode="exact"
        ),
        simulated_results={
            "read_file": '{"database": "postgres", "port": 5432, "host": "localhost", "user": "admin"}'
        },
        expected_turn2_en=ExpectedCalls(
            calls=[ExpectedCall(
                name="send_email",
                args={"to": "admin@example.com", "subject": "Config File"}
            )],
            mode="exact"
        ),
        description="Multi-turn: Read file, then email contents",
        tags=["multi-turn", "sequential", "file", "email"]
    ),
    MultiTurnTestCase(
        id="L3-02",
        level=3,
        prompt_en="Get the weather in Paris and translate the result to Russian",
        prompt_ru="Получить погоду в Париже и перевести результат на русский",
        available_tools=["get_weather", "translate_text", "send_email"],
        expected_turn1_en=ExpectedCalls(
            calls=[ExpectedCall(name="get_weather", args={"city": "Paris"})],
            mode="exact"
        ),
        expected_turn1_ru=ExpectedCalls(
            calls=[ExpectedCall(name="get_weather", args={"city": "Париж"})],
            mode="exact"
        ),
        simulated_results={
            "get_weather": "Paris: Temperature 18°C, partly cloudy, humidity 65%, wind 12 km/h from west"
        },
        expected_turn2_en=ExpectedCalls(
            calls=[ExpectedCall(name="translate_text", args={"target_language": "ru"})],
            mode="exact"
        ),
        description="Multi-turn: Get weather, then translate",
        tags=["multi-turn", "sequential", "weather", "translation"]
    ),
    MultiTurnTestCase(
        id="L3-03",
        level=3,
        prompt_en="Search for user 'alice' in the database and create a task to contact them",
        prompt_ru="Найти пользователя 'alice' в базе данных и создать задачу связаться с ним",
        available_tools=["search_database", "create_task", "send_email"],
        expected_turn1_en=ExpectedCalls(
            calls=[ExpectedCall(name="search_database", args={"query": "alice"})],
            mode="exact"
        ),
        simulated_results={
            "search_database": '[{"id": 42, "name": "Alice Johnson", "email": "alice.j@company.com", "department": "Engineering"}]'
        },
        expected_turn2_en=ExpectedCalls(
            calls=[ExpectedCall(name="create_task")],
            mode="exact"
        ),
        description="Multi-turn: Search DB, then create task",
        tags=["multi-turn", "sequential", "database", "task"]
    ),
    MultiTurnTestCase(
        id="L3-04",
        level=3,
        prompt_en="Get the stock price for GOOGL and calculate 10% of it",
        prompt_ru="Получить цену акций GOOGL и вычислить 10% от неё",
        available_tools=["get_stock_price", "calculate", "convert_currency"],
        expected_turn1_en=ExpectedCalls(
            calls=[ExpectedCall(name="get_stock_price", args={"symbol": "GOOGL"})],
            mode="exact"
        ),
        simulated_results={
            "get_stock_price": '{"symbol": "GOOGL", "price": 142.50, "currency": "USD", "change": "+1.25"}'
        },
        expected_turn2_en=ExpectedCalls(
            calls=[ExpectedCall(name="calculate")],
            mode="exact"
        ),
        description="Multi-turn: Get stock price, then calculate percentage",
        tags=["multi-turn", "sequential", "stocks", "math"]
    ),
    MultiTurnTestCase(
        id="L3-05",
        level=3,
        prompt_en="List files in /tmp and then delete the file named old_cache.txt if it exists",
        prompt_ru="Показать файлы в /tmp и затем удалить файл old_cache.txt если он существует",
        available_tools=["list_directory", "delete_file", "read_file"],
        expected_turn1_en=ExpectedCalls(
            calls=[ExpectedCall(name="list_directory", args={"path": "/tmp"})],
            mode="exact"
        ),
        simulated_results={
            "list_directory": '["cache.db", "old_cache.txt", "session_123.tmp", "logs.txt"]'
        },
        expected_turn2_en=ExpectedCalls(
            calls=[ExpectedCall(name="delete_file", args={"path": "/tmp/old_cache.txt"})],
            mode="exact"
        ),
        description="Multi-turn: List directory, then delete file",
        tags=["multi-turn", "sequential", "file"]
    ),
]

# =============================================================================
# LEVEL 5: Complex Multi-Turn Tests
# =============================================================================

MULTI_TURN_L5_TESTS = [
    MultiTurnTestCase(
        id="L5-01",
        level=5,
        prompt_en="Get the weather in Moscow, Paris, and Tokyo, then create a summary file called weather_report.txt with all results",
        prompt_ru="Получить погоду в Москве, Париже и Токио, затем создать файл weather_report.txt со всеми результатами",
        available_tools=["get_weather", "create_file", "read_file"],
        expected_turn1_en=ExpectedCalls(
            calls=[
                ExpectedCall(name="get_weather", args={"city": "Moscow"}),
                ExpectedCall(name="get_weather", args={"city": "Paris"}),
                ExpectedCall(name="get_weather", args={"city": "Tokyo"})
            ],
            mode="parallel"
        ),
        expected_turn1_ru=ExpectedCalls(
            calls=[
                ExpectedCall(name="get_weather", args={"city": "Москва"}),
                ExpectedCall(name="get_weather", args={"city": "Париж"}),
                ExpectedCall(name="get_weather", args={"city": "Токио"})
            ],
            mode="parallel"
        ),
        simulated_results={
            "get_weather_Moscow": "Moscow: -5°C, snow, humidity 80%",
            "get_weather_Paris": "Paris: 12°C, cloudy, humidity 70%",
            "get_weather_Tokyo": "Tokyo: 8°C, clear, humidity 55%"
        },
        expected_turn2_en=ExpectedCalls(
            calls=[ExpectedCall(name="create_file", args={"path": "weather_report.txt"})],
            mode="exact"
        ),
        description="Multi-turn: Parallel weather calls, then create report",
        tags=["multi-turn", "complex", "weather", "file"]
    ),
    MultiTurnTestCase(
        id="L5-02",
        level=5,
        prompt_en="Search for all orders in the database, generate a sales report for 2024, and email it to reports@company.com",
        prompt_ru="Найти все заказы в базе данных, сгенерировать отчёт по продажам за 2024 и отправить его на reports@company.com",
        available_tools=["search_database", "generate_report", "send_email", "create_file"],
        expected_turn1_en=ExpectedCalls(
            calls=[ExpectedCall(name="search_database", args={"table": "orders"})],
            mode="exact"
        ),
        expected_turn1_ru=ExpectedCalls(
            calls=[ExpectedCall(name="search_database", args={"table": "заказы"})],
            mode="exact"
        ),
        simulated_results={
            "search_database": '[{"id": 1, "total": 1500}, {"id": 2, "total": 2300}, {"id": 3, "total": 890}]'
        },
        turn2_context_en="Orders found. Now generate the sales report and send it.",
        turn2_context_ru="Заказы найдены. Теперь сгенерируй отчёт продаж и отправь его.",
        expected_turn2_en=ExpectedCalls(
            calls=[
                ExpectedCall(name="generate_report", args={"report_type": "sales"}),
                ExpectedCall(name="send_email", args={"to": "reports@company.com"})
            ],
            mode="sequential"
        ),
        expected_turn2_ru=ExpectedCalls(
            calls=[
                ExpectedCall(name="generate_report", args={"report_type": "продаж"}),
                ExpectedCall(name="send_email", args={"to": "reports@company.com"})
            ],
            mode="sequential"
        ),
        description="Multi-turn: Search DB → Generate report → Email",
        tags=["multi-turn", "complex", "database", "report", "email"]
    ),
    MultiTurnTestCase(
        id="L5-03",
        level=5,
        prompt_en="Schedule a meeting titled 'Project Review' with alice@company.com and bob@company.com for 2024-03-15 at 14:00, then create tasks for each participant to prepare materials",
        prompt_ru="Запланировать встречу 'Project Review' с alice@company.com и bob@company.com на 2024-03-15 в 14:00, затем создать задачу для каждого участника подготовить материалы",
        available_tools=["schedule_meeting", "create_task", "send_email"],
        expected_turn1_en=ExpectedCalls(
            calls=[ExpectedCall(name="schedule_meeting", args={
                "title": "Project Review",
                "participants": ["alice@company.com", "bob@company.com"]
            })],
            mode="exact"
        ),
        simulated_results={
            "schedule_meeting": '{"meeting_id": "mtg_123", "confirmed": true, "calendar_link": "https://cal.example.com/mtg_123"}'
        },
        expected_turn2_en=ExpectedCalls(
            calls=[
                ExpectedCall(name="create_task"),
                ExpectedCall(name="create_task")
            ],
            mode="parallel"
        ),
        description="Multi-turn: Schedule meeting, then create prep tasks",
        tags=["multi-turn", "complex", "meeting", "task"]
    ),
    MultiTurnTestCase(
        id="L5-04",
        level=5,
        prompt_en="Convert 1000 USD to EUR and to GBP, then calculate the total value in EUR (assume GBP to EUR rate is 1.15)",
        prompt_ru="Конвертировать 1000 USD в EUR и в GBP, затем вычислить общую сумму в EUR (курс GBP к EUR = 1.15)",
        available_tools=["convert_currency", "calculate"],
        expected_turn1_en=ExpectedCalls(
            calls=[
                ExpectedCall(name="convert_currency", args={"amount": 1000, "from_currency": "USD", "to_currency": "EUR"}),
                ExpectedCall(name="convert_currency", args={"amount": 1000, "from_currency": "USD", "to_currency": "GBP"})
            ],
            mode="parallel"
        ),
        simulated_results={
            "convert_currency_EUR": '{"from": "USD", "to": "EUR", "amount": 1000, "result": 920.50}',
            "convert_currency_GBP": '{"from": "USD", "to": "GBP", "amount": 1000, "result": 790.25}'
        },
        expected_turn2_en=ExpectedCalls(
            calls=[ExpectedCall(name="calculate")],
            mode="exact"
        ),
        description="Multi-turn: Parallel currency conversion, then calculate total",
        tags=["multi-turn", "complex", "currency", "math"]
    ),
    MultiTurnTestCase(
        id="L5-05",
        level=5,
        prompt_en="Read the files data1.csv, data2.csv, and data3.csv, then generate a performance report",
        prompt_ru="Прочитать файлы data1.csv, data2.csv и data3.csv, затем сгенерировать отчёт о производительности",
        available_tools=["read_file", "generate_report", "create_file"],
        expected_turn1_en=ExpectedCalls(
            calls=[
                ExpectedCall(name="read_file", args={"path": "data1.csv"}),
                ExpectedCall(name="read_file", args={"path": "data2.csv"}),
                ExpectedCall(name="read_file", args={"path": "data3.csv"})
            ],
            mode="parallel"
        ),
        simulated_results={
            "read_file_data1": "date,value\n2024-01-01,100\n2024-01-02,150",
            "read_file_data2": "date,value\n2024-01-01,200\n2024-01-02,180",
            "read_file_data3": "date,value\n2024-01-01,300\n2024-01-02,320"
        },
        expected_turn2_en=ExpectedCalls(
            calls=[ExpectedCall(name="generate_report", args={"report_type": "performance"})],
            mode="exact"
        ),
        description="Multi-turn: Read files, then generate report",
        tags=["multi-turn", "complex", "file", "report"]
    ),
]

# All multi-turn tests
ALL_MULTI_TURN_TESTS = MULTI_TURN_L3_TESTS + MULTI_TURN_L5_TESTS
