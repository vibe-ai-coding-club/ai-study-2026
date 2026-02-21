# Advanced-03: Agentic Workflow & SDLC

## 프로젝트 개요
AI 학습 동아리 심화 과정 3주차 - Agentic Workflow와 SDLC에 대한 학습 자료 및 실습 프로젝트

## 디렉토리 구조
```
Advanced-03-agentic-workflow-and-sdlc/
├── CLAUDE.md                          # 이 파일
├── docs/                              # 학습 자료 (Markdown → PPT 변환용)
│   ├── 01-agentic-workflow-and-patterns.md  # 이론 1: Agentic Workflow & Design Patterns (~15분)
│   ├── 02-agent-architectures.md            # 이론 2: Agent 아키텍처 스펙트럼 (~12분)
│   ├── 03-sdlc-and-ai.md                   # 이론 3: SDLC와 AI (~13분)
│   └── 04-hands-on.md                      # 실습: 프레임워크 비교 + 실습 가이드 (~20분)
├── examples/                          # 실습 코드
│   ├── 01_react_agent.py              # 실습 1: ReAct Agent (Tool Use + Planning)
│   ├── 02_reflection_agent.py         # 실습 2: Reflection Agent (자기 성찰)
│   ├── .env.sample                    # 환경 변수 샘플
│   └── requirements.txt              # 의존성
└── ...
```

## 발표 구성 (1시간)

### 이론 (40분)
1. **Agentic Workflow & Patterns** (~15분) - 정의, 구성요소, 기본 루프, 4가지 Design Patterns, Genspark 사례
2. **Agent 아키텍처** (~12분) - 5단계 스펙트럼 (Prompt Chaining → Autonomous Agent), 선택 가이드
3. **SDLC와 AI** (~13분) - SDLC 기본 → AI-Assisted → Agentic SDLC, 도구 소개

### 실습 (20분)
4. **실습** (~20분) - 프레임워크 비교표 + ReAct Agent, Reflection, Claude Code 실습

## 컨벤션
- 문서 번호: `01-`, `02-` 형태
- 다이어그램: Mermaid 문법 사용
- 실습 코드: Python 기반 (anthropic)
- 학습 자료는 PPT 발표용으로 작성 (간결, 시각적)

## 상위 프로젝트 구조
이 프로젝트는 `ai-study-2026` 저장소의 일부:
- Advanced-01-agent: Agent 기초
- Advanced-01-mcp: MCP 프로토콜
- Advanced-02-multimodal: 멀티모달
- Advanced-02-multimodal-embedding: 멀티모달 임베딩
- **Advanced-03-agentic-workflow-and-sdlc**: 현재 프로젝트
