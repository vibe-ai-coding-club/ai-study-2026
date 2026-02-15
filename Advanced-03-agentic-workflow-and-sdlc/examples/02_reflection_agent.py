"""
실습 2: Reflection Agent (자기 성찰 패턴)
==========================================
Generator → Evaluator → 개선 루프를 구현합니다.
반복할수록 결과물의 품질이 향상되는 과정을 관찰합니다.

소요 시간: ~15분
필요: pip install anthropic python-dotenv
"""

import json

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()


# ============================================================
# Generator: 결과물 생성
# ============================================================
def generate(task: str, feedback: str | None = None) -> str:
    """작업을 수행하여 결과물을 생성합니다."""
    prompt = f"다음 작업을 수행해주세요:\n\n{task}"
    if feedback:
        prompt += f"\n\n⚠️ 이전 평가에서 받은 피드백을 반드시 반영해주세요:\n{feedback}"

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


# ============================================================
# Evaluator: 결과물 평가
# ============================================================
def evaluate(task: str, result: str) -> dict:
    """결과물을 평가하고 점수와 피드백을 반환합니다."""
    prompt = f"""당신은 엄격하지만 공정한 평가자입니다.
다음 작업의 결과물을 평가해주세요.

## 작업
{task}

## 결과물
{result}

## 평가 기준
1. 정확성 (내용이 정확한가?)
2. 완성도 (빠진 부분이 없는가?)
3. 명확성 (이해하기 쉬운가?)
4. 구조화 (잘 정리되어 있는가?)

## 응답 형식
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트를 추가하지 마세요.

{{"score": <1-10 정수>, "strengths": "<잘한 점>", "weaknesses": "<개선할 점>", "feedback": "<구체적 개선 방향>"}}"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()

    # JSON 파싱 (코드블록으로 감싸져 있을 수 있음)
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"score": 5, "strengths": "파싱 실패", "weaknesses": "파싱 실패", "feedback": text}


# ============================================================
# Reflection Loop: 핵심 루프
# ============================================================
def reflection_agent(
    task: str,
    max_iterations: int = 3,
    threshold: int = 8,
    verbose: bool = True,
) -> dict:
    """
    Reflection 패턴으로 결과물을 반복 개선합니다.

    1. Generate: 결과물 생성
    2. Evaluate: 품질 평가 (1-10점)
    3. 점수 < threshold → 피드백 반영하여 재생성
    4. 점수 >= threshold → 완료
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"🎯 작업: {task}")
        print(f"📊 목표 점수: {threshold}/10")
        print(f"🔄 최대 반복: {max_iterations}회")
        print(f"{'='*60}")

    # 1차 생성
    if verbose:
        print(f"\n--- Iteration 0: 초기 생성 ---")
        print("  ⏳ 생성 중...")

    result = generate(task)

    if verbose:
        print(f"  ✅ 생성 완료 ({len(result)}자)")
        print(f"  📝 미리보기: {result[:150]}...")

    history = []

    # 반복 개선 루프
    for i in range(max_iterations):
        if verbose:
            print(f"\n--- Iteration {i + 1}: 평가 & 개선 ---")
            print("  ⏳ 평가 중...")

        # 평가
        evaluation = evaluate(task, result)
        score = evaluation.get("score", 0)

        history.append(
            {
                "iteration": i + 1,
                "score": score,
                "strengths": evaluation.get("strengths", ""),
                "weaknesses": evaluation.get("weaknesses", ""),
            }
        )

        if verbose:
            print(f"  📊 점수: {score}/10")
            print(f"  ✅ 잘한 점: {evaluation.get('strengths', '')}")
            print(f"  ⚠️ 개선점: {evaluation.get('weaknesses', '')}")

        # 목표 점수 달성 시 종료
        if score >= threshold:
            if verbose:
                print(f"\n🎉 목표 점수 {threshold}점 달성! ({i + 1}회 반복)")
            break

        # 피드백 반영하여 재생성
        feedback = evaluation.get("feedback", "")
        if verbose:
            print(f"  💡 피드백: {feedback}")
            print(f"  ⏳ 피드백 반영하여 재생성 중...")

        result = generate(task, feedback)

        if verbose:
            print(f"  ✅ 재생성 완료 ({len(result)}자)")
    else:
        if verbose:
            print(f"\n⏰ 최대 반복 횟수 {max_iterations}회 도달")

    # 결과 요약
    if verbose:
        print(f"\n{'='*60}")
        print("📈 점수 변화:")
        for h in history:
            bar = "█" * h["score"] + "░" * (10 - h["score"])
            print(f"  반복 {h['iteration']}: [{bar}] {h['score']}/10")
        print(f"{'='*60}")

    return {
        "result": result,
        "history": history,
        "iterations": len(history),
    }


# ============================================================
# 실행
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  Reflection Agent 실습")
    print("  - Generator → Evaluator → 개선 루프")
    print("  - 반복할수록 품질이 향상되는 과정을 관찰")
    print("=" * 60)

    tasks = [
        "Python으로 이진 탐색(Binary Search) 함수를 작성하고, 동작 원리를 주석으로 설명해주세요.",
        "'AI Agent의 미래'라는 주제로 블로그 서론 (200자 내외)을 작성해주세요.",
        "REST API 설계 시 지켜야 할 베스트 프랙티스 5가지를 정리해주세요.",
    ]

    print("\n예시 작업:")
    for i, t in enumerate(tasks, 1):
        print(f"  {i}. {t}")
    print()

    user_input = input("작업 입력 (또는 예시 번호 1-3): ").strip()
    if user_input in ("1", "2", "3"):
        user_input = tasks[int(user_input) - 1]

    if user_input:
        output = reflection_agent(user_input, max_iterations=3, threshold=8)

        print(f"\n{'='*60}")
        print("📄 최종 결과물:")
        print(f"{'='*60}")
        print(output["result"])
