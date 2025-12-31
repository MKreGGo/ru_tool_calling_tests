"""
BFCL-V4 specific tools.

Tools required for BFCL-V4 benchmark tests. These extend the base tool registry.
"""

from typing import Any

# BFCL Tool Schemas
BFCL_TOOL_SCHEMAS = {
    # ==========================================================================
    # GEOMETRY TOOLS
    # ==========================================================================
    "calculate_triangle_area": {
        "name": "calculate_triangle_area",
        "description": "Calculate the area of a triangle given base and height",
        "description_ru": "Вычислить площадь треугольника по основанию и высоте",
        "parameters": {
            "type": "object",
            "properties": {
                "base": {
                    "type": "number",
                    "description": "The base length of the triangle",
                    "description_ru": "Длина основания треугольника"
                },
                "height": {
                    "type": "number",
                    "description": "The height of the triangle",
                    "description_ru": "Высота треугольника"
                },
                "unit": {
                    "type": "string",
                    "description": "Unit of measurement (default: m²)",
                    "description_ru": "Единица измерения (по умолчанию: м²)",
                    "default": "m²"
                }
            },
            "required": ["base", "height"]
        }
    },
    "triangle_area": {
        "name": "triangle_area",
        "description": "Calculate triangle area from base and height",
        "description_ru": "Вычислить площадь треугольника по основанию и высоте",
        "parameters": {
            "type": "object",
            "properties": {
                "base": {"type": "number", "description": "Base length", "description_ru": "Длина основания"},
                "height": {"type": "number", "description": "Height", "description_ru": "Высота"}
            },
            "required": ["base", "height"]
        }
    },
    "circle_area": {
        "name": "circle_area",
        "description": "Calculate the area of a circle given radius",
        "description_ru": "Вычислить площадь круга по радиусу",
        "parameters": {
            "type": "object",
            "properties": {
                "radius": {
                    "type": "number",
                    "description": "The radius of the circle",
                    "description_ru": "Радиус круга"
                }
            },
            "required": ["radius"]
        }
    },
    "circle_perimeter": {
        "name": "circle_perimeter",
        "description": "Calculate the perimeter (circumference) of a circle",
        "description_ru": "Вычислить периметр (длину окружности) круга",
        "parameters": {
            "type": "object",
            "properties": {
                "radius": {
                    "type": "number",
                    "description": "The radius of the circle",
                    "description_ru": "Радиус круга"
                }
            },
            "required": ["radius"]
        }
    },
    "rectangle_area": {
        "name": "rectangle_area",
        "description": "Calculate the area of a rectangle given length and width",
        "description_ru": "Вычислить площадь прямоугольника по длине и ширине",
        "parameters": {
            "type": "object",
            "properties": {
                "length": {"type": "number", "description": "Length of the rectangle", "description_ru": "Длина прямоугольника"},
                "width": {"type": "number", "description": "Width of the rectangle", "description_ru": "Ширина прямоугольника"}
            },
            "required": ["length", "width"]
        }
    },
    
    # ==========================================================================
    # MATH TOOLS
    # ==========================================================================
    "math_factorial": {
        "name": "math_factorial",
        "description": "Calculate the factorial of a number",
        "description_ru": "Вычислить факториал числа",
        "parameters": {
            "type": "object",
            "properties": {
                "n": {
                    "type": "integer",
                    "description": "The number to calculate factorial for",
                    "description_ru": "Число для вычисления факториала"
                }
            },
            "required": ["n"]
        }
    },
    "math_hypot": {
        "name": "math_hypot",
        "description": "Calculate the hypotenuse of a right triangle",
        "description_ru": "Вычислить гипотенузу прямоугольного треугольника",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "number", "description": "First side length", "description_ru": "Длина первого катета"},
                "y": {"type": "number", "description": "Second side length", "description_ru": "Длина второго катета"},
                "z": {"type": "number", "description": "Optional third dimension", "description_ru": "Необязательное третье измерение"}
            },
            "required": ["x", "y"]
        }
    },
    "sum_arithmetic_sequence": {
        "name": "sum_arithmetic_sequence",
        "description": "Calculate the sum of an arithmetic sequence",
        "description_ru": "Вычислить сумму арифметической последовательности",
        "parameters": {
            "type": "object",
            "properties": {
                "start": {"type": "integer", "description": "Starting value", "description_ru": "Начальное значение"},
                "end": {"type": "integer", "description": "Ending value", "description_ru": "Конечное значение"},
                "step": {"type": "integer", "description": "Step between values", "description_ru": "Шаг между значениями", "default": 1}
            },
            "required": ["start", "end"]
        }
    },
    "sum_of_squares": {
        "name": "sum_of_squares",
        "description": "Calculate the sum of squares of two numbers",
        "description_ru": "Вычислить сумму квадратов двух чисел",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number", "description_ru": "Первое число"},
                "b": {"type": "number", "description": "Second number", "description_ru": "Второе число"}
            },
            "required": ["a", "b"]
        }
    },
    
    # ==========================================================================
    # STRING TOOLS
    # ==========================================================================
    "string_to_lowercase": {
        "name": "string_to_lowercase",
        "description": "Convert a string to lowercase",
        "description_ru": "Преобразовать строку в нижний регистр",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to convert", "description_ru": "Текст для преобразования"},
                "preserve_numbers": {"type": "boolean", "default": False}
            },
            "required": ["text"]
        }
    },
    "validate_user_input": {
        "name": "validate_user_input",
        "description": "Validate a user input field",
        "description_ru": "Проверить поле ввода пользователя",
        "parameters": {
            "type": "object",
            "properties": {
                "input_field": {"type": "string", "description": "Name of the input field", "description_ru": "Название поля ввода"},
                "is_complete": {"type": "boolean", "description": "Whether input is complete", "description_ru": "Заполнено ли поле полностью"}
            },
            "required": ["input_field", "is_complete"]
        }
    },
    
    # ==========================================================================
    # PHYSICS TOOLS
    # ==========================================================================
    "calculate_resistance": {
        "name": "calculate_resistance",
        "description": "Calculate electrical resistance of a wire",
        "description_ru": "Рассчитать электрическое сопротивление провода",
        "parameters": {
            "type": "object",
            "properties": {
                "material": {
                    "type": "string",
                    "enum": ["copper", "aluminum", "steel"],
                    "description": "Wire material",
                    "description_ru": "Материал провода"
                },
                "length": {"type": "number", "description": "Wire length in meters", "description_ru": "Длина провода в метрах"}
            },
            "required": ["material", "length"]
        }
    },
    
    # ==========================================================================
    # API TOOLS
    # ==========================================================================
    "get_user_info": {
        "name": "get_user_info",
        "description": "Get information about a user by ID",
        "description_ru": "Получить информацию о пользователе по ID",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "User ID", "description_ru": "ID пользователя"},
                "include_history": {"type": "boolean", "default": False}
            },
            "required": ["user_id"]
        }
    },
    "uber_request_ride": {
        "name": "uber_request_ride",
        "description": "Request a ride through Uber",
        "description_ru": "Заказать поездку через Uber",
        "parameters": {
            "type": "object",
            "properties": {
                "pickup_location": {"type": "string", "description": "Pickup location", "description_ru": "Место посадки"},
                "destination": {"type": "string", "description": "Destination", "description_ru": "Пункт назначения"},
                "ride_type": {
                    "type": "string",
                    "enum": ["COMFORT", "COMFORT_XL", "UBER_X"],
                    "description": "Type of ride",
                    "description_ru": "Тип поездки"
                },
                "surge_multiplier": {"type": "number", "default": 1.0}
            },
            "required": ["pickup_location", "destination", "ride_type"]
        }
    },
    "weather_forecast": {
        "name": "weather_forecast",
        "description": "Get weather forecast for a city",
        "description_ru": "Получить прогноз погоды для города",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name", "description_ru": "Название города"},
                "units": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "default": "celsius"
                }
            },
            "required": ["city"]
        }
    },
    "bmi_calculator": {
        "name": "bmi_calculator",
        "description": "Calculate Body Mass Index",
        "description_ru": "Рассчитать индекс массы тела",
        "parameters": {
            "type": "object",
            "properties": {
                "weight": {"type": "number", "description": "Weight in kg", "description_ru": "Вес в кг"},
                "height": {"type": "number", "description": "Height in meters", "description_ru": "Рост в метрах"}
            },
            "required": ["weight", "height"]
        }
    },
    
    # ==========================================================================
    # ORDER MANAGEMENT TOOLS
    # ==========================================================================
    "update_order_drink": {
        "name": "update_order_drink",
        "description": "Update drink details in an order",
        "description_ru": "Обновить данные напитка в заказе",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID", "description_ru": "ID заказа"},
                "drink_size": {"type": "string", "description": "New drink size", "description_ru": "Новый размер напитка"}
            },
            "required": ["drink_size"]
        }
    },
    "update_order_food": {
        "name": "update_order_food",
        "description": "Update food item in an order",
        "description_ru": "Обновить блюдо в заказе",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description_ru": "ID заказа"},
                "food_item": {"type": "string", "description_ru": "Название блюда"}
            },
            "required": ["order_id", "food_item"]
        }
    },
    "update_order_payment": {
        "name": "update_order_payment",
        "description": "Update payment method for an order",
        "description_ru": "Обновить способ оплаты заказа",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description_ru": "ID заказа"},
                "payment_method": {"type": "string", "description_ru": "Способ оплаты"}
            },
            "required": ["order_id", "payment_method"]
        }
    },
    
    # ==========================================================================
    # FILE SYSTEM TOOLS
    # ==========================================================================
    "file_copy": {
        "name": "file_copy",
        "description": "Copy a file from source to destination. Use this for creating backups or duplicating files. Creates an exact copy of the file at a new location.",
        "description_ru": "Скопировать файл из источника в место назначения. Используй для создания резервных копий или дублирования файлов.",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Source file path", "description_ru": "Путь исходного файла"},
                "destination": {"type": "string", "description": "Destination path for the copy", "description_ru": "Путь назначения для копии"}
            },
            "required": ["source", "destination"]
        }
    },
    "list_directory": {
        "name": "list_directory",
        "description": "List files in a directory",
        "description_ru": "Показать файлы в директории",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path", "description_ru": "Путь к директории"}
            },
            "required": ["path"]
        }
    },
    "file_archive": {
        "name": "file_archive",
        "description": "Compress and archive a file into a compressed format (zip/tar). Use this for compressing files, NOT for simple backups.",
        "description_ru": "Сжать и архивировать файл в сжатый формат (zip/tar). Используй для сжатия файлов, НЕ для простых резервных копий.",
        "parameters": {
            "type": "object",
            "properties": {
                "file": {"type": "string", "description": "File to compress and archive", "description_ru": "Файл для сжатия и архивации"}
            },
            "required": ["file"]
        }
    },
    "find_files": {
        "name": "find_files",
        "description": "Find files matching a pattern",
        "description_ru": "Найти файлы по шаблону",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "File pattern (glob)", "description_ru": "Шаблон файлов (glob)"}
            },
            "required": ["pattern"]
        }
    },
    "delete_files": {
        "name": "delete_files",
        "description": "Delete files matching pattern",
        "description_ru": "Удалить файлы по шаблону",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description_ru": "Шаблон файлов"}
            },
            "required": ["pattern"]
        }
    },
    "archive_files": {
        "name": "archive_files",
        "description": "Archive files matching pattern",
        "description_ru": "Архивировать файлы по шаблону",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description_ru": "Шаблон файлов"},
                "destination": {"type": "string", "description_ru": "Путь назначения"}
            },
            "required": ["pattern"]
        }
    },
    "move_file": {
        "name": "move_file",
        "description": "Move a file to a new location",
        "description_ru": "Переместить файл в новое место",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Source file path", "description_ru": "Путь исходного файла"},
                "destination": {"type": "string", "description": "Destination path", "description_ru": "Путь назначения"}
            },
            "required": ["source", "destination"]
        }
    },
    
    # ==========================================================================
    # TICKET MANAGEMENT TOOLS
    # ==========================================================================
    "create_ticket": {
        "name": "create_ticket",
        "description": "Create a support ticket",
        "description_ru": "Создать тикет поддержки",
        "parameters": {
            "type": "object",
            "properties": {
                "issue": {"type": "string", "description": "Issue description", "description_ru": "Описание проблемы"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"], "description_ru": "Приоритет"}
            },
            "required": ["issue"]
        }
    },
    "assign_ticket": {
        "name": "assign_ticket",
        "description": "Assign a ticket to someone",
        "description_ru": "Назначить тикет кому-либо",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string", "description_ru": "ID тикета"},
                "assignee": {"type": "string", "description_ru": "Ответственный"}
            },
            "required": ["ticket_id", "assignee"]
        }
    },
    "update_priority": {
        "name": "update_priority",
        "description": "Update ticket priority",
        "description_ru": "Обновить приоритет тикета",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string", "description_ru": "ID тикета"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"], "description_ru": "Приоритет"}
            },
            "required": ["ticket_id", "priority"]
        }
    },
    
    # ==========================================================================
    # MEMORY TOOLS
    # ==========================================================================
    "memory_store": {
        "name": "memory_store",
        "description": "Store a value in agent memory",
        "description_ru": "Сохранить значение в памяти агента",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Memory key", "description_ru": "Ключ памяти"},
                "value": {"type": ["string", "number", "boolean"], "description": "Value to store. Pass numbers as numeric types, not strings.", "description_ru": "Значение для сохранения. Передавай числа как числовые типы, не строки."}
            },
            "required": ["key", "value"]
        }
    },
    "memory_retrieve": {
        "name": "memory_retrieve",
        "description": "Retrieve a value from agent memory",
        "description_ru": "Получить значение из памяти агента",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Memory key to retrieve", "description_ru": "Ключ памяти для получения"}
            },
            "required": ["key"]
        }
    },
    
    # ==========================================================================
    # WEB TOOLS
    # ==========================================================================
    "web_search": {
        "name": "web_search",
        "description": "Search the web for information",
        "description_ru": "Искать информацию в интернете",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query", "description_ru": "Поисковый запрос"}
            },
            "required": ["query"]
        }
    },
    "get_webpage": {
        "name": "get_webpage",
        "description": "Fetch content from a URL",
        "description_ru": "Получить содержимое веб-страницы по URL",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch", "description_ru": "URL для получения"}
            },
            "required": ["url"]
        }
    },
    "web_fetch": {
        "name": "web_fetch",
        "description": "Fetch content from a URL",
        "description_ru": "Получить содержимое URL",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch", "description_ru": "URL для получения"}
            },
            "required": ["url"]
        }
    },
    
    # ==========================================================================
    # INVESTMENT TOOLS
    # ==========================================================================
    "analyze_investment": {
        "name": "analyze_investment",
        "description": "Analyze an investment opportunity",
        "description_ru": "Анализировать инвестиционную возможность",
        "parameters": {
            "type": "object",
            "properties": {
                "asset": {"type": "string", "description": "Asset identifier", "description_ru": "Идентификатор актива"},
                "return_pct": {"type": "number", "description": "Expected return percentage", "description_ru": "Ожидаемая доходность в процентах"},
                "risk_pct": {"type": "number", "description": "Risk percentage", "description_ru": "Риск в процентах"}
            },
            "required": ["asset", "return_pct", "risk_pct"]
        }
    },
    "execute_investment": {
        "name": "execute_investment",
        "description": "Execute an investment. If the decision is based on a specific threshold (e.g. risk or return), include ONLY that parameter to justify it.",
        "description_ru": "Выполнить инвестицию. Если решение основано на конкретном пороге (напр. риск или доходность), включи ТОЛЬКО тот параметр для обоснования.",
        "parameters": {
            "type": "object",
            "properties": {
                "asset": {"type": "string", "description": "Asset identifier", "description_ru": "Идентификатор актива"},
                "amount": {"type": "number", "description": "Amount to invest", "description_ru": "Сумма инвестиции"},
                "return_pct": {"type": "number", "description": "Include this if return > 10%", "description_ru": "Включи, если доходность > 10%"},
                "risk_pct": {"type": "number", "description": "Include this if risk < 5%", "description_ru": "Включи, если риск < 5%"}
            },
            "required": ["asset", "amount"]
        }
    },
}


def get_bfcl_tool_schema(tool_name: str) -> dict[str, Any] | None:
    """Get schema for a BFCL tool by name."""
    return BFCL_TOOL_SCHEMAS.get(tool_name)


def get_all_bfcl_tools() -> list[str]:
    """Get list of all BFCL tool names."""
    return list(BFCL_TOOL_SCHEMAS.keys())
