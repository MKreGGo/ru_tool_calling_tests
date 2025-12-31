"""
LLM Tool Calling Benchmark Application

Configuration settings for the benchmark.
"""

from dataclasses import dataclass, field


@dataclass
class BenchmarkConfig:
    """Main configuration for the benchmark."""
    
    # LLM settings
    api_url: str = "http://172.26.16.1:8000/v1"
    model: str = ""
    api_key: str = "lm-studio"  # LM Studio default
    max_tokens: int = 32000
    
    # Benchmark settings
    runs_per_test: int = 3
    temperatures: list[float] = field(default_factory=lambda: [0.2, 0.5, 0.8])
    levels: list[int] = field(default_factory=lambda: [1, 2, 3, 4, 5])
    
    # Test selection
    test_suite: str = "all"  # "custom" | "bfcl" | "all"
    language: str = "en"     # "en" | "ru"
    
    # Response format
    response_format: str = "auto"  # auto, openai, anthropic, mistral, hermes, raw_json
    
    # Timeouts
    request_timeout: int = 120
    max_retries: int = 3
    
    # Output
    output_path: str = ""
    verbose: bool = False


# System prompts for different formats
SYSTEM_PROMPTS = {
    "openai": """You are a helpful AI assistant with access to tools. When you need to use a tool, respond with a function call in the standard format. 

CRITICAL INSTRUCTIONS:
1. Use exact data types specified in the tool schema (e.g., pass numbers as numbers, not strings).
2. Do NOT translate or modify parameter values unless the tool's description explicitly asks for it. Use the original values from the user query.
3. If a tool can be used to answer the request — you MUST use it. PRIORITY: tools first, text second.""",
    
    "anthropic": """You are a helpful AI assistant with access to tools. When you need to use a tool, use the tool_use format.

CRITICAL INSTRUCTIONS:
1. Use exact data types specified in the tool schema (e.g., pass numbers as numbers, not strings).
2. Do NOT translate or modify parameter values unless the tool's description explicitly asks for it. Use the original values from the user query.
3. If a tool can be used to answer the request — you MUST use it. PRIORITY: tools first, text second.""",
    
    "hermes": """You are a function calling AI model. You are provided with function signatures within <tools></tools> XML tags. You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug into functions.

CRITICAL INSTRUCTIONS:
1. Use exact data types specified in the tool schema (e.g., pass numbers as numbers, not strings).
2. Do NOT translate or modify parameter values unless the tool's description explicitly asks for it. Use the original values from the user query.

When calling tools, use the following format:
<tool_call>
{"name": "function_name", "arguments": {"arg1": "value1"}}
</tool_call>""",
    
    "mistral": """You are a helpful AI assistant with access to tools. When you need to use a tool, respond with a function call. 

CRITICAL INSTRUCTIONS:
1. Use exact data types specified in the tool schema (e.g., pass numbers as numbers, not strings).
2. Do NOT translate or modify parameter values unless the tool's description explicitly asks for it. Use the original values from the user query.
3. If a tool can be used to answer the request — you MUST use it. PRIORITY: tools first, text second.""",
    
    "raw_json": """You are a helpful AI assistant with access to tools. When you need to use a tool, respond with a JSON object containing the tool name and arguments.

CRITICAL INSTRUCTIONS:
1. Use exact data types specified in the tool schema (e.g., pass numbers as numbers, not strings).
2. Do NOT translate or modify parameter values unless the tool's description explicitly asks for it. Use the original values from the user query.

Format:
{"tool": "tool_name", "arguments": {"arg1": "value1"}}

For multiple tool calls, respond with a JSON array:
[{"tool": "tool1", "arguments": {...}}, {"tool": "tool2", "arguments": {...}}]"""
}

# Russian system prompts
SYSTEM_PROMPTS_RU = {
    "openai": """Ты полезный ИИ-ассистент с доступом к инструментам. Когда тебе нужно использовать инструмент, отвечай вызовом функции в стандартном формате. 

КРИТИЧЕСКИЕ ИНСТРУКЦИИ:
1. Используй точные типы данных, указанные в схеме инструмента (например, передавай числа как числа, а не строки).
2. НЕ переводи и не изменяй значения параметров, если описание инструмента явно не требует этого. Используй оригинальные значения из запроса пользователя.
3. Если для ответа можно использовать инструмент — ОБЯЗАТЕЛЬНО используй его. ПРИОРИТЕТ: сначала инструменты, потом текст.""",
    
    "anthropic": """Ты полезный ИИ-ассистент с доступом к инструментам. Когда тебе нужно использовать инструмент, используй формат tool_use. 

КРИТИЧЕСКИЕ ИНСТРУКЦИИ:
1. Используй точные типы данных, указанные в схеме инструмента (например, передавай числа как числа, а не строки).
2. НЕ переводи и не изменяй значения параметров, если описание инструмента явно не требует этого. Используй оригинальные значения из запроса пользователя.
3. Если для ответа можно использовать инструмент — ОБЯЗАТЕЛЬНО используй его. ПРИОРИТЕТ: сначала инструменты, потом текст.""",
    
    "hermes": """Ты модель ИИ для вызова функций. Тебе предоставлены сигнатуры функций в XML-тегах <tools></tools>. Ты можешь вызывать одну или несколько функций для помощи с запросом пользователя. Не делай предположений о значениях параметров функций.

КРИТИЧЕСКИЕ ИНСТРУКЦИИ:
1. Используй точные типы данных, указанные в схеме инструмента (например, передавай числа как числа, а не строки).
2. НЕ переводи и не изменяй значения параметров, если описание инструмента явно не требует этого. Используй оригинальные значения из запроса пользователя.

При вызове инструментов используй следующий формат:
<tool_call>
{"name": "function_name", "arguments": {"arg1": "value1"}}
</tool_call>""",
    
    "mistral": """Ты полезный ИИ-ассистент с доступом к инструментам. Когда тебе нужно использовать инструмент, отвечай вызовом функции.

КРИТИЧЕСКИЕ ИНСТРУКЦИИ:
1. Используй точные типы данных, указанные в схеме инструмента (например, передавай числа как числа, а не строки).
2. НЕ переводи и не изменяй значения параметров, если описание инструмента явно не требует этого. Используй оригинальные значения из запроса пользователя.
3. Если для ответа можно использовать инструмент — ОБЯЗАТЕЛЬНО используй его. ПРИОРИТЕТ: сначала инструменты, потом текст.""",
    
    "raw_json": """Ты полезный ИИ-ассистент с доступом к инструментам. Когда тебе нужно использовать инструмент, отвечай JSON-объектом с именем инструмента и аргументами.

КРИТИЧЕСКИЕ ИНСТРУКЦИИ:
1. Используй точные типы данных, указанные в схеме инструмента (например, передавай числа как числа, а не строки).
2. НЕ переводи и не изменяй значения параметров, если описание инструмента явно не требует этого. Используй оригинальные значения из запроса пользователя.

Формат:
{"tool": "tool_name", "arguments": {"arg1": "value1"}}

Для нескольких вызовов отвечай JSON-массивом:
[{"tool": "tool1", "arguments": {...}}, {"tool": "tool2", "arguments": {...}}]"""
}

DEFAULT_SYSTEM_PROMPT = SYSTEM_PROMPTS["openai"]


# Sequential execution instructions for multi-turn tests
SEQUENTIAL_INSTRUCTION_EN = """
IMPORTANT FOR SEQUENTIAL TASKS:
If the task requires multiple steps (e.g., "do X and then do Y"), execute ONLY the FIRST step now and wait for results before proceeding. Do NOT call multiple tools at once for sequential tasks. Complete one action, receive its result, then proceed to the next.
"""

SEQUENTIAL_INSTRUCTION_RU = """
ВАЖНО ДЛЯ ПОСЛЕДОВАТЕЛЬНЫХ ЗАДАЧ:
Если задача требует нескольких шагов (например, "сделай X, затем сделай Y"), выполни ТОЛЬКО ПЕРВЫЙ шаг сейчас и дождись результатов перед продолжением. НЕ вызывай несколько инструментов сразу для последовательных задач. Выполни одно действие, получи его результат, затем переходи к следующему.
"""


def get_system_prompt(format_type: str = "openai", language: str = "en", sequential: bool = False) -> str:
    """
    Get system prompt for the specified format and language.
    
    Args:
        format_type: Response format type
        language: "en" for English, "ru" for Russian
        sequential: If True, add sequential execution instruction for multi-turn tests
        
    Returns:
        System prompt string
    """
    prompts = SYSTEM_PROMPTS_RU if language == "ru" else SYSTEM_PROMPTS
    base_prompt = prompts.get(format_type, prompts["openai"])
    
    if sequential:
        seq_instruction = SEQUENTIAL_INSTRUCTION_RU if language == "ru" else SEQUENTIAL_INSTRUCTION_EN
        return base_prompt + "\n" + seq_instruction
    
    return base_prompt
