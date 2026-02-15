"""
실습 1: ReAct Agent (Tool Use + Planning)
==========================================
LLM이 도구를 사용하여 문제를 해결하는 기본 Agent 루프를 구현합니다.

소요 시간: ~15분
필요: pip install anthropic python-dotenv
"""

import json
import math
from datetime import datetime

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

# ============================================================
# 1단계: 도구 정의
# ============================================================
tools = [
    {
        "name": "calculator",
        "description": "수학 계산을 수행합니다. 사칙연산, 거듭제곱, 제곱근 등을 지원합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "계산할 수학 표현식 (예: '2 + 3 * 4', 'sqrt(16)', '2**10')",
                }
            },
            "required": ["expression"],
        },
    },
    {
        "name": "get_current_time",
        "description": "현재 날짜와 시간을 반환합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "시간대 (예: 'KST', 'UTC'). 기본값은 KST입니다.",
                }
            },
        },
    },
    {
        "name": "get_weather",
        "description": "도시의 현재 날씨를 조회합니다. (Mock 데이터)",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "도시명 (예: '서울', '부산', '제주')",
                }
            },
            "required": ["city"],
        },
    },
]

# ============================================================
# 2단계: 도구 실행 함수
# ============================================================
WEATHER_DATA = {
    "서울": {"temp": -2, "condition": "맑음", "humidity": 35},
    "부산": {"temp": 5, "condition": "흐림", "humidity": 60},
    "제주": {"temp": 8, "condition": "비", "humidity": 80},
    "대전": {"temp": 1, "condition": "눈", "humidity": 70},
}


def execute_tool(name: str, tool_input: dict) -> str:
    """도구를 실행하고 결과를 반환합니다."""
    print(f"  🔧 도구 실행: {name}({json.dumps(tool_input, ensure_ascii=False)})")

    if name == "calculator":
        expr = tool_input["expression"]
        # 안전한 수학 함수만 허용
        allowed = {"sqrt": math.sqrt, "abs": abs, "round": round, "pow": pow}
        try:
            result = eval(expr, {"__builtins__": {}, "math": math, **allowed})
            return f"계산 결과: {result}"
        except Exception as e:
            return f"계산 오류: {e}"

    elif name == "get_current_time":
        now = datetime.now()
        return f"현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')} (KST)"

    elif name == "get_weather":
        city = tool_input["city"]
        weather = WEATHER_DATA.get(city)
        if weather:
            return f"{city} 날씨: {weather['condition']}, 기온 {weather['temp']}°C, 습도 {weather['humidity']}%"
        return f"{city}의 날씨 정보를 찾을 수 없습니다. 지원 도시: {', '.join(WEATHER_DATA.keys())}"

    return f"알 수 없는 도구: {name}"


# ============================================================
# 3단계: Agent 루프 (핵심!)
# ============================================================
def run_agent(user_message: str, verbose: bool = True) -> str:
    """
    ReAct Agent 루프를 실행합니다.

    Plan → Act → Observe 를 반복하며,
    LLM이 도구 호출을 멈출 때까지 계속합니다.
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"🧑 사용자: {user_message}")
        print(f"{'='*60}")

    messages = [{"role": "user", "content": user_message}]
    turn = 0

    while True:
        turn += 1
        if verbose:
            print(f"\n--- Turn {turn} ---")

        # LLM 호출
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )

        if verbose:
            print(f"  📡 stop_reason: {response.stop_reason}")

        # 응답을 메시지에 추가
        messages.append({"role": "assistant", "content": response.content})

        # 텍스트 응답 출력
        for block in response.content:
            if block.type == "text" and block.text.strip():
                if verbose:
                    print(f"  💬 LLM: {block.text[:200]}")

        # 도구 호출이 없으면 종료
        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if not tool_uses:
            final_text = "\n".join(
                b.text for b in response.content if b.type == "text"
            )
            if verbose:
                print(f"\n{'='*60}")
                print(f"✅ 최종 답변:")
                print(f"{final_text}")
                print(f"{'='*60}")
                print(f"총 {turn}번의 턴으로 완료")
            return final_text

        # 도구 실행 & 결과 전달
        tool_results = []
        for tool_use in tool_uses:
            result = execute_tool(tool_use.name, tool_use.input)
            if verbose:
                print(f"  📋 결과: {result}")
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result,
                }
            )

        messages.append({"role": "user", "content": tool_results})


# ============================================================
# 실행
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  ReAct Agent 실습")
    print("  - 도구: calculator, get_weather, get_current_time")
    print("  - 'quit'을 입력하면 종료")
    print("=" * 60)

    # 예시 질문들
    examples = [
        "서울과 부산의 날씨를 비교해줘. 기온 차이도 계산해줘.",
        "지금 몇 시야? 그리고 제주 날씨 알려줘.",
        "2의 10승은 얼마야? 그리고 그 값의 제곱근은?",
    ]
    print("\n예시 질문:")
    for i, ex in enumerate(examples, 1):
        print(f"  {i}. {ex}")
    print()

    while True:
        user_input = input("🧑 질문 입력 (또는 예시 번호 1-3): ").strip()
        if user_input.lower() == "quit":
            break
        if user_input in ("1", "2", "3"):
            user_input = examples[int(user_input) - 1]
        if user_input:
            run_agent(user_input)
