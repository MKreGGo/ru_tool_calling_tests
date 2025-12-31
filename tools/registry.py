"""
Tool registry - collection of 15 fake tools for benchmarking.

Tools are designed with varying complexity levels:
- Simple: 1-2 required parameters
- Medium: 2-3 parameters with optional fields
- Complex: Multiple parameters with enums, arrays, nested objects
"""

from .schemas import ToolSchema, ToolParameter


# =============================================================================
# SIMPLE TOOLS (Level 1)
# =============================================================================

TOOL_GET_WEATHER = ToolSchema(
    name="get_weather",
    description="Get the current weather for a specified city",
    description_ru="Получить текущую погоду для указанного города",
    parameters={
        "city": ToolParameter(
            type="string",
            description="The city name to get weather for",
            description_ru="Название города для получения погоды",
            required=True
        ),
        "units": ToolParameter(
            type="string",
            description="Temperature units",
            description_ru="Единицы измерения температуры",
            required=False,
            enum=["celsius", "fahrenheit"],
            default="celsius"
        )
    }
)

TOOL_CALCULATE = ToolSchema(
    name="calculate",
    description="Perform a mathematical calculation",
    description_ru="Выполнить математическое вычисление",
    parameters={
        "expression": ToolParameter(
            type="string",
            description="Mathematical expression to evaluate (e.g., '2 + 2', '15 * 23')",
            description_ru="Математическое выражение для вычисления (например, '2 + 2', '15 * 23')",
            required=True
        )
    }
)

TOOL_GET_TIME = ToolSchema(
    name="get_time",
    description="Get the current time in a specified timezone",
    description_ru="Получить текущее время в указанном часовом поясе",
    parameters={
        "timezone": ToolParameter(
            type="string",
            description="Timezone name (e.g., 'Europe/Moscow', 'America/New_York', 'Asia/Tokyo')",
            description_ru="Название часового пояса (например, 'Europe/Moscow', 'America/New_York', 'Asia/Tokyo')",
            required=True
        )
    }
)

TOOL_GET_STOCK_PRICE = ToolSchema(
    name="get_stock_price",
    description="Get the current stock price for a ticker symbol",
    description_ru="Получить текущую цену акций по тикеру",
    parameters={
        "symbol": ToolParameter(
            type="string",
            description="Stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'MSFT')",
            description_ru="Тикер акции (например, 'AAPL', 'GOOGL', 'MSFT')",
            required=True
        )
    }
)

# =============================================================================
# MEDIUM COMPLEXITY TOOLS (Level 2-3)
# =============================================================================

TOOL_TRANSLATE_TEXT = ToolSchema(
    name="translate_text",
    description="Translate text from one language to another",
    description_ru="Перевести текст с одного языка на другой",
    parameters={
        "text": ToolParameter(
            type="string",
            description="The original text to translate. Do NOT pre-translate this text yourself.",
            description_ru="Оригинальный текст для перевода. НЕ переводи текст самостоятельно.",
            required=True
        ),
        "target_language": ToolParameter(
            type="string",
            description="Target language code (e.g., 'en', 'ru', 'fr', 'de', 'es', 'ja', 'zh')",
            description_ru="Код целевого языка (например, 'en', 'ru', 'fr', 'de', 'es', 'ja', 'zh')",
            required=True
        ),
        "source_language": ToolParameter(
            type="string",
            description="Source language code (auto-detect if not specified)",
            description_ru="Код исходного языка (автоопределение, если не указан)",
            required=False
        )
    }
)

TOOL_SEARCH_DATABASE = ToolSchema(
    name="search_database",
    description="Search for records in a database",
    description_ru="Поиск записей в базе данных",
    parameters={
        "query": ToolParameter(
            type="string",
            description="Search query string",
            description_ru="Поисковый запрос",
            required=True
        ),
        "table": ToolParameter(
            type="string",
            description="Database table to search",
            description_ru="Таблица базы данных для поиска",
            required=False,
            enum=["users", "products", "orders", "logs"],
            default="users"
        ),
        "limit": ToolParameter(
            type="integer",
            description="Maximum number of results to return",
            description_ru="Максимальное количество результатов",
            required=False,
            default=10
        )
    }
)

TOOL_SEND_EMAIL = ToolSchema(
    name="send_email",
    description="Send an email message",
    description_ru="Отправить электронное письмо",
    parameters={
        "to": ToolParameter(
            type="string",
            description="Recipient email address",
            description_ru="Адрес электронной почты получателя",
            required=True
        ),
        "subject": ToolParameter(
            type="string",
            description="Email subject line",
            description_ru="Тема письма",
            required=True
        ),
        "body": ToolParameter(
            type="string",
            description="Email body content",
            description_ru="Текст письма",
            required=True
        ),
        "cc": ToolParameter(
            type="string",
            description="CC recipients (comma-separated)",
            description_ru="Получатели копии (через запятую)",
            required=False
        )
    }
)

TOOL_CONVERT_CURRENCY = ToolSchema(
    name="convert_currency",
    description="Convert an amount from one currency to another",
    description_ru="Конвертировать сумму из одной валюты в другую",
    parameters={
        "amount": ToolParameter(
            type="number",
            description="Amount to convert",
            description_ru="Сумма для конвертации",
            required=True
        ),
        "from_currency": ToolParameter(
            type="string",
            description="Source currency code (e.g., 'USD', 'EUR', 'RUB')",
            description_ru="Код исходной валюты (например, 'USD', 'EUR', 'RUB')",
            required=True
        ),
        "to_currency": ToolParameter(
            type="string",
            description="Target currency code (e.g., 'USD', 'EUR', 'RUB')",
            description_ru="Код целевой валюты (например, 'USD', 'EUR', 'RUB')",
            required=True
        )
    }
)

# =============================================================================
# FILE OPERATION TOOLS (Level 3-4)
# =============================================================================

TOOL_READ_FILE = ToolSchema(
    name="read_file",
    description="Read the contents of a file",
    description_ru="Прочитать содержимое файла",
    parameters={
        "path": ToolParameter(
            type="string",
            description="Path to the file to read",
            description_ru="Путь к файлу для чтения",
            required=True
        ),
        "encoding": ToolParameter(
            type="string",
            description="File encoding",
            description_ru="Кодировка файла",
            required=False,
            default="utf-8"
        )
    }
)

TOOL_CREATE_FILE = ToolSchema(
    name="create_file",
    description="Create a new file with specified content",
    description_ru="Создать новый файл с указанным содержимым",
    parameters={
        "path": ToolParameter(
            type="string",
            description="Path where the file should be created",
            description_ru="Путь для создания файла",
            required=True
        ),
        "content": ToolParameter(
            type="string",
            description="Content to write to the file",
            description_ru="Содержимое для записи в файл",
            required=True
        ),
        "overwrite": ToolParameter(
            type="boolean",
            description="Whether to overwrite if file exists",
            description_ru="Перезаписать файл, если существует",
            required=False,
            default=False
        )
    }
)

TOOL_DELETE_FILE = ToolSchema(
    name="delete_file",
    description="Delete a file",
    description_ru="Удалить файл",
    parameters={
        "path": ToolParameter(
            type="string",
            description="Path to the file to delete",
            description_ru="Путь к файлу для удаления",
            required=True
        )
    }
)

TOOL_LIST_DIRECTORY = ToolSchema(
    name="list_directory",
    description="List files and subdirectories in a directory",
    description_ru="Показать файлы и подкаталоги в директории",
    parameters={
        "path": ToolParameter(
            type="string",
            description="Path to the directory",
            description_ru="Путь к директории",
            required=True
        ),
        "include_hidden": ToolParameter(
            type="boolean",
            description="Whether to include hidden files",
            description_ru="Включать скрытые файлы",
            required=False,
            default=False
        )
    }
)

# =============================================================================
# COMPLEX TOOLS (Level 4-5)
# =============================================================================

TOOL_SCHEDULE_MEETING = ToolSchema(
    name="schedule_meeting",
    description="Schedule a meeting with participants",
    description_ru="Запланировать встречу с участниками",
    parameters={
        "title": ToolParameter(
            type="string",
            description="Meeting title",
            description_ru="Название встречи",
            required=True
        ),
        "participants": ToolParameter(
            type="array",
            description="List of participant email addresses",
            description_ru="Список email-адресов участников",
            required=True,
            items={"type": "string"}
        ),
        "start_time": ToolParameter(
            type="string",
            description="Meeting start time in ISO 8601 format",
            description_ru="Время начала встречи в формате ISO 8601",
            required=True
        ),
        "duration_minutes": ToolParameter(
            type="integer",
            description="Meeting duration in minutes (integer number)",
            description_ru="Продолжительность встречи в минутах (целое число)",
            required=True
        ),
        "location": ToolParameter(
            type="string",
            description="Meeting location or video call link",
            description_ru="Место встречи или ссылка на видеозвонок",
            required=False
        ),
        "description": ToolParameter(
            type="string",
            description="Meeting description/agenda",
            description_ru="Описание встречи/повестка дня",
            required=False
        )
    }
)

TOOL_CREATE_TASK = ToolSchema(
    name="create_task",
    description="Create a new task in the task management system",
    description_ru="Создать новую задачу в системе управления задачами",
    parameters={
        "title": ToolParameter(
            type="string",
            description="Task title",
            description_ru="Название задачи",
            required=True
        ),
        "description": ToolParameter(
            type="string",
            description="Task description",
            description_ru="Описание задачи",
            required=False
        ),
        "assignee": ToolParameter(
            type="string",
            description="Email of the person assigned to the task",
            description_ru="Email ответственного за задачу",
            required=False
        ),
        "due_date": ToolParameter(
            type="string",
            description="Due date in YYYY-MM-DD format",
            description_ru="Срок выполнения в формате YYYY-MM-DD",
            required=False
        ),
        "priority": ToolParameter(
            type="string",
            description="Task priority",
            description_ru="Приоритет задачи",
            required=False,
            enum=["low", "medium", "high", "urgent"],
            default="medium"
        )
    }
)

TOOL_GENERATE_REPORT = ToolSchema(
    name="generate_report",
    description="Generate a report based on specified parameters",
    description_ru="Сгенерировать отчёт на основе указанных параметров",
    parameters={
        "report_type": ToolParameter(
            type="string",
            description="Type of report to generate",
            description_ru="Тип отчёта для генерации",
            required=True,
            enum=["sales", "inventory", "users", "performance", "financial"]
        ),
        "start_date": ToolParameter(
            type="string",
            description="Report start date in YYYY-MM-DD format",
            description_ru="Дата начала отчёта в формате YYYY-MM-DD",
            required=True
        ),
        "end_date": ToolParameter(
            type="string",
            description="Report end date in YYYY-MM-DD format",
            description_ru="Дата окончания отчёта в формате YYYY-MM-DD",
            required=True
        ),
        "format": ToolParameter(
            type="string",
            description="Output format",
            description_ru="Формат вывода",
            required=False,
            enum=["pdf", "csv", "json", "html"],
            default="pdf"
        ),
        "filters": ToolParameter(
            type="object",
            description="Additional filters for the report",
            description_ru="Дополнительные фильтры для отчёта",
            required=False
        )
    }
)


# =============================================================================
# PARAMETER EXTRACTION TESTS (Level 1 advanced)
# =============================================================================

TOOL_BOOK_FLIGHT = ToolSchema(
    name="book_flight",
    description="Book a flight between two cities on a specific date",
    description_ru="Забронировать рейс между двумя городами на определённую дату",
    parameters={
        "origin": ToolParameter(
            type="string",
            description="Departure city",
            description_ru="Город вылета",
            required=True
        ),
        "destination": ToolParameter(
            type="string",
            description="Arrival city",
            description_ru="Город прибытия",
            required=True
        ),
        "date": ToolParameter(
            type="string",
            description="Flight date in YYYY-MM-DD format",
            description_ru="Дата рейса в формате YYYY-MM-DD",
            required=True
        )
    }
)

TOOL_REGISTER_EVENT = ToolSchema(
    name="register_event",
    description="Register a new event or conference",
    description_ru="Зарегистрировать новое мероприятие или конференцию",
    parameters={
        "event_name": ToolParameter(
            type="string",
            description="Name of the event",
            description_ru="Название мероприятия",
            required=True
        ),
        "date": ToolParameter(
            type="string",
            description="Event date in YYYY-MM-DD format",
            description_ru="Дата мероприятия в формате YYYY-MM-DD",
            required=True
        ),
        "location": ToolParameter(
            type="string",
            description="Event location/venue",
            description_ru="Место проведения",
            required=True
        ),
        "max_participants": ToolParameter(
            type="integer",
            description="Maximum number of participants",
            description_ru="Максимальное количество участников",
            required=True
        ),
        "category": ToolParameter(
            type="string",
            description="Event category",
            description_ru="Категория мероприятия",
            required=True,
            enum=["conference", "workshop", "meetup"]
        )
    }
)

# =============================================================================
# SIMILAR TOOL DISAMBIGUATION (Level 2 advanced)
# =============================================================================

TOOL_SEND_SMS = ToolSchema(
    name="send_sms",
    description="Send an SMS text message to a phone number",
    description_ru="Отправить SMS-сообщение на номер телефона",
    parameters={
        "phone_number": ToolParameter(
            type="string",
            description="Recipient phone number",
            description_ru="Номер телефона получателя",
            required=True
        ),
        "message": ToolParameter(
            type="string",
            description="Text message content",
            description_ru="Текст сообщения",
            required=True
        )
    }
)

TOOL_SEND_PUSH_NOTIFICATION = ToolSchema(
    name="send_push_notification",
    description="Send a push notification to a mobile device",
    description_ru="Отправить push-уведомление на мобильное устройство",
    parameters={
        "device_id": ToolParameter(
            type="string",
            description="Target device ID",
            description_ru="ID целевого устройства",
            required=True
        ),
        "title": ToolParameter(
            type="string",
            description="Notification title",
            description_ru="Заголовок уведомления",
            required=True
        ),
        "body": ToolParameter(
            type="string",
            description="Notification body text",
            description_ru="Текст уведомления",
            required=True
        )
    }
)


# =============================================================================
# TOOL REGISTRY
# =============================================================================

TOOL_REGISTRY: dict[str, ToolSchema] = {
    # Simple tools
    "get_weather": TOOL_GET_WEATHER,
    "calculate": TOOL_CALCULATE,
    "get_time": TOOL_GET_TIME,
    "get_stock_price": TOOL_GET_STOCK_PRICE,
    
    # Parameter extraction tests (L1 advanced)
    "book_flight": TOOL_BOOK_FLIGHT,
    "register_event": TOOL_REGISTER_EVENT,
    
    # Medium complexity
    "translate_text": TOOL_TRANSLATE_TEXT,
    "search_database": TOOL_SEARCH_DATABASE,
    "send_email": TOOL_SEND_EMAIL,
    "convert_currency": TOOL_CONVERT_CURRENCY,
    
    # Similar tool disambiguation (L2 advanced)
    "send_sms": TOOL_SEND_SMS,
    "send_push_notification": TOOL_SEND_PUSH_NOTIFICATION,
    
    # File operations
    "read_file": TOOL_READ_FILE,
    "create_file": TOOL_CREATE_FILE,
    "delete_file": TOOL_DELETE_FILE,
    "list_directory": TOOL_LIST_DIRECTORY,
    
    # Complex tools
    "schedule_meeting": TOOL_SCHEDULE_MEETING,
    "create_task": TOOL_CREATE_TASK,
    "generate_report": TOOL_GENERATE_REPORT,
}


def get_tool(name: str) -> ToolSchema | None:
    """Get a tool schema by name."""
    return TOOL_REGISTRY.get(name)


def get_tools_by_names(names: list[str]) -> list[ToolSchema]:
    """Get multiple tool schemas by names."""
    return [TOOL_REGISTRY[name] for name in names if name in TOOL_REGISTRY]


def get_all_tool_names() -> list[str]:
    """Get all available tool names."""
    return list(TOOL_REGISTRY.keys())


# =============================================================================
# BFCL TOOLS INTEGRATION
# =============================================================================

def get_bfcl_tools_by_names(names: list[str]) -> list['ToolSchema']:
    """
    Get BFCL tool schemas by names.
    
    Converts BFCL tool schemas to ToolSchema format for compatibility.
    Falls back to standard registry if tool not found in BFCL.
    """
    from .bfcl_tools import BFCL_TOOL_SCHEMAS
    
    tools = []
    for name in names:
        if name in BFCL_TOOL_SCHEMAS:
            # Convert BFCL schema dict to ToolSchema
            schema_dict = BFCL_TOOL_SCHEMAS[name]
            params = {}
            prop_schema = schema_dict.get("parameters", {}).get("properties", {})
            required = schema_dict.get("parameters", {}).get("required", [])
            
            for param_name, param_info in prop_schema.items():
                params[param_name] = ToolParameter(
                    type=param_info.get("type", "string"),
                    description=param_info.get("description", ""),
                    description_ru=param_info.get("description_ru"),
                    required=param_name in required,
                    enum=param_info.get("enum"),
                    default=param_info.get("default")
                )
            
            tool = ToolSchema(
                name=schema_dict["name"],
                description=schema_dict.get("description", ""),
                description_ru=schema_dict.get("description_ru"),
                parameters=params
            )
            tools.append(tool)
        elif name in TOOL_REGISTRY:
            # Fallback to standard registry
            tools.append(TOOL_REGISTRY[name])
    
    return tools


def get_unified_registry() -> dict[str, 'ToolSchema']:
    """
    Get unified registry containing both custom and BFCL tools.
    
    Returns:
        Dict mapping tool names to ToolSchema objects
    """
    from .bfcl_tools import BFCL_TOOL_SCHEMAS
    
    # Start with base registry
    registry = dict(TOOL_REGISTRY)
    
    # Add BFCL tools
    for name, schema_dict in BFCL_TOOL_SCHEMAS.items():
        if name not in registry:
            params = {}
            prop_schema = schema_dict.get("parameters", {}).get("properties", {})
            required = schema_dict.get("parameters", {}).get("required", [])
            
            for param_name, param_info in prop_schema.items():
                params[param_name] = ToolParameter(
                    type=param_info.get("type", "string"),
                    description=param_info.get("description", ""),
                    description_ru=param_info.get("description_ru"),
                    required=param_name in required,
                    enum=param_info.get("enum"),
                    default=param_info.get("default")
                )
            
            registry[name] = ToolSchema(
                name=schema_dict["name"],
                description=schema_dict.get("description", ""),
                description_ru=schema_dict.get("description_ru"),
                parameters=params
            )
    
    return registry
