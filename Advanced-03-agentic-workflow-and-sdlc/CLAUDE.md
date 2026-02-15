# Advanced-03: Agentic Workflow & SDLC

## 프로젝트 개요
AI 학습 동아리 심화 과정 3주차 - Agentic Workflow와 SDLC에 대한 학습 자료 및 실습 프로젝트

## 디렉토리 구조
```
Advanced-03-agentic-workflow-and-sdlc/
├── CLAUDE.md                          # 이 파일
├── docs/                              # 학습 자료 (Markdown → PPT 변환용)
│   ├── 001-agentic-workflow-overview.md   # Agentic Workflow 개요
│   ├── 002-agentic-design-patterns.md     # Agentic Design Patterns (4가지)
│   ├── 003-agent-architectures.md         # Agent 아키텍처 심화
│   ├── 004-sdlc-overview.md               # SDLC 개요와 전통적 모델
│   ├── 005-ai-assisted-sdlc.md            # AI-Assisted SDLC
│   ├── 006-agentic-sdlc.md               # Agentic SDLC
│   ├── 007-agentic-frameworks.md          # 주요 Agentic 프레임워크
│   └── 008-hands-on-guide.md              # 실습 가이드
├── examples/                          # 실습 코드 (~15분씩)
│   ├── 01_react_agent.py              # ReAct Agent (Tool Use + Planning)
│   ├── 02_reflection_agent.py         # Reflection Agent (자기 성찰)
│   ├── 03_multi_agent_pipeline.py     # Multi-Agent Pipeline (역할 분담)
│   ├── .env.sample                    # 환경 변수 샘플
│   └── requirements.txt              # 의존성
└── ...
```

## 커리큘럼 순서
1. Agentic Workflow 개요 - 정의, 구성요소, 기본 루프
2. Design Patterns - Reflection, Tool Use, Planning, Multi-Agent
3. Agent 아키텍처 - Prompt Chaining → Orchestrator-Workers 스펙트럼
4. SDLC 개요 - Waterfall, Agile, DevOps
5. AI-Assisted SDLC - SDLC 각 단계별 AI 활용
6. Agentic SDLC - Agent가 자율적으로 수행하는 SDLC
7. 프레임워크 - LangGraph, CrewAI, AutoGen, Agents SDK
8. 실습 가이드 - ReAct Agent, Reflection, Claude Code, CrewAI

## 컨벤션
- 문서 번호: `001-`, `002-` 형태
- 다이어그램: Mermaid 문법 사용
- 실습 코드: Python 기반 (anthropic, crewai, langgraph)
- 학습 자료는 PPT 발표용으로 작성 (간결, 시각적)

## 상위 프로젝트 구조
이 프로젝트는 `ai-study-2026` 저장소의 일부:
- Advanced-01-agent: Agent 기초
- Advanced-01-mcp: MCP 프로토콜
- Advanced-02-multimodal: 멀티모달
- Advanced-02-multimodal-embedding: 멀티모달 임베딩
- **Advanced-03-agentic-workflow-and-sdlc**: 현재 프로젝트
