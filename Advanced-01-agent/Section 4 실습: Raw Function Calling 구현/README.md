# 🤖 Section 4 실습: Raw Function Calling 구현

이 폴더는 Section 4 "Raw Function Calling 구현과 MCP로의 연결"의 실습 코드를 포함합니다.

## 📚 학습 목표

1. **Schema Design**: JSON Schema를 통한 함수 명세 설계
2. **The Loop**: While 루프를 통한 에이전트 실행 루프 구현
3. **ReAct 패턴**: Thought → Action → Observation의 반복 과정 이해

## 📁 파일 구조

```
Advanced-01-agent/
├── raw_function_calling.py  # 메인 실습 코드
├── requirements.txt         # Python 의존성
├── .env                     # API 키 설정 파일
└── README.md               # 이 파일
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상 환경 생성 (선택사항)
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate  # Windows

# 패키지 설치
pip install -r requirements.txt
```

### 2. API 키 설정

프로젝트에 포함된 `.env` 파일을 열어서 `your-gemini-api-key-here` 부분을 본인의 Gemini API 키로 변경하세요.

```
GEMINI_API_KEY=your-gemini-api-key-here
```

**Gemini API 키 발급 방법 (무료):**

1. Google AI Studio (https://aistudio.google.com/app/apikey) 접속
2. Google 계정으로 로그인
3. "Create API Key" 클릭
4. 발급받은 API 키를 복사하여 `.env` 파일에 붙여넣기

> **참고**: Gemini는 무료 할당량을 제공하며, OpenAI 호환 API를 지원하므로 기존 코드를 그대로 사용할 수 있습니다.

### 3. 실행

```bash
python raw_function_calling.py
```

## 🎯 코드 구조 설명

### [1단계: Schema Design]

```python
FUNCTIONS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "주식의 현재 가격과 변동률을 조회합니다...",
            # ...
        }
    },
    # ...
]
```

- **핵심**: `description` 필드가 Semantic Matching의 핵심입니다
- 모델은 이 설명을 읽고 어떤 함수를 호출할지 결정합니다

### [2단계: The Loop]

```python
while iteration < max_iterations:
    # 1. 모델에게 요청 전송
    response = client.chat.completions.create(...)

    # 2. tool_calls 확인
    if tool_calls:
        # 3. 함수 실행 (Action)
        result = execute_function(...)
        # 4. 결과 피드백 (Observation)
        messages.append({"role": "tool", ...})
    else:
        # Final Answer 도달
        return response.content
```

- **핵심**: 이 루프가 에이전트의 심장입니다
- 모델이 Final Answer를 반환할 때까지 반복됩니다

## 🧪 예제 질문

1. **주가 조회**: "오늘 삼성전자 주가가 얼마야?"
2. **날씨 비교**: "서울과 도쿄의 날씨를 비교해줘"
3. **복합 질문**: "애플 주가에 10을 곱한 값이 얼마야?"

## 🔍 주요 학습 포인트

### 1. Semantic Matching

- 함수의 `description`이 모델의 함수 선택을 결정합니다
- "주가"라는 단어가 포함된 질문 → `get_stock_price` 함수 선택

### 2. ReAct 루프

- **Thought**: 모델이 다음 행동 계획
- **Action**: `tool_calls`를 통한 함수 호출
- **Observation**: 함수 실행 결과 관찰

### 3. 제어권의 이전

- 개발자는 함수를 정의하고 Schema를 제공합니다
- 모델이 **언제, 어떤 함수를, 어떤 인자로** 호출할지 결정합니다

## 🎓 다음 단계: MCP로의 연결

이 실습에서 우리는 함수 명세를 직접 딕셔너리로 작성했습니다. 하지만:

- 모델이 바뀐다면? (OpenAI → Anthropic → Google)
- 연동해야 할 도구가 100개라면?
- 다른 팀의 도구를 재사용해야 한다면?

매번 이 복잡한 Schema를 새로 짜고 루프를 관리하는 건 너무나 고통스러운 일입니다.

**MCP (Model Context Protocol)**는 에이전트가 어떤 도구와도 '플러그 앤 플레이' 방식으로 연결될 수 있도록 하는 표준 규격입니다.

이 실습을 통해 에이전트의 기초 체력을 다졌다면, 다음 단계로 MCP를 통해 더 쉽고 표준화된 방식으로 확장할 수 있습니다.

→ `../Advanced-01-mcp/weather-mcp-demo/` 폴더에서 MCP 예제를 확인하세요!

## 📝 참고사항

- 이 코드는 **교육 목적**으로 작성되었습니다
- 실제 프로덕션 환경에서는 에러 처리, 보안, 비용 관리 등을 추가해야 합니다
- `calculate` 함수의 `eval()` 사용은 데모용이며, 실제로는 더 안전한 방법을 사용해야 합니다
- Gemini는 무료 할당량을 제공하며 Function Calling을 지원합니다
- 사용 가능한 모델: `gemini-1.5-flash` (빠름, 기본값), `gemini-1.5-pro` (고성능)
