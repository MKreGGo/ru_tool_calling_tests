"""
BFCL-V4 Test Cases.

25 test cases based on Berkeley Function Calling Leaderboard V4.
All tests have bilingual prompts (EN/RU).
"""

from tools.validator import ExpectedCalls, ExpectedCall
from tests.test_cases import TestCase


# =============================================================================
# BFCL LEVEL 1: BASIC (Tests 1-6)
# Simple tool calls with explicit parameters
# =============================================================================

BFCL_LEVEL_1 = [
    TestCase(
        id="BFCL-1.1",
        level=1,
        prompt_en="Calculate the area of a triangle with base 10 and height 5",
        prompt_ru="Вычислить площадь треугольника с основанием 10 и высотой 5",
        available_tools=["calculate_triangle_area"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(name="calculate_triangle_area", args={"base": 10, "height": 5})],
            mode="exact"
        ),
        description="Simple triangle area calculation",
        tags=["bfcl", "basic", "geometry"],
        source="bfcl"
    ),
    TestCase(
        id="BFCL-1.2",
        level=1,
        prompt_en="What is the factorial of 5?",
        prompt_ru="Чему равен факториал 5?",
        available_tools=["math_factorial"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(name="math_factorial", args={"n": 5})],
            mode="exact"
        ),
        description="Simple factorial calculation",
        tags=["bfcl", "basic", "math"],
        source="bfcl"
    ),
    TestCase(
        id="BFCL-1.3",
        level=1,
        prompt_en="Validate the email input field to ensure it's complete",
        prompt_ru="Проверить поле ввода email, убедиться что оно заполнено",
        available_tools=["validate_user_input"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(name="validate_user_input", args={"input_field": "email", "is_complete": True})],
            mode="exact"
        ),
        description="DOM input validation",
        tags=["bfcl", "basic", "validation"],
        source="bfcl"
    ),
    TestCase(
        id="BFCL-1.4",
        level=1,
        prompt_en="Find the hypotenuse of a right triangle with sides 3 and 4 meters",
        prompt_ru="Найти гипотенузу прямоугольного треугольника со сторонами 3 и 4 метра",
        available_tools=["math_hypot"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(name="math_hypot", args={"x": 3, "y": 4})],
            mode="exact"
        ),
        description="Hypotenuse calculation with type handling",
        tags=["bfcl", "basic", "geometry"],
        source="bfcl"
    ),
    TestCase(
        id="BFCL-1.5",
        level=1,
        prompt_en="Convert the string 'HELLO' to lowercase",
        prompt_ru="Преобразовать строку 'ПРИВЕТ' в нижний регистр",
        available_tools=["string_to_lowercase"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(name="string_to_lowercase", args={"text": "HELLO"})],
            mode="exact"
        ),
        expected_ru=ExpectedCalls(
            calls=[ExpectedCall(name="string_to_lowercase", args={"text": "ПРИВЕТ"})],
            mode="exact"
        ),
        description="String parameter extraction",
        tags=["bfcl", "basic", "string"],
        source="bfcl"
    ),
    TestCase(
        id="BFCL-1.6",
        level=1,
        prompt_en="Calculate the sum of first 10 even numbers starting from 2",
        prompt_ru="Вычислить сумму первых 10 четных чисел начиная с 2",
        available_tools=["sum_arithmetic_sequence"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(name="sum_arithmetic_sequence", args={"start": 2, "end": 20, "step": 2})],
            mode="exact"
        ),
        description="Optional parameters with defaults",
        tags=["bfcl", "basic", "math"],
        source="bfcl"
    ),
]

# =============================================================================
# BFCL LEVEL 2: INTERMEDIATE (Tests 7-14)
# Multiple calls, tool selection, live APIs
# =============================================================================

BFCL_LEVEL_2 = [
    TestCase(
        id="BFCL-2.1",
        level=2,
        prompt_en="Get the area of a circle with radius 5",
        prompt_ru="Найти площадь круга с радиусом 5",
        available_tools=["triangle_area", "circle_area", "rectangle_area"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(name="circle_area", args={"radius": 5})],
            mode="exact"
        ),
        description="Select correct tool from multiple geometry options",
        tags=["bfcl", "intermediate", "selection"],
        source="bfcl"
    ),
    TestCase(
        id="BFCL-2.2",
        level=2,
        prompt_en="Calculate resistance for copper and aluminum wires, both 100 meters long",
        prompt_ru="Рассчитать сопротивление медного и алюминиевого проводов, оба по 100 метров",
        available_tools=["calculate_resistance"],
        expected_en=ExpectedCalls(
            calls=[
                ExpectedCall(name="calculate_resistance", args={"material": "copper", "length": 100}),
                ExpectedCall(name="calculate_resistance", args={"material": "aluminum", "length": 100})
            ],
            mode="parallel"
        ),
        description="Parallel calls - same tool, different params",
        tags=["bfcl", "intermediate", "parallel", "physics"],
        source="bfcl"
    ),
    TestCase(
        id="BFCL-2.3",
        level=2,
        prompt_en="Calculate the area of both a circle with radius 5 and a rectangle with length 10 and width 3",
        prompt_ru="Вычислить площадь круга с радиусом 5 и прямоугольника 10x3",
        available_tools=["circle_area", "rectangle_area"],
        expected_en=ExpectedCalls(
            calls=[
                ExpectedCall(name="circle_area", args={"radius": 5}),
                ExpectedCall(name="rectangle_area", args={"length": 10, "width": 3})
            ],
            mode="parallel"
        ),
        description="Parallel calls - different tools",
        tags=["bfcl", "intermediate", "parallel", "geometry"],
        source="bfcl"
    ),
    TestCase(
        id="BFCL-2.4",
        level=2,
        prompt_en="What is the capital of France?",
        prompt_ru="Какая столица Франции?",
        available_tools=["bmi_calculator"],
        expected_en=ExpectedCalls(
            calls=[],
            mode="exact"
        ),
        description="Refusal test - no tool should be called",
        tags=["bfcl", "intermediate", "refusal"],
        source="bfcl"
    ),
    TestCase(
        id="BFCL-2.5",
        level=2,
        prompt_en="Get information about user with ID 7890",
        prompt_ru="Получить информацию о пользователе с ID 7890",
        available_tools=["get_user_info"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(name="get_user_info", args={"user_id": 7890})],
            mode="exact"
        ),
        description="Live API - user lookup",
        tags=["bfcl", "intermediate", "api"],
        source="bfcl"
    ),
    TestCase(
        id="BFCL-2.6",
        level=2,
        prompt_en="Book an Uber Comfort ride from downtown to airport",
        prompt_ru="Заказать поездку Uber Comfort из центра в аэропорт",
        available_tools=["uber_request_ride"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(name="uber_request_ride", args={
                "pickup_location": "downtown",
                "destination": "airport",
                "ride_type": "COMFORT"
            })],
            mode="exact"
        ),
        expected_ru=ExpectedCalls(
            calls=[ExpectedCall(name="uber_request_ride", args={
                "pickup_location": "центр",
                "destination": "аэропорт",
                "ride_type": "COMFORT"
            })],
            mode="exact"
        ),
        description="Live API with enum selection",
        tags=["bfcl", "intermediate", "api", "enum"],
        source="bfcl"
    ),
    TestCase(
        id="BFCL-2.7",
        level=2,
        prompt_en="What's the weather in Moscow and Saint Petersburg?",
        prompt_ru="Какая погода в Москве и Санкт-Петербурге?",
        available_tools=["weather_forecast"],
        expected_en=ExpectedCalls(
            calls=[
                ExpectedCall(name="weather_forecast", args={"city": "Moscow"}),
                ExpectedCall(name="weather_forecast", args={"city": "Saint Petersburg"})
            ],
            mode="parallel"
        ),
        expected_ru=ExpectedCalls(
            calls=[
                ExpectedCall(name="weather_forecast", args={"city": "Москва"}),
                ExpectedCall(name="weather_forecast", args={"city": "Санкт-Петербург"})
            ],
            mode="parallel"
        ),
        description="Live parallel - weather for multiple cities",
        tags=["bfcl", "intermediate", "parallel", "weather"],
        source="bfcl"
    ),
    TestCase(
        id="BFCL-2.8",
        level=2,
        prompt_en="I want to modify my coffee order - change the size to large",
        prompt_ru="Хочу изменить мой заказ кофе - поменять размер на большой",
        available_tools=["update_order_drink", "update_order_food", "update_order_payment"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(name="update_order_drink", args={"drink_size": "large"})],
            mode="exact"
        ),
        expected_ru=ExpectedCalls(
            calls=[ExpectedCall(name="update_order_drink", args={"drink_size": "большой"})],
            mode="exact"
        ),
        description="Tool selection among similar APIs",
        tags=["bfcl", "intermediate", "selection", "api"],
        source="bfcl"
    ),
]

# =============================================================================
# BFCL LEVEL 3: ADVANCED (Tests 15-19)
# Multi-turn, state persistence, robustness
# NOTE: All L3 tests (3.1-3.5) are now in bfcl_multi_turn_tests.py
# =============================================================================

BFCL_LEVEL_3 = []  # All L3 tests are multi-turn, see bfcl_multi_turn_tests.py

# =============================================================================
# BFCL LEVEL 4: EXPERT (Tests 20-25)
# Memory, web search, format sensitivity, constraints
# NOTE: 4.3 is now in bfcl_multi_turn_tests.py (3-turn web search)
# =============================================================================

BFCL_LEVEL_4 = [
    TestCase(
        id="BFCL-4.1",
        level=4,
        prompt_en="Remember that my name is Michael and I am 35 years old",
        prompt_ru="Запомни, что меня зовут Михаил и мне 35 лет",
        available_tools=["memory_store"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(name="memory_store", args={"key": "name", "value": "Michael"}),
                   ExpectedCall(name="memory_store", args={"key": "age", "value": 35})],
            mode="parallel"
        ),
        expected_ru=ExpectedCalls(
            calls=[ExpectedCall(name="memory_store", args={"key": "name", "value": "Михаил"}),
                   ExpectedCall(name="memory_store", args={"key": "age", "value": 35})],
            mode="parallel"
        ),
        description="Persistent memory - store customer profile",
        tags=["bfcl", "expert", "memory"],
        source="bfcl"
    ),
    TestCase(
        id="BFCL-4.2",
        level=4,
        prompt_en="What is my first name?",
        prompt_ru="Как моё имя?",
        available_tools=["memory_retrieve"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(name="memory_retrieve", args={"key": "name"})],
            mode="exact"
        ),
        description="Memory retrieval - temporal information",
        tags=["bfcl", "expert", "memory"],
        source="bfcl"
    ),
    # 4.3 moved to bfcl_multi_turn_tests.py (3-turn web search)
    TestCase(
        id="BFCL-4.4",
        level=4,
        prompt_en="Calculate perimeter of a circle with radius 5, area of rectangle 10x3, and sum of squares of 2 and 3",
        prompt_ru="Вычислить периметр круга с радиусом 5, площадь прямоугольника 10x3 и сумму квадратов 2 и 3",
        available_tools=["circle_perimeter", "rectangle_area", "sum_of_squares"],
        expected_en=ExpectedCalls(
            calls=[
                ExpectedCall(name="circle_perimeter", args={"radius": 5}),
                ExpectedCall(name="rectangle_area", args={"length": 10, "width": 3}),
                ExpectedCall(name="sum_of_squares", args={"a": 2, "b": 3})
            ],
            mode="parallel"
        ),
        description="Complex multi-tool coordination",
        tags=["bfcl", "expert", "parallel", "complex"],
        source="bfcl"
    ),
    TestCase(
        id="BFCL-4.5",
        level=4,
        prompt_en="Calculate area of circle with radius 5",
        prompt_ru="Вычислить площадь круга с радиусом 5",
        available_tools=["circle_area"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(name="circle_area", args={"radius": 5})],
            mode="exact",
            strict_format=True
        ),
        description="Format sensitivity test (same as basic but can test XML output)",
        tags=["bfcl", "expert", "format"],
        source="bfcl"
    ),
    TestCase(
        id="BFCL-4.6",
        level=4,
        prompt_en="Should I invest 1000 in asset A with 8% return and 3% risk? Only invest if return > 10% or risk < 5%. If you decide to invest, justify the reason by passing ONLY the winning parameter to execute_investment.",
        prompt_ru="Стоит ли инвестировать 1000 в актив A с доходностью 8% и риском 3%? Инвестировать только если доходность > 10% или риск < 5%. Если решишь инвестировать, обоснуй причину, передав ТОЛЬКО тот параметр, который обеспечил выполнение условия, в execute_investment.",
        available_tools=["analyze_investment", "execute_investment"],
        expected_en=ExpectedCalls(
            calls=[ExpectedCall(
                name="execute_investment", 
                args={"asset": "A", "amount": 1000, "risk_pct": 3},
                strict_args=True
            )],
            mode="exact"
        ),
        description="Complex reasoning with logical constraints and parameter-based justification",
        tags=["bfcl", "expert", "reasoning", "constraints"],
        source="bfcl"
    ),
]

# All BFCL single-turn tests combined
# L1: 6 tests (1.1-1.6)
# L2: 8 tests (2.1-2.8)
# L3: 0 tests (all in bfcl_multi_turn_tests.py)
# L4: 5 tests (4.1, 4.2, 4.4, 4.5, 4.6) - 4.3 is multi-turn
# Total single-turn: 19
# Multi-turn: 6 (3.1-3.5, 4.3)
# Grand total: 25
BFCL_TESTS = BFCL_LEVEL_1 + BFCL_LEVEL_2 + BFCL_LEVEL_3 + BFCL_LEVEL_4


