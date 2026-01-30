#!/usr/bin/env python3
"""
Section 4 실습: Raw Function Calling 구현과 MCP로의 연결

이 코드는 라이브러리 없이 직접 구현한 Function Calling 에이전트입니다.
에이전트의 심장인 While 루프와 JSON Schema 설계를 직접 체험할 수 있습니다.
"""

import json
import os
from typing import Dict, List, Any, Callable
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Gemini API 클라이언트 초기화
gemini_api_key = os.getenv("GEMINI_API_KEY")
client = OpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai"
)

# ============================================================================
# [1단계: Schema Design - 모델이 읽는 매뉴얼]
# ============================================================================

def get_stock_price(symbol: str) -> Dict[str, Any]:
    """주식 가격을 조회하는 함수 (시뮬레이션)"""
    stock_data = {
        "AAPL": {"name": "Apple Inc.", "price": 175.50, "change": 2.3},
        "005930": {"name": "삼성전자", "price": 75000, "change": -1.2},
        "TSLA": {"name": "Tesla Inc.", "price": 245.80, "change": 5.1},
    }
    
    return stock_data.get(symbol.upper(), {
        "name": f"Unknown ({symbol})",
        "price": 0,
        "change": 0
    })


def get_weather(location: str, units: str = "metric") -> Dict[str, Any]:
    """날씨 정보를 조회하는 함수 (시뮬레이션)"""
    weather_data = {
        "seoul": {"temp": 15, "condition": "맑음", "humidity": 65},
        "tokyo": {"temp": 18, "condition": "구름 조금", "humidity": 70},
        "new york": {"temp": 12, "condition": "가벼운 비", "humidity": 80},
    }
    
    data = weather_data.get(location.lower(), {
        "temp": 20,
        "condition": "알 수 없음",
        "humidity": 60
    })
    
    if units == "imperial":
        data["temp"] = data["temp"] * 9 / 5 + 32
        data["unit"] = "°F"
    else:
        data["unit"] = "°C"
    
    return data


def calculate(expression: str) -> Dict[str, Any]:
    """수식을 계산하는 함수"""
    try:
        result = eval(expression)
        return {"result": result, "expression": expression}
    except Exception as e:
        return {"error": str(e), "expression": expression}


# 함수 레지스트리
FUNCTIONS: Dict[str, Callable] = {
    "get_stock_price": get_stock_price,
    "get_weather": get_weather,
    "calculate": calculate,
}

# JSON Schema 정의 - description 필드가 Semantic Matching의 핵심
FUNCTIONS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "주식의 현재 가격과 변동률을 조회합니다. 삼성전자, 애플, 테슬라 등의 주가를 확인할 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "주식 심볼 코드 (예: 'AAPL'은 애플, '005930'은 삼성전자, 'TSLA'는 테슬라)"
                    }
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "특정 도시의 현재 날씨 정보를 조회합니다. 온도, 날씨 상태, 습도를 확인할 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "도시 이름 (예: 'Seoul', 'Tokyo', 'New York')"
                    },
                    "units": {
                        "type": "string",
                        "enum": ["metric", "imperial"],
                        "description": "온도 단위: 'metric'은 섭씨, 'imperial'은 화씨",
                        "default": "metric"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "수학적 계산을 수행합니다. 덧셈, 뺄셈, 곱셈, 나눗셈 등의 연산을 할 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "계산할 수식 (예: '2 + 2', '10 * 5', '100 / 4')"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]


# ============================================================================
# [2단계: The Loop - 에이전트를 움직이는 심장]
# ============================================================================

def execute_function(function_name: str, arguments: Dict[str, Any]) -> str:
    """함수를 실행하고 결과를 JSON 문자열로 반환"""
    if function_name not in FUNCTIONS:
        return json.dumps({"error": f"Unknown function: {function_name}"})
    
    try:
        func = FUNCTIONS[function_name]
        result = func(**arguments)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


def run_agent(user_query: str, model: str = "gemini-flash-latest") -> str:
    """
    에이전트의 메인 루프 - ReAct 패턴 구현
    
    ═══════════════════════════════════════════════════════════════
    [2단계: The Loop - 에이전트를 움직이는 심장]
    ═══════════════════════════════════════════════════════════════
    
    이 루프는 모델이 Final Answer를 반환할 때까지 반복됩니다:
    
    1. Thought (추론): 모델이 현재 상황을 분석하고 다음 행동을 계획
    2. Action (행동): tool_calls를 통해 함수를 실제로 호출
    3. Observation (관찰): 함수 실행 결과를 확인하고 목표 달성 여부 판단
    
    이 과정이 반복되면서 에이전트는 단순한 답변기가 아니라,
    문제를 해결해 나가는 지능적인 주체로 거듭나게 됩니다.
    
    Args:
        user_query: 사용자의 질문
        model: 사용할 Gemini 모델 (예: "gemini-1.5-flash", "gemini-1.5-pro")
    
    Returns:
        최종 답변
    """
    messages = [
        {
            "role": "system",
            "content": """당신은 유용한 AI 어시스턴트입니다. 
사용자의 질문에 답하기 위해 필요한 도구를 사용할 수 있습니다.
함수 실행 결과를 관찰한 후, 사용자에게 명확하고 도움이 되는 답변을 제공하세요."""
        },
        {
            "role": "user",
            "content": user_query
        }
    ]
    
    max_iterations = 10  # 무한 루프 방지
    iteration = 0
    
    print(f"\n{'='*60}")
    print(f"🤖 에이전트 시작: {user_query}")
    print(f"{'='*60}\n")
    
    while iteration < max_iterations:
        iteration += 1
        print(f"[반복 {iteration}] 모델에게 요청 전송...")
        
        # ──────────────────────────────────────────────────────────
        # [Step 1: Thought] 모델이 다음 행동을 계획
        # ──────────────────────────────────────────────────────────
        # 모델에게 요청 전송 - 모델은 현재 상황을 분석하고
        # 필요한 도구를 선택할지, 아니면 최종 답변을 할지 결정합니다
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=FUNCTIONS_SCHEMA,  # 사용 가능한 도구 목록 제공
            tool_choice="auto"  # 모델이 자동으로 도구 사용 결정
        )
        
        # 응답 확인
        assistant_message = response.choices[0].message
        messages.append({
            "role": "assistant",
            "content": assistant_message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in (assistant_message.tool_calls or [])
            ]
        })
        
        # ──────────────────────────────────────────────────────────
        # [Final Answer 체크] 모델이 일반 텍스트로 답변한 경우
        # ──────────────────────────────────────────────────────────
        if not assistant_message.tool_calls:
            print(f"\n✅ 최종 답변 도달!")
            print(f"{'='*60}")
            return assistant_message.content or "답변을 생성할 수 없습니다."
        
        # ──────────────────────────────────────────────────────────
        # [Step 2: Action] tool_calls가 있는 경우 - 함수 실행
        # ──────────────────────────────────────────────────────────
        # 모델이 '이 함수를 호출해야겠다'고 결정한 경우
        print(f"🔧 도구 호출 감지: {len(assistant_message.tool_calls)}개")
        
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            print(f"  → 함수: {function_name}")
            print(f"  → 인자: {function_args}")
            
            # 실제 함수 실행 (우리가 작성한 Python 코드 실행)
            function_result = execute_function(function_name, function_args)
            
            print(f"  → 결과: {function_result[:100]}...")
            
            # ──────────────────────────────────────────────────────────
            # [Step 3: Observation] 결과 피드백을 모델에게 전달
            # ──────────────────────────────────────────────────────────
            # 함수 실행 결과를 다시 모델에게 던져줍니다
            # 모델은 이 결과를 보고 다음 행동을 결정합니다
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": function_result
            })
        
        print()
    
    # 최대 반복 횟수 초과
    return "최대 반복 횟수를 초과했습니다. 에이전트가 답변을 찾지 못했습니다."


# ============================================================================
# [3단계: MCP로의 연결 - 표준화의 필요성]
# ============================================================================
# 
# 이 실습에서는 함수 명세를 직접 딕셔너리로 작성했습니다.
# 하지만 모델이 바뀌거나 도구가 많아지면 매번 Schema를 새로 짜는 것은 비효율적입니다.
# 
# MCP (Model Context Protocol)는 에이전트와 도구를 '플러그 앤 플레이' 방식으로
# 연결할 수 있도록 하는 표준 규격입니다.
# 
# ============================================================================

if __name__ == "__main__":
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key or gemini_api_key == "your-gemini-api-key-here":
        print("❌ 오류: GEMINI_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일을 열어서 GEMINI_API_KEY를 본인의 Gemini API 키로 변경하세요.")
        print("   Gemini API 키는 https://aistudio.google.com/app/apikey 에서 무료로 발급받을 수 있습니다.")
        exit(1)
    
    print("\n" + "="*60)
    print("🎯 Raw Function Calling 에이전트 실습")
    print("="*60)
    print("\n이 예제는 라이브러리 없이 직접 구현한 Function Calling입니다.")
    print("에이전트의 심장인 While 루프와 JSON Schema를 직접 체험해보세요!\n")
    
    examples = [
        "오늘 삼성전자 주가가 얼마야?",
        "서울과 도쿄의 날씨를 비교해줘",
        "애플 주가에 10을 곱한 값이 얼마야?",
    ]
    
    print("📝 예제 질문:")
    for i, q in enumerate(examples, 1):
        print(f"  {i}. {q}")
    
    print("\n" + "-"*60)
    
    # 첫 번째 예제 실행
    query = examples[0]
    result = run_agent(query)
    
    print(f"\n💬 최종 답변:\n{result}\n")
    
    # 사용자 입력 받기
    print("\n" + "-"*60)
    print("직접 질문을 입력해보세요! (종료: Ctrl+C 또는 빈 입력)")
    print("-"*60 + "\n")
    
    try:
        while True:
            user_input = input("질문: ").strip()
            if not user_input:
                break
            
            result = run_agent(user_input)
            print(f"\n💬 최종 답변:\n{result}\n")
            print("-"*60 + "\n")
    except KeyboardInterrupt:
        print("\n\n👋 에이전트를 종료합니다.")
