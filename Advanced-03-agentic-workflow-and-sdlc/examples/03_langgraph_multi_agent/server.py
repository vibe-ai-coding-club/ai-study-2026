"""
실습 3: LangGraph Multi-Agent Pipeline
==========================================
LangGraph StateGraph로 멀티에이전트 파이프라인을 구현합니다.
5개의 Agent가 순차/조건부로 실행되며, SSE로 실시간 진행을 스트리밍합니다.
API 키 없이 더미 데이터로 동작합니다.

소요 시간: ~20분
필요: pip install langgraph fastapi uvicorn
실행: python server.py → http://localhost:8000
"""

import asyncio
import json
from pathlib import Path
from typing import TypedDict

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel


# ============================================================
# 1단계: 워크플로우 상태 정의
# ============================================================
class WorkflowState(TypedDict):
    prompt: str  # 사용자 입력 프롬프트
    search_query: str  # Orchestrator가 생성한 검색 쿼리
    retrieved_templates: list[dict]  # Retriever가 찾은 템플릿 목록
    reference_xmls: list[str]  # 참조 XML 코드
    analysis: dict  # Analyzer의 분석 결과
    generated_xml: str  # Generator가 생성한 XML
    validation_passed: bool  # Validator 검증 통과 여부
    validation_feedback: str  # Validator 피드백
    retry_count: int  # 재시도 횟수


# ============================================================
# 2단계: Mock 데이터
# ============================================================
MOCK_TEMPLATES = [
    {
        "id": "tpl-001",
        "name": "로그인 폼",
        "type": "form",
        "components": ["TextInput", "PasswordInput", "Button"],
        "popularity": 95,
    },
    {
        "id": "tpl-002",
        "name": "대시보드 레이아웃",
        "type": "dashboard",
        "components": ["Card", "Chart", "Table", "Header"],
        "popularity": 87,
    },
    {
        "id": "tpl-003",
        "name": "상품 카드 목록",
        "type": "list",
        "components": ["Card", "Image", "Badge", "Pagination"],
        "popularity": 82,
    },
]

MOCK_REFERENCE_XMLS = [
    '<Screen name="ref-form"><Header title="Form" /><FormGroup><TextInput label="Name" /></FormGroup></Screen>',
    '<Screen name="ref-list"><Header title="Items" /><ListView><Card title="Item" /></ListView></Screen>',
]

MOCK_ANALYSIS = {
    "layout": "vertical-stack",
    "primary_components": ["Header", "FormGroup", "ButtonGroup"],
    "color_scheme": "brand-primary",
    "responsive": True,
    "accessibility_level": "AA",
    "estimated_complexity": "medium",
}

INCOMPLETE_XML = """\
<Screen name="generated-ui">
  <Header title="UI 화면" />
  <FormGroup>
    <TextInput label="이메일" type="email" />
    <TextInput label="비밀번호" type="password" />
  </FormGroup>
  <!-- TODO: 버튼 그룹 미완성 -->
</Screen>"""

COMPLETE_XML = """\
<Screen name="generated-ui">
  <Header title="UI 화면" subtitle="환영합니다" />
  <FormGroup>
    <TextInput label="이메일" type="email" placeholder="이메일을 입력하세요" required="true" />
    <TextInput label="비밀번호" type="password" placeholder="비밀번호를 입력하세요" required="true" />
  </FormGroup>
  <ButtonGroup layout="vertical" spacing="8">
    <Button type="primary" label="시작하기" action="submit" />
    <Button type="secondary" label="둘러보기" action="navigate" target="explore" />
  </ButtonGroup>
  <Footer>
    <Link label="도움말" action="navigate" target="help" />
  </Footer>
</Screen>"""


# ============================================================
# 3단계: Agent 함수 (5개)
# ============================================================
AGENT_LABELS = {
    "orchestrate": "Orchestrator",
    "retrieve": "Retriever",
    "analyze": "Analyzer",
    "generate": "Generator",
    "validate": "Validator",
}

AGENT_SEQUENCE = list(AGENT_LABELS.keys())


async def orchestrate(state: WorkflowState) -> dict:
    """프롬프트를 분석하여 검색 쿼리를 생성합니다."""
    await asyncio.sleep(1.5)
    prompt = state["prompt"]
    # 간단한 문자열 조작으로 검색 쿼리 생성
    keywords = (
        prompt.replace("을 ", " ")
        .replace("를 ", " ")
        .replace("해주세요", "")
        .replace("만들어", "")
        .strip()
    )
    search_query = f"UI 템플릿 {keywords}"
    return {"search_query": search_query}


async def retrieve(state: WorkflowState) -> dict:
    """검색 쿼리로 템플릿을 검색합니다 (Mock)."""
    await asyncio.sleep(2.0)
    return {
        "retrieved_templates": MOCK_TEMPLATES,
        "reference_xmls": MOCK_REFERENCE_XMLS,
    }


async def analyze(state: WorkflowState) -> dict:
    """검색된 템플릿을 분석합니다 (Mock)."""
    await asyncio.sleep(2.0)
    return {"analysis": MOCK_ANALYSIS}


async def generate(state: WorkflowState) -> dict:
    """분석 결과를 바탕으로 XML을 생성합니다."""
    await asyncio.sleep(2.5)
    if state["retry_count"] == 0:
        return {"generated_xml": INCOMPLETE_XML}
    return {"generated_xml": COMPLETE_XML}


async def validate(state: WorkflowState) -> dict:
    """생성된 XML의 완성도를 검증합니다."""
    await asyncio.sleep(1.5)
    xml = state["generated_xml"]

    if "TODO" in xml or "미완성" in xml:
        return {
            "validation_passed": False,
            "validation_feedback": (
                "ButtonGroup이 누락되었습니다. "
                "필수 컴포넌트(Header, FormGroup, ButtonGroup)를 모두 포함해주세요."
            ),
            "retry_count": state["retry_count"] + 1,
        }

    return {
        "validation_passed": True,
        "validation_feedback": "",
        "retry_count": state["retry_count"],
    }


def should_retry(state: WorkflowState) -> str:
    """검증 결과에 따라 재시도 여부를 결정합니다."""
    if state["validation_passed"]:
        return "complete"
    return "retry"


# ============================================================
# 4단계: 그래프 구성
# ============================================================
graph = StateGraph(WorkflowState)

graph.add_node("orchestrate", orchestrate)
graph.add_node("retrieve", retrieve)
graph.add_node("analyze", analyze)
graph.add_node("generate", generate)
graph.add_node("validate", validate)

graph.add_edge(START, "orchestrate")
graph.add_edge("orchestrate", "retrieve")
graph.add_edge("retrieve", "analyze")
graph.add_edge("analyze", "generate")
graph.add_edge("generate", "validate")
graph.add_conditional_edges(
    "validate",
    should_retry,
    {"retry": "generate", "complete": END},
)

compiled = graph.compile()


# ============================================================
# 5단계: FastAPI 서버 (SSE 스트리밍)
# ============================================================
app = FastAPI(title="LangGraph Multi-Agent Pipeline")

STATIC_DIR = Path(__file__).parent


def _format_sse(data: dict) -> str:
    """SSE 형식으로 데이터를 포맷합니다."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _serialize(data: dict) -> dict:
    """직렬화가 어려운 타입을 문자열로 변환합니다."""
    result = {}
    for key, value in data.items():
        try:
            json.dumps(value, ensure_ascii=False)
            result[key] = value
        except (TypeError, ValueError):
            result[key] = str(value)
    return result


async def stream_workflow(prompt: str):
    """워크플로우를 실행하고 SSE 이벤트를 스트리밍합니다."""
    initial_state: WorkflowState = {
        "prompt": prompt,
        "search_query": "",
        "retrieved_templates": [],
        "reference_xmls": [],
        "analysis": {},
        "generated_xml": "",
        "validation_passed": False,
        "validation_feedback": "",
        "retry_count": 0,
    }

    # 첫 번째 Agent 시작 이벤트
    yield _format_sse({
        "type": "agent_start",
        "agent": "orchestrate",
        "step": 1,
        "label": "Orchestrator",
    })

    final_xml = ""

    async for chunk in compiled.astream(initial_state, stream_mode="updates"):
        for node_name, updates in chunk.items():
            if node_name not in AGENT_LABELS:
                continue

            step = AGENT_SEQUENCE.index(node_name) + 1

            # generated_xml 추적
            if "generated_xml" in updates:
                final_xml = updates["generated_xml"]

            # Agent 완료 이벤트
            yield _format_sse({
                "type": "agent_complete",
                "agent": node_name,
                "step": step,
                "label": AGENT_LABELS[node_name],
                "data": _serialize(updates),
            })

            # 다음 Agent 시작 또는 재시도 처리
            if node_name == "validate":
                if not updates.get("validation_passed", False):
                    yield _format_sse({
                        "type": "retry",
                        "retry_count": updates.get("retry_count", 1),
                        "feedback": updates.get("validation_feedback", ""),
                    })
                    yield _format_sse({
                        "type": "agent_start",
                        "agent": "generate",
                        "step": 4,
                        "label": "Generator",
                    })
            else:
                next_idx = AGENT_SEQUENCE.index(node_name) + 1
                if next_idx < len(AGENT_SEQUENCE):
                    next_agent = AGENT_SEQUENCE[next_idx]
                    yield _format_sse({
                        "type": "agent_start",
                        "agent": next_agent,
                        "step": next_idx + 1,
                        "label": AGENT_LABELS[next_agent],
                    })

    # 최종 결과
    yield _format_sse({"type": "result", "xml": final_xml})


class GenerateRequest(BaseModel):
    prompt: str


@app.get("/")
async def root():
    """index.html을 서빙합니다."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health():
    """헬스체크"""
    return {"status": "ok"}


@app.post("/api/generate/stream")
async def generate_stream(request: GenerateRequest):
    """SSE 스트리밍으로 워크플로우를 실행합니다."""
    return StreamingResponse(
        stream_workflow(request.prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("  LangGraph Multi-Agent Pipeline")
    print("  http://localhost:8000 에서 실행 중")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
