# 04. 실습 가이드

---

## 실습 개요

> 이론에서 배운 Agentic Workflow와 SDLC 개념을 직접 체험

### 실습 목표

1. Agentic 패턴이 실제로 어떻게 동작하는지 이해
2. AI Agent가 SDLC에 어떻게 참여하는지 체험
3. Agent를 직접 구축하는 기본 방법 습득

---

## Agentic 프레임워크 비교

> 실습에 앞서, 주요 프레임워크를 간략히 비교

### 종합 비교표

| 기준          | LangGraph       | CrewAI    | AutoGen   | Agents SDK   |
| ------------- | --------------- | --------- | --------- | ------------ |
| **패러다임**  | 그래프/상태머신 | 역할 기반 | 대화 기반 | Handoff 기반 |
| **학습 곡선** | 높음            | 낮음      | 중간      | 낮음         |
| **유연성**    | 매우 높음       | 중간      | 높음      | 중간         |
| **프로덕션**  | 적합            | 제한적    | 제한적    | 적합         |
| **LLM 지원**  | 다양            | 다양      | 다양      | OpenAI 중심  |
| **디버깅**    | 우수            | 보통      | 보통      | 우수         |

### 선택 가이드

```mermaid
flowchart TD
    Q1{"빠른 프로토타이핑?"} -->|Yes| CrewAI
    Q1 -->|No| Q2{"복잡한 워크플로우<br/>제어 필요?"}
    Q2 -->|Yes| LangGraph
    Q2 -->|No| Q3{"코드 생성/실행이<br/>핵심?"}
    Q3 -->|Yes| AutoGen
    Q3 -->|No| Q4{"OpenAI 생태계?"}
    Q4 -->|Yes| AgentsSDK["Agents SDK"]
    Q4 -->|No| ClaudeCode["Claude Code + MCP"]
```

### "프레임워크 없이 구축하기" - Anthropic의 권장

> 프레임워크가 항상 필요한 것은 아님.
> 간단한 에이전트는 **LLM API + 도구 호출 루프**로 충분.

| 프레임워크가 필요한 경우   | 프레임워크가 불필요한 경우      |
| -------------------------- | ------------------------------- |
| 복잡한 멀티에이전트 시스템 | 단일 에이전트, 간단한 도구 호출 |
| 상태 관리/체크포인트 중요  | 프로토타이핑 단계               |
| 프로덕션급 모니터링/디버깅 | 커스텀 제어가 중요한 경우       |
| 팀 단위 개발               |                                 |

---

## 실습 환경 설정

### 필요한 패키지

```bash
# 기본 패키지
pip install anthropic openai

# 실습 도구
pip install fastapi uvicorn pytest httpx
```

### 환경 변수

```bash
# .env 파일
ANTHROPIC_API_KEY=your-api-key-here
```

---

## 실습 1: 기본 Agent 루프 구현 (ReAct 패턴)

> LLM API + Tool 호출 루프를 직접 구현하여 Plan → Act → Observe 순환을 체험

### 구현할 Agent 흐름

```mermaid
flowchart TD
    Q["사용자 질문"] --> LLM["LLM 추론"]
    LLM -->|"도구 사용 필요"| Tool["도구 실행<br/>calculator, search 등"]
    Tool --> Observe["결과 관찰<br/>결과를 LLM에 전달"]
    Observe --> LLM
    LLM -->|"최종 답변"| Answer["답변 반환"]
```

### 핵심 코드

```python
# 실습 1: 기본 ReAct Agent

import anthropic

client = anthropic.Anthropic()

# 도구 정의
tools = [
    {
        "name": "calculator",
        "description": "수학 계산을 수행합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "계산할 수학 표현식"
                }
            },
            "required": ["expression"]
        }
    },
    {
        "name": "get_weather",
        "description": "도시의 현재 날씨를 조회합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "도시명"
                }
            },
            "required": ["city"]
        }
    }
]

# 도구 실행 함수
def execute_tool(name, input_data):
    if name == "calculator":
        return str(eval(input_data["expression"]))
    elif name == "get_weather":
        # Mock 데이터
        return f"{input_data['city']}: 맑음, 5°C"

# Agent 루프
def run_agent(user_message):
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )

        # 응답을 메시지에 추가
        messages.append({
            "role": "assistant",
            "content": response.content
        })

        # 도구 호출이 있는지 확인
        tool_calls = [
            block for block in response.content
            if block.type == "tool_use"
        ]

        if not tool_calls:
            # 최종 답변
            final = [
                block.text for block in response.content
                if block.type == "text"
            ]
            return "\n".join(final)

        # 도구 실행 결과를 메시지에 추가
        tool_results = []
        for tool_call in tool_calls:
            result = execute_tool(
                tool_call.name,
                tool_call.input
            )
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_call.id,
                "content": result
            })

        messages.append({
            "role": "user",
            "content": tool_results
        })

# 실행
answer = run_agent(
    "서울 날씨를 알려주고, 기온에 10을 곱하면 얼마인지 계산해줘"
)
print(answer)
```

### 실습 포인트

- `while True` 루프가 Agent의 **반복적 동작**을 구현
- `stop_reason`이 `tool_use`이면 도구 실행 후 계속
- 도구 결과를 다시 LLM에 전달하는 것이 핵심

---

## 실습 2: Reflection 패턴 구현

> Generator + Evaluator 구조로 반복적 품질 개선 체험

### 구현할 흐름

```mermaid
flowchart TD
    Gen["Generator<br/>코드/글 생성"] --> Eval["Evaluator<br/>품질 평가 (점수 + 피드백)"]
    Eval -->|"점수 >= 8"| Done["완료"]
    Eval -->|"점수 < 8"| Gen
```

### 핵심 코드

```python
# 실습 2: Reflection Agent

def generate(task, feedback=None):
    prompt = f"다음 작업을 수행해주세요: {task}"
    if feedback:
        prompt += f"\n\n이전 피드백을 반영해주세요:\n{feedback}"

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

def evaluate(task, result):
    prompt = f"""다음 작업 결과를 평가해주세요.

작업: {task}
결과:
{result}

JSON으로 응답해주세요:
{{"score": 1-10, "feedback": "개선 사항"}}"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return json.loads(response.content[0].text)

def reflection_agent(task, max_iterations=3, threshold=8):
    result = generate(task)

    for i in range(max_iterations):
        evaluation = evaluate(task, result)
        print(f"반복 {i+1}: 점수 {evaluation['score']}/10")

        if evaluation["score"] >= threshold:
            print("품질 기준 충족!")
            return result

        result = generate(task, evaluation["feedback"])

    return result
```

---

## 실습 3: Claude Code로 Agentic SDLC 체험

> 실제 AI Agent 도구로 SDLC 단계를 수행

### 실습 시나리오

```mermaid
flowchart LR
    Req["Step 1: 요구사항<br/>자연어로 요청"] --> Design["Step 2: 설계<br/>Agent가 구조 제안"]
    Design --> Impl["Step 3: 구현<br/>Agent가 코드 작성"]
    Impl --> Test["Step 4: 테스트<br/>Agent가 테스트 작성/실행"]
    Test --> Review["Step 5: 리뷰<br/>Agent가 코드 리뷰/개선"]
```

### Claude Code 사용 예시

```bash
# Claude Code 실행
$ claude

# 1. 요구사항 전달
> FastAPI로 TODO CRUD API를 만들어줘.
  SQLite를 사용하고 테스트도 작성해줘.

# Agent가 자율적으로:
# - 프로젝트 구조 설계
# - 코드 작성 (models, routes, schemas)
# - 테스트 작성
# - 실행 및 검증
# - 필요시 수정
```

### 관찰 포인트

- Agent가 어떤 순서로 작업하는가?
- 어떤 도구를 사용하는가?
- 에러 발생 시 어떻게 대응하는가?
- 코드 품질은 어떠한가?
- 사람의 개입이 필요한 순간은?

---

## 실습 체크리스트

### 실습 1: 기본 Agent 루프

- [ ] Tool 정의 및 등록
- [ ] Agent 루프 구현 (Plan-Act-Observe)
- [ ] 멀티턴 대화 동작 확인
- [ ] 다양한 질문으로 테스트

### 실습 2: Reflection 패턴

- [ ] Generator 구현
- [ ] Evaluator 구현
- [ ] 반복 개선 루프 동작 확인
- [ ] 반복 횟수에 따른 품질 변화 관찰

### 실습 3: Agentic SDLC (Claude Code)

- [ ] Claude Code로 프로젝트 생성
- [ ] Agent의 SDLC 단계별 행동 관찰
- [ ] 결과물 품질 평가

---

## 정리

| 실습       | 패턴             | 핵심 학습            |
| ---------- | ---------------- | -------------------- |
| **실습 1** | ReAct / Tool Use | Agent 기본 루프 이해 |
| **실습 2** | Reflection       | 자기 개선 패턴 이해  |
| **실습 3** | Agentic SDLC     | 실무 AI Agent 체험   |
