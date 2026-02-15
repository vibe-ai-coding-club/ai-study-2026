# 003. Agent 아키텍처 심화

---

## Agent 아키텍처 스펙트럼

Anthropic의 "Building Effective Agents" 가이드 기반:

```mermaid
graph LR
    A["Prompt<br/>Chaining"] --> B["Router<br/>Workflow"]
    B --> C["Parallel<br/>Workflow"]
    C --> D["Orchestrator<br/>Workers"]
    D --> E["Evaluator<br/>Optimizer"]
    E --> F["Autonomous<br/>Agent"]

    style A fill:#e8f5e9
    style F fill:#ffebee
```

> **간단함** ←――――――――――――――――→ **복잡함**

> **핵심 원칙**: 가능한 한 가장 단순한 구조를 사용하라.
> 복잡한 아키텍처는 필요할 때만 도입한다.

---

## Level 1: Prompt Chaining (프롬프트 체이닝)

> LLM 호출을 **순차적으로 연결**, 이전 출력이 다음 입력이 됨

### 구조

```mermaid
flowchart LR
    L1["LLM Call 1<br/>입력"] --> Gate{"Gate<br/>검증"}
    Gate -->|통과| L2["LLM Call 2<br/>출력"]
    Gate -->|실패| Fail["중단"]
```

### 특징

- 각 단계가 **명확하고 독립적**
- 중간에 **게이트(검증)** 추가 가능
- 디버깅이 쉬움

### 사용 사례

```
예시: 마케팅 카피 생성

Step 1: [LLM] 제품 특징 분석 → 핵심 키워드 추출
Step 2: [Gate] 키워드가 3개 이상? → Yes
Step 3: [LLM] 키워드 기반 카피 5개 생성
Step 4: [LLM] 최적의 카피 1개 선택 및 다듬기
```

---

## Level 2: Routing Workflow (라우팅)

> 입력을 **분류하여 적절한 처리 경로로 분기**

### 구조

```mermaid
flowchart TD
    Input["입력"] --> Router["Router<br/>LLM 분류"]
    Router -->|간단| PathA["경로 A<br/>간단한 처리"]
    Router -->|보통| PathB["경로 B<br/>보통 처리"]
    Router -->|복잡| PathC["경로 C<br/>복잡한 처리"]
```

### 사용 사례

```mermaid
flowchart TD
    Msg["고객 메시지"] --> Router["Router 분류"]
    Router -->|"환불 문의"| Refund["환불 처리 Agent"]
    Router -->|"기술 문의"| Tech["기술 지원 Agent"]
    Router -->|"일반 문의"| FAQ["FAQ Agent"]
    Router -->|"불만/긴급"| Human["사람에게 에스컬레이션"]
```

### 장점

- 각 경로에 **전문화된 프롬프트/모델** 사용 가능
- 간단한 요청은 가벼운 모델, 복잡한 요청은 강력한 모델
- **비용 최적화** 가능

---

## Level 3: Parallelization (병렬화)

> 여러 LLM 호출을 **동시에 실행**하여 효율성 증대

### A. Sectioning (분할)

```mermaid
flowchart TD
    Input["입력"] --> A["LLM A<br/>보안 검사"]
    Input --> B["LLM B<br/>성능 검사"]
    Input --> C["LLM C<br/>가독성 검사"]
    A --> Result["종합 결과"]
    B --> Result
    C --> Result
```

### B. Voting (투표)

```mermaid
flowchart TD
    Input["입력"] --> L1["LLM 1 → 답: A"]
    Input --> L2["LLM 2 → 답: A"]
    Input --> L3["LLM 3 → 답: B"]
    L1 --> Vote["다수결: A"]
    L2 --> Vote
    L3 --> Vote
```

### 사용 사례

- **코드 리뷰**: 보안, 성능, 스타일을 병렬로 검사
- **콘텐츠 검수**: 사실 확인, 문법, 톤을 동시에 체크
- **의사결정**: 여러 LLM의 답변을 종합하여 신뢰도 향상

---

## Level 4: Orchestrator-Workers (오케스트레이터-워커)

> 중앙 오케스트레이터가 **동적으로 작업을 분배**하고 결과를 종합

### 구조

```mermaid
flowchart TD
    Orch["Orchestrator (LLM)<br/>1. 작업 분석<br/>2. 하위 작업 생성 (동적)<br/>3. Worker에게 할당<br/>4. 결과 종합"]
    Orch --> W1["Worker 1 (LLM)"]
    Orch --> W2["Worker 2 (LLM)"]
    Orch --> W3["Worker 3 (LLM)"]

    style W1 fill:#fff3e0
    style W2 fill:#fff3e0
    style W3 fill:#fff3e0
```

### Prompt Chaining과의 차이

| 구분   | Prompt Chaining | Orchestrator-Workers |
| ------ | --------------- | -------------------- |
| 단계   | 사전에 고정     | **동적으로 결정**    |
| 분기   | 없음 (순차)     | 입력에 따라 변화     |
| 병렬   | 불가            | 가능                 |
| 유연성 | 낮음            | **높음**             |

### 사용 사례

```mermaid
flowchart TD
    Input["이 프로젝트를 리팩토링해줘"] --> Orch["Orchestrator 분석<br/>10개 파일 발견, 3가지 이슈"]
    Orch --> W1["Worker 1<br/>auth.py 리팩토링"]
    Orch --> W2["Worker 2<br/>database.py 리팩토링"]
    Orch --> W3["Worker 3<br/>api.py 리팩토링"]
    Orch --> W4["Worker 4<br/>테스트 업데이트"]
    W1 --> Result["결과 종합"]
    W2 --> Result
    W3 --> Result
    W4 --> Result
```

---

## Level 5: Evaluator-Optimizer (평가자-최적화)

> 생성과 평가를 **분리**하여 반복적으로 품질 향상

### 구조

```mermaid
flowchart TD
    Gen["Generator (LLM)<br/>생성/수정"] -->|결과물| Eval["Evaluator (LLM)<br/>평가/피드백"]
    Eval -->|"품질 미달: 피드백"| Gen
    Eval -->|"품질 충족"| Final["최종 결과"]
```

### Reflection과의 관계

- Reflection 패턴의 **구체적 아키텍처 구현**
- Generator와 Evaluator를 **다른 프롬프트/모델**로 분리
- 평가 기준을 **명시적으로 정의** 가능

### 사용 사례

```mermaid
sequenceDiagram
    participant G as Generator
    participant E as Evaluator

    G->>E: 영→한 번역 결과
    E->>G: 85/100, "3번째 문장 부자연스러움"
    G->>E: 피드백 반영 재번역
    E-->>G: 95/100 - 통과!
```

---

## 아키텍처 선택 가이드

### 언제 어떤 아키텍처를 사용할까?

```mermaid
flowchart TD
    Q1{"작업이 단순한가?"} -->|Yes| PC["Prompt Chaining"]
    Q1 -->|No| Q2{"입력 유형이 다양한가?"}
    Q2 -->|Yes| RT["Routing"]
    Q2 -->|No| Q3{"독립적으로 병렬<br/>처리 가능한가?"}
    Q3 -->|Yes| PL["Parallelization"]
    Q3 -->|No| Q4{"작업이 동적으로<br/>변하는가?"}
    Q4 -->|Yes| OW["Orchestrator-Workers"]
    Q4 -->|No| Q5{"반복적 품질<br/>개선이 필요한가?"}
    Q5 -->|Yes| EO["Evaluator-Optimizer"]
    Q5 -->|No| AA["Autonomous Agent"]
```

---

## 정리

| 아키텍처                 | 핵심         | 적합한 경우            |
| ------------------------ | ------------ | ---------------------- |
| **Prompt Chaining**      | 순차 연결    | 단계가 명확한 작업     |
| **Routing**              | 분류 후 분기 | 입력 유형이 다양       |
| **Parallelization**      | 동시 실행    | 독립적 하위 작업       |
| **Orchestrator-Workers** | 동적 분배    | 복잡하고 유동적인 작업 |
| **Evaluator-Optimizer**  | 반복 개선    | 높은 품질 요구         |

**다음 장**: SDLC 개요와 전통적 모델 →
