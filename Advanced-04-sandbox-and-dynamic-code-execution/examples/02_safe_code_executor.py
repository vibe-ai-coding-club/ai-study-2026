"""
실습 2: subprocess + resource limits로 안전한 코드 실행
========================================================
프로세스 격리와 OS 레벨 리소스 제한을 사용해 코드를 안전하게 실행합니다.
실습 1(AST 분석)과 달리, 코드를 실제로 실행하되 격리된 환경에서 실행합니다.

소요 시간: ~10분
필요 패키지: 없음 (stdlib만 사용)

핵심 개념:
- subprocess로 자식 프로세스 격리
- resource 모듈로 CPU/메모리/파일 제한
- 환경변수 격리로 민감 정보 차단
- timeout으로 무한루프 방어

⚠️  참고: resource 모듈은 macOS에서 일부 제한이 있습니다.
   (RLIMIT_AS가 RLIMIT_RSS로 대체될 수 있음)
"""

import os
import resource
import subprocess
import sys
import tempfile
import textwrap
import time
from typing import Optional


# ============================================================
# 섹션 1: resource limits 설정
# ============================================================

def get_resource_limits() -> dict:
    """현재 시스템의 resource 제한 정보 조회"""
    limits = {}
    limit_names = [
        ('CPU (초)', resource.RLIMIT_CPU),
        ('파일 크기 (bytes)', resource.RLIMIT_FSIZE),
        ('프로세스 수', resource.RLIMIT_NPROC),
    ]

    # RLIMIT_AS는 macOS에서 다를 수 있음
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        limits['주소 공간 (bytes)'] = (soft, hard)
    except Exception:
        try:
            soft, hard = resource.getrlimit(resource.RLIMIT_RSS)
            limits['RSS 메모리 (bytes)'] = (soft, hard)
        except Exception:
            pass

    for name, res_type in limit_names:
        try:
            soft, hard = resource.getrlimit(res_type)
            limits[name] = (soft, hard)
        except Exception:
            pass

    return limits


def print_resource_limits():
    """현재 resource limits 출력"""
    print("\n📊 현재 시스템 Resource Limits:")
    print(f"{'항목':<20} {'Soft':<20} {'Hard':<20}")
    print("─" * 60)

    limits = get_resource_limits()
    for name, (soft, hard) in limits.items():
        soft_str = str(soft) if soft != resource.RLIM_INFINITY else "무제한"
        hard_str = str(hard) if hard != resource.RLIM_INFINITY else "무제한"
        print(f"{name:<20} {soft_str:<20} {hard_str:<20}")


# ============================================================
# 섹션 2: subprocess 기반 격리 실행기
# ============================================================

SANDBOX_WRAPPER = """
import resource
import sys
import os

# ── Resource Limits 설정 ──────────────────────────────────
# CPU 시간: {cpu_limit}초 초과 시 SIGXCPU → 프로세스 종료
resource.setrlimit(resource.RLIMIT_CPU, ({cpu_limit}, {cpu_limit}))

# 파일 크기: {file_limit}바이트 초과 시 IOError
resource.setrlimit(resource.RLIMIT_FSIZE, ({file_limit}, {file_limit}))

# 프로세스 수: {proc_limit}개 초과 시 BlockingIOError (Fork Bomb 방어)
try:
    resource.setrlimit(resource.RLIMIT_NPROC, ({proc_limit}, {proc_limit}))
except Exception:
    pass

# 메모리: {mem_limit}바이트 초과 시 MemoryError
try:
    resource.setrlimit(resource.RLIMIT_AS, ({mem_limit}, {mem_limit}))
except Exception:
    try:
        resource.setrlimit(resource.RLIMIT_RSS, ({mem_limit}, {mem_limit}))
    except Exception:
        pass

# ── 환경 격리 ───────────────────────────────────────────
# 민감한 환경변수 제거 (API 키, 패스워드 등)
sensitive_env_prefixes = ('AWS_', 'ANTHROPIC_', 'OPENAI_', 'SECRET_', 'PASSWORD_', 'TOKEN_')
for key in list(os.environ.keys()):
    if any(key.startswith(p) for p in sensitive_env_prefixes):
        del os.environ[key]

# ── 사용자 코드 실행 ────────────────────────────────────
{user_code}
"""


class SafeExecutor:
    """subprocess + resource limits 기반 안전한 코드 실행기"""

    def __init__(
        self,
        cpu_limit: int = 5,           # CPU 시간 제한 (초)
        mem_limit: int = 64 * 1024 * 1024,   # 메모리 제한 (64MB)
        file_limit: int = 1024 * 1024,       # 파일 크기 제한 (1MB)
        proc_limit: int = 10,                # 프로세스 수 제한
        timeout: int = 10,                   # subprocess timeout (초)
    ):
        self.cpu_limit = cpu_limit
        self.mem_limit = mem_limit
        self.file_limit = file_limit
        self.proc_limit = proc_limit
        self.timeout = timeout

    def execute(self, user_code: str) -> dict:
        """
        코드를 격리된 subprocess에서 실행합니다.

        격리 레이어:
        1. 별도 Python 프로세스 (PID 격리)
        2. resource limits (CPU/메모리/파일/프로세스)
        3. 환경변수 격리 (민감 정보 제거)
        4. subprocess timeout (무한루프 최후 방어)
        """
        # wrapper 스크립트 생성
        wrapper_code = SANDBOX_WRAPPER.format(
            cpu_limit=self.cpu_limit,
            mem_limit=self.mem_limit,
            file_limit=self.file_limit,
            proc_limit=self.proc_limit,
            user_code=textwrap.indent(user_code, '    '),
        )

        start_time = time.time()
        result = {
            'success': False,
            'stdout': '',
            'stderr': '',
            'elapsed': 0,
            'exit_code': None,
            'killed_by': None,
        }

        try:
            proc_result = subprocess.run(
                [sys.executable, '-c', wrapper_code],
                capture_output=True,
                timeout=self.timeout,
                text=True,
                env={  # 최소 환경변수만 전달
                    'PATH': '/usr/bin:/bin:/usr/local/bin',
                    'PYTHONPATH': '',
                    'HOME': '/tmp',
                    'LANG': 'en_US.UTF-8',
                },
            )

            result['success'] = proc_result.returncode == 0
            result['stdout'] = proc_result.stdout
            result['stderr'] = proc_result.stderr
            result['exit_code'] = proc_result.returncode

            # exit code 해석
            if proc_result.returncode < 0:
                import signal as sig
                try:
                    signal_name = sig.Signals(-proc_result.returncode).name
                    result['killed_by'] = signal_name
                except Exception:
                    result['killed_by'] = f"Signal {-proc_result.returncode}"

        except subprocess.TimeoutExpired:
            result['killed_by'] = 'TIMEOUT'
            result['stderr'] = f"⏰ 실행 시간 제한 초과 ({self.timeout}초)"

        result['elapsed'] = round(time.time() - start_time, 3)
        return result

    def print_config(self):
        """현재 설정 출력"""
        print(f"\n⚙️  SafeExecutor 설정:")
        print(f"   CPU 제한:       {self.cpu_limit}초")
        print(f"   메모리 제한:     {self.mem_limit // (1024*1024)}MB")
        print(f"   파일 크기 제한:  {self.file_limit // 1024}KB")
        print(f"   프로세스 제한:   {self.proc_limit}개")
        print(f"   Timeout:        {self.timeout}초")


# ============================================================
# 섹션 3: 데모 시나리오 모음
# ============================================================

DEMO_SCENARIOS = {
    "1": {
        "name": "✅ 정상 코드",
        "code": """
result = [x**2 for x in range(10)]
print(f"제곱수 목록: {result}")
print(f"합계: {sum(result)}")
""",
        "desc": "일반적인 계산 코드 — 정상 실행됨",
        "expect": "정상 실행",
    },
    "2": {
        "name": "⏰ 무한 루프 (CPU 타임아웃 테스트)",
        "code": """
print("무한루프 시작...")
while True:
    pass
""",
        "desc": "CPU 시간을 모두 소비하는 무한루프 → CPU 제한으로 종료",
        "expect": "SIGXCPU 또는 TIMEOUT",
    },
    "3": {
        "name": "💥 메모리 폭탄 (메모리 제한 테스트)",
        "code": """
print("메모리 폭탄 시작...")
x = []
while True:
    x.extend([0] * 10**6)
    print(f"현재 크기: {len(x):,}")
""",
        "desc": "메모리를 무한히 할당하는 코드 → 메모리 제한으로 종료",
        "expect": "MemoryError 또는 SIGKILL",
    },
    "4": {
        "name": "📁 대용량 파일 생성 시도 (파일 크기 제한 테스트)",
        "code": """
print("대용량 파일 생성 시도...")
with open('/tmp/sandbox_test.txt', 'w') as f:
    for i in range(10**6):
        f.write(f"line {i}: {'A' * 100}\\n")
print("파일 생성 완료 (이 메시지가 나오면 제한 실패)")
""",
        "desc": "1GB 파일 생성 시도 → 파일 크기 제한(1MB)으로 차단",
        "expect": "IOError (파일 크기 초과)",
    },
    "5": {
        "name": "🔑 환경변수 탈취 시도 (격리 테스트)",
        "code": """
import os
print("환경변수 목록:")
for key, val in sorted(os.environ.items()):
    print(f"  {key}={val[:20]}...")
""",
        "desc": "API 키 등 민감 환경변수 탈취 시도 → 격리된 환경에서 민감 변수 없음",
        "expect": "환경변수 목록에 AWS_/ANTHROPIC_ 등 없음",
    },
    "6": {
        "name": "🐛 재귀 폭탄 (스택 오버플로우)",
        "code": """
def infinite_recursion(n=0):
    return infinite_recursion(n + 1)

print("재귀 폭탄 시작...")
infinite_recursion()
""",
        "desc": "재귀 호출로 스택을 소진하는 코드",
        "expect": "RecursionError",
    },
}


def run_scenario(executor: SafeExecutor, scenario_id: str):
    """단일 시나리오 실행 및 결과 출력"""
    scenario = DEMO_SCENARIOS[scenario_id]

    print(f"\n{'=' * 60}")
    print(f"📌 시나리오: {scenario['name']}")
    print(f"💡 설명: {scenario['desc']}")
    print(f"🎯 예상 결과: {scenario['expect']}")
    print(f"{'─' * 60}")
    print("📄 코드:")
    for line in scenario['code'].strip().split('\n'):
        print(f"   {line}")
    print(f"{'─' * 60}")

    print("🚀 실행 중...")
    result = executor.execute(scenario['code'])

    print(f"\n⏱️  실행 시간: {result['elapsed']}초")
    print(f"🔢 종료 코드: {result['exit_code']}")

    if result['killed_by']:
        print(f"⛔ 종료 원인: {result['killed_by']}")

    if result['stdout']:
        print(f"\n📤 출력:\n{textwrap.indent(result['stdout'].strip(), '   ')}")

    if result['stderr'] and result['stderr'].strip():
        print(f"\n⚠️  오류/경고:\n{textwrap.indent(result['stderr'].strip()[:500], '   ')}")

    if result['success']:
        print(f"\n✅ 정상 실행 완료")
    else:
        print(f"\n🛡️  제한에 의해 종료됨")


# ============================================================
# 메인: 대화형 인터페이스
# ============================================================

def print_banner():
    print("\n" + "=" * 60)
    print("🛡️  Safe Code Executor — subprocess + resource limits")
    print("=" * 60)
    print("📌 격리된 subprocess에서 resource limits를 적용해 실행")
    print()


if __name__ == '__main__':
    print_banner()

    executor = SafeExecutor(
        cpu_limit=5,
        mem_limit=64 * 1024 * 1024,  # 64MB
        file_limit=1024 * 1024,       # 1MB
        proc_limit=10,
        timeout=8,
    )

    executor.print_config()

    print("\n" + "─" * 60)
    print("📋 시나리오를 선택하세요:")
    for key, scenario in DEMO_SCENARIOS.items():
        print(f"  [{key}] {scenario['name']}")
    print("  [A] 모든 시나리오 순서대로 실행 (발표용)")
    print("  [Q] 직접 코드 입력")
    print()

    choice = input("선택: ").strip().upper()

    if choice == 'A':
        for key in DEMO_SCENARIOS:
            run_scenario(executor, key)
            input("\n   [Enter] 다음 시나리오...")

    elif choice == 'Q':
        print("\n💻 직접 코드를 입력하세요 (빈 줄 두 번으로 실행, 'exit'로 종료):")
        while True:
            lines = []
            try:
                while True:
                    line = input(">>> " if not lines else "... ")
                    if line.lower() == 'exit':
                        print("👋 종료합니다.")
                        sys.exit(0)
                    if line == '' and lines and lines[-1] == '':
                        break
                    lines.append(line)
            except (KeyboardInterrupt, EOFError):
                print("\n👋 종료합니다.")
                break

            code = '\n'.join(lines).strip()
            if code:
                result = executor.execute(code)
                if result['killed_by']:
                    print(f"⛔ 종료: {result['killed_by']} ({result['elapsed']}초)")
                if result['stdout']:
                    print(result['stdout'])
                if result['stderr']:
                    print(f"⚠️  {result['stderr'][:300]}")

    elif choice in DEMO_SCENARIOS:
        run_scenario(executor, choice)

    else:
        print("잘못된 선택입니다. 1~6, A, Q 중 선택하세요.")
