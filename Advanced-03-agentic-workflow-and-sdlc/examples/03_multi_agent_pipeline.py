"""
실습 3: Multi-Agent Pipeline (다중 에이전트)
=============================================
프레임워크 없이 순수 Python으로 멀티에이전트 파이프라인을 구현합니다.
3명의 Agent가 역할을 나누어 순차적으로 작업합니다.

소요 시간: ~15분
필요: pip install anthropic python-dotenv
"""

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()


# ============================================================
# Agent 클래스 정의
# ============================================================
class Agent:
    """역할과 시스템 프롬프트를 가진 간단한 Agent."""

    def __init__(self, name: str, role: str, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt

    def run(self, task: str) -> str:
        """주어진 작업을 수행하고 결과를 반환합니다."""
        print(f"\n  🤖 [{self.name}] ({self.role})")
        print(f"     작업: {task[:100]}...")
        print(f"     ⏳ 작업 중...")

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            system=self.system_prompt,
            messages=[{"role": "user", "content": task}],
        )
        result = response.content[0].text
        print(f"     ✅ 완료 ({len(result)}자)")
        return result


# ============================================================
# 파이프라인: Agent들을 순차 연결
# ============================================================
class Pipeline:
    """여러 Agent를 순차적으로 연결하는 파이프라인."""

    def __init__(self, name: str, agents: list[tuple[Agent, str]]):
        """
        agents: [(agent, task_template), ...] 형태의 리스트
        task_template에서 {input}은 이전 Agent의 출력으로 치환됩니다.
        {user_input}은 사용자의 최초 입력으로 치환됩니다.
        """
        self.name = name
        self.agents = agents

    def run(self, user_input: str) -> dict:
        """파이프라인을 실행합니다."""
        print(f"\n{'='*60}")
        print(f"🚀 파이프라인: {self.name}")
        print(f"📝 입력: {user_input}")
        print(f"👥 참여 Agent: {len(self.agents)}명")
        print(f"{'='*60}")

        results = []
        current_input = user_input

        for i, (agent, task_template) in enumerate(self.agents, 1):
            print(f"\n--- Stage {i}/{len(self.agents)} ---")

            # 템플릿의 {input}을 이전 결과로, {user_input}을 원래 입력으로 치환
            task = task_template.format(
                input=current_input,
                user_input=user_input,
            )

            result = agent.run(task)
            results.append(
                {
                    "agent": agent.name,
                    "role": agent.role,
                    "output": result,
                }
            )
            current_input = result

        print(f"\n{'='*60}")
        print(f"✅ 파이프라인 완료!")
        print(f"{'='*60}")

        return {
            "pipeline": self.name,
            "stages": results,
            "final_output": results[-1]["output"],
        }


# ============================================================
# 시나리오 1: 기술 블로그 작성 파이프라인
# ============================================================
def create_blog_pipeline() -> Pipeline:
    """Researcher → Writer → Editor 파이프라인."""
    researcher = Agent(
        name="Researcher",
        role="기술 리서처",
        system_prompt="""당신은 AI/기술 분야의 전문 리서처입니다.
주어진 주제에 대해 핵심 포인트 5가지를 조사하여 정리합니다.
각 포인트에 대해 2-3문장으로 설명하세요.
한국어로 작성하세요.""",
    )

    writer = Agent(
        name="Writer",
        role="기술 블로거",
        system_prompt="""당신은 기술 블로그 전문 작가입니다.
주어진 리서치 자료를 바탕으로 읽기 쉬운 블로그 글을 작성합니다.
- 제목, 서론, 본론, 결론 구조
- 500자 내외
- 한국어로 작성
- 마크다운 형식""",
    )

    editor = Agent(
        name="Editor",
        role="편집자",
        system_prompt="""당신은 기술 콘텐츠 전문 편집자입니다.
주어진 블로그 글을 검토하고 개선합니다.
- 문법/맞춤법 수정
- 문장 흐름 개선
- 전문 용어 정확성 확인
- 개선된 최종본을 출력하세요
- 한국어로 작성""",
    )

    return Pipeline(
        name="기술 블로그 작성",
        agents=[
            (researcher, "다음 주제에 대해 핵심 포인트 5가지를 조사해주세요: {user_input}"),
            (writer, "다음 리서치 자료를 바탕으로 블로그 글을 작성해주세요:\n\n{input}"),
            (editor, "다음 블로그 글을 검토하고 개선해주세요:\n\n{input}"),
        ],
    )


# ============================================================
# 시나리오 2: 코드 리뷰 파이프라인
# ============================================================
def create_code_review_pipeline() -> Pipeline:
    """Coder → Reviewer → Improver 파이프라인."""
    coder = Agent(
        name="Coder",
        role="개발자",
        system_prompt="""당신은 Python 전문 개발자입니다.
주어진 요구사항에 맞는 깔끔한 Python 코드를 작성합니다.
- 타입 힌트 사용
- docstring 포함
- 에러 처리 포함""",
    )

    reviewer = Agent(
        name="Reviewer",
        role="코드 리뷰어",
        system_prompt="""당신은 시니어 코드 리뷰어입니다.
주어진 코드를 다음 기준으로 리뷰하세요:
1. 버그/잠재적 이슈
2. 성능 개선점
3. 가독성/유지보수성
4. 보안 취약점
5. 베스트 프랙티스 준수 여부

구체적인 개선 제안을 포함하세요.""",
    )

    improver = Agent(
        name="Improver",
        role="코드 개선자",
        system_prompt="""당신은 코드 품질 개선 전문가입니다.
원본 코드와 리뷰 피드백을 받아 개선된 코드를 작성합니다.
리뷰에서 지적된 모든 사항을 반영하세요.
개선된 부분에 주석으로 '# 개선: ...' 을 표시하세요.""",
    )

    return Pipeline(
        name="코드 리뷰",
        agents=[
            (coder, "다음 요구사항에 맞는 Python 코드를 작성해주세요: {user_input}"),
            (reviewer, "다음 코드를 리뷰해주세요:\n\n{input}"),
            (
                improver,
                "다음 리뷰 피드백을 반영하여 코드를 개선해주세요.\n\n## 원래 요구사항\n{user_input}\n\n## 리뷰 피드백\n{input}",
            ),
        ],
    )


# ============================================================
# 실행
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  Multi-Agent Pipeline 실습")
    print("  - 프레임워크 없이 순수 Python으로 구현")
    print("  - 여러 Agent가 역할을 나누어 순차 협업")
    print("=" * 60)

    print("\n시나리오 선택:")
    print("  1. 기술 블로그 작성 (Researcher → Writer → Editor)")
    print("  2. 코드 리뷰 (Coder → Reviewer → Improver)")

    choice = input("\n선택 (1 또는 2): ").strip()

    if choice == "1":
        pipeline = create_blog_pipeline()
        examples = [
            "2026년 AI Agent 트렌드",
            "Agentic Workflow가 소프트웨어 개발을 바꾸는 방법",
            "LLM의 한계와 도구 사용으로 극복하는 방법",
        ]
    else:
        pipeline = create_code_review_pipeline()
        examples = [
            "URL을 입력 받아 웹페이지를 크롤링하고 텍스트를 추출하는 함수",
            "CSV 파일을 읽어서 통계 요약(평균, 중앙값, 표준편차)을 계산하는 함수",
            "간단한 LRU 캐시를 구현하는 클래스",
        ]

    print(f"\n예시 입력:")
    for i, ex in enumerate(examples, 1):
        print(f"  {i}. {ex}")

    user_input = input("\n입력 (또는 예시 번호): ").strip()
    if user_input in ("1", "2", "3"):
        user_input = examples[int(user_input) - 1]

    if user_input:
        result = pipeline.run(user_input)

        print(f"\n{'='*60}")
        print("📄 각 Stage 결과 요약:")
        print(f"{'='*60}")
        for i, stage in enumerate(result["stages"], 1):
            print(f"\n--- Stage {i}: {stage['agent']} ({stage['role']}) ---")
            print(stage["output"][:300])
            if len(stage["output"]) > 300:
                print("... (생략)")

        print(f"\n{'='*60}")
        print("📄 최종 결과물:")
        print(f"{'='*60}")
        print(result["final_output"])
