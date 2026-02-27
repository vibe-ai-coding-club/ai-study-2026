# 04. 실습 가이드 — Sandbox를 직접 체험해보자

---

## 실습 개요

| 실습 | 파일 | 핵심 개념 | 소요 시간 |
|------|------|-----------|-----------|
| **실습 1** | `01_sandbox_escape_demo.py` | AST 정적 분석 + 탈출 시도 차단 | ~15분 |
| **실습 2** | `02_safe_code_executor.py` | subprocess + resource limits | ~10분 |
| **실습 3** | `03_network_isolation_demo.py` | 네트워크 격리 + 데이터 유출 탐지 | ~10분 |

**준비사항:**
```bash
cd Advanced-04-sandbox-and-dynamic-code-execution/examples
python --version  # Python 3.8+ 필요
# 추가 패키지 불필요 (stdlib만 사용)
```

---

## 실습 1: Sandbox Escape Demo — "AI를 해킹해 보아요!"

> 팀 질문 1: "보안이 뚫리는 걸 보고 싶어요!"

### 실행

```bash
python 01_sandbox_escape_demo.py
```

### 데모 시나리오

```
🔐 Sandbox Escape Demo
==================================================
탈출 시도에 사용할 코드를 입력하세요.
(입력 후 Enter 두 번, 종료는 'quit')

>>> import os; os.system('rm -rf /')
🔍 코드 분석 중...
⛔ 차단: 금지된 모듈 import 감지 (os)

>>> __import__('subprocess').run(['rm', '-rf', '/tmp'])
🔍 코드 분석 중...
⛔ 차단: __import__ 호출 감지

>>> ().__class__.__bases__[0].__subclasses__()
🔍 코드 분석 중...
⛔ 차단: 클래스 계층 탐색 감지 (__subclasses__)

>>> 1 + 1
🔍 코드 분석 중...
✅ 안전: 실행 결과 = 2

>>> while True: pass
🔍 코드 분석 중...
✅ 정적 분석 통과...
⏰ 실행 중... (타임아웃 3초)
⛔ 타임아웃: 실행 시간 초과 (3초)
```

### 핵심 코드 개념

```python
# AST 기반 정적 분석
import ast

class DangerousCodeDetector(ast.NodeVisitor):
    FORBIDDEN_MODULES = {'os', 'subprocess', 'sys', 'socket', ...}

    def visit_Import(self, node):
        # import os → 즉시 차단
        for alias in node.names:
            if alias.name.split('.')[0] in self.FORBIDDEN_MODULES:
                raise SecurityError(f"금지된 모듈: {alias.name}")

    def visit_Call(self, node):
        # __import__('os') → 차단
        if isinstance(node.func, ast.Name):
            if node.func.id == '__import__':
                raise SecurityError("__import__ 호출 금지")
```

---

## 실습 2: Safe Code Executor — "제한된 환경에서 실행"

### 실행

```bash
python 02_safe_code_executor.py
```

### 데모 시나리오

```
🛡️ Safe Code Executor
==================================================
[1] 정상 코드 실행
[2] 무한 루프 (타임아웃 테스트)
[3] 메모리 폭탄 (메모리 제한 테스트)
[4] 직접 입력

>>> 2
🔧 resource limits 설정:
   CPU: 5초
   메모리: 256MB
   파일 크기: 1MB
🚀 실행: while True: pass
⏰ 타임아웃 (5초 초과) → 프로세스 강제 종료

>>> 3
🚀 실행: x = []\nwhile True: x.extend([0]*10**6)
💥 메모리 제한 초과 (256MB) → OOM 종료
```

### 핵심 코드 개념

```python
import subprocess, resource, sys, tempfile, os

def create_resource_limited_script(code: str) -> str:
    """resource limits를 설정하는 wrapper 스크립트 생성"""
    wrapper = f"""
import resource, sys
# CPU 제한: 5초
resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
# 메모리 제한: 256MB
resource.setrlimit(resource.RLIMIT_AS, (256*1024*1024, 256*1024*1024))
# 파일 크기 제한: 1MB
resource.setrlimit(resource.RLIMIT_FSIZE, (1024*1024, 1024*1024))

# 사용자 코드 실행
{code}
"""
    return wrapper

def safe_execute(code: str, timeout: int = 10):
    """격리된 subprocess에서 코드 실행"""
    result = subprocess.run(
        [sys.executable, '-c', create_resource_limited_script(code)],
        capture_output=True,
        timeout=timeout,        # 프로세스 레벨 타임아웃
        text=True,
        env={                   # 환경변수 격리
            'PATH': '/usr/bin:/bin',
            'PYTHONPATH': ''
        }
    )
    return result
```

---

## 실습 3: Network Isolation Demo — "데이터 유출 차단"

> 팀 질문 2: "프록시 통제로 외부로 데이터 안나가는 거"

### 실행

```bash
python 03_network_isolation_demo.py
```

### 데모 시나리오

```
🌐 Network Isolation Demo
==================================================
[모드 선택]
1. 완전 차단 모드 (모든 외부 접근 차단)
2. 화이트리스트 모드 (허용 도메인만 접근)
3. DLP 모드 (민감 데이터 유출 탐지)
4. 비교: 격리 없을 때 vs 있을 때

>>> 1
🔒 완전 차단 모드 활성화

코드 실행: urllib.request.urlopen('https://google.com')
🚫 차단: 외부 접근 불가 (google.com)

코드 실행: socket.connect(('8.8.8.8', 53))
🚫 차단: 외부 접근 불가 (8.8.8.8)

>>> 3
🔍 DLP 모드 활성화

코드 실행: requests.post('http://api.site.com',
           data={'key': 'sk-ant-api03-xxxxx'})
⚠️  민감 데이터 탐지: API 키 패턴 발견 (sk-...)
🚫 차단: 민감 데이터 외부 전송 시도
```

### 핵심 코드 개념

```python
import socket
import re

# 민감 데이터 패턴
SENSITIVE_PATTERNS = [
    (re.compile(r'sk-[a-zA-Z0-9-]{40,}'), 'API 키'),
    (re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'), '카드번호'),
    (re.compile(r'password\s*=\s*["\']?.{4,}'), '비밀번호'),
]

ALLOWED_HOSTS = {'localhost', '127.0.0.1', 'api.anthropic.com'}

_original_connect = socket.socket.connect

def safe_connect(self, address):
    host = address[0] if isinstance(address, tuple) else address

    # 화이트리스트 확인
    if host not in ALLOWED_HOSTS:
        raise ConnectionRefusedError(
            f"🚫 네트워크 격리: {host} 접근 차단"
        )

    return _original_connect(self, address)

# Monkey-patching
socket.socket.connect = safe_connect
```

---

## FigJam 발표 구조

> 기존 Week 1~3 패턴 (Section > Step 구조)

```
📋 Week 4: Sandbox & Dynamic Code Execution
│
├── 🟡 Section 01: 왜 Sandbox인가?
│   ├── Step 1-1: AI 코드의 비확정성
│   ├── Step 1-2: 실제 위협 (Escape / Exfiltration / Exhaustion)
│   └── Step 1-3: Defense in Depth 개요
│
├── 🟡 Section 02: 격리 기술 스택
│   ├── Step 2-1: OS 레이어 (namespaces / cgroups / seccomp)
│   ├── Step 2-2: 컨테이너 레이어 (Docker / gVisor)
│   └── Step 2-3: MicroVM (Firecracker / WASM)
│
├── 🟡 Section 03: 실제 구현체 비교
│   ├── Step 3-1: E2B / Modal / OpenAI Code Interpreter
│   └── Step 3-2: Claude Code의 Proxy 제어 방식
│
└── 🟡 Section 04: 실습
    ├── [실습 1] Sandbox Escape Demo   ← 팀 질문 1
    ├── [실습 2] Safe Code Executor
    └── [실습 3] Network Isolation     ← 팀 질문 2
```

**FigJam 노드 색상 컨벤션:**
- 🟡 노란색 하이라이트: 섹션 제목
- 🔵 파란색 박스: 이론 개념
- 🟢 초록색 박스: 실습/코드
- 🔴 빨간색 박스: 위험/경고 예시

---

## 팀 질문 최종 정리

### Q1. "보안이 뚫리는 걸 보고 싶어요! rm -rf 같은 거..."

**답변:**
1. 정적 분석 없이 `exec("import os; os.system('rm -rf /')")` → 실제로 실행됨 (위험!)
2. AST 분석기 적용 → `import os` 감지 즉시 차단
3. `__import__('os')` 우회 시도 → `__import__` 호출 감지 차단
4. `().__class__.__bases__[0].__subclasses__()` 고급 탈출 → 클래스 탐색 차단

**핵심 메시지:** "모든 탈출 시도를 막는 것보다, 처음부터 격리된 환경을 쓰는 것이 더 안전"

### Q2. "프록시 통제로 외부로 데이터 안나가는 거..."

**답변:**
1. 네트워크 Namespace: 아예 외부 인터페이스 없음
2. iptables: 특정 UID의 outbound 차단
3. 프록시 경유: 모든 트래픽이 DLP 필터 통과
4. Claude Code가 이 방식 채택: Anthropic 프록시 경유로 임의 외부 서버 접근 차단

### Q3. "샌드박스가 가능한 원리가 알고 싶어요"

**답변 (3단 요약):**
1. **무엇을 보이게 할지** = Linux Namespaces (프로세스 격리)
2. **얼마나 쓸 수 있는지** = cgroups (리소스 제한)
3. **무엇을 할 수 있는지** = seccomp (시스템콜 필터)

"세 가지를 조합하면 → 완전히 격리된 환경, 이게 컨테이너/VM의 기반"

---

## 실습 코드 실행 체크리스트

```bash
# 1. 환경 확인
python --version        # 3.8+ 필요
uname -s               # Linux 권장 (macOS는 resource 모듈 일부 제한)

# 2. 실습 1 실행
python 01_sandbox_escape_demo.py
# → 탈출 시도 입력 후 차단 메시지 확인

# 3. 실습 2 실행
python 02_safe_code_executor.py
# → 메뉴에서 2(무한루프), 3(메모리폭탄) 선택 → 차단 확인

# 4. 실습 3 실행
python 03_network_isolation_demo.py
# → 모드 1(완전차단): 외부 URL 접근 차단 확인
# → 모드 3(DLP): API 키 포함 요청 탐지 확인
```
