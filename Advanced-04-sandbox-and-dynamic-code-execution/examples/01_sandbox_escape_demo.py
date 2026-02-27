"""
실습 1: Sandbox Escape 시도와 방어 (팀 질문 1)
===============================================
AI가 생성한 위험한 코드가 어떻게 탐지·차단되는지 직접 체험합니다.

소요 시간: ~15분
필요 패키지: 없음 (stdlib만 사용)

핵심 개념:
- AST(Abstract Syntax Tree) 기반 정적 분석
- 허용목록(Allowlist) vs 차단목록(Denylist) 전략
- Python 클래스 계층 탐색을 통한 탈출 시도 원리
"""

import ast
import signal
import sys
import textwrap
from typing import Optional


# ============================================================
# 섹션 1: AST 기반 정적 분석기
# ============================================================

class SecurityError(Exception):
    """보안 정책 위반 예외"""
    pass


class DangerousCodeDetector(ast.NodeVisitor):
    """
    AST 노드를 순회하며 위험한 패턴을 탐지하는 정적 분석기.
    코드를 실행하기 전에 문법 트리를 검사합니다.
    """

    # 금지된 모듈 (import 자체를 차단)
    FORBIDDEN_MODULES = {
        'os', 'sys', 'subprocess', 'socket', 'urllib',
        'http', 'ftplib', 'smtplib', 'shutil', 'pathlib',
        'ctypes', 'cffi', 'importlib', 'pkgutil', 'zipimport',
        'pickle', 'shelve', 'marshal', 'builtins',
    }

    # 금지된 함수 호출
    FORBIDDEN_CALLS = {
        '__import__', 'eval', 'exec', 'compile',
        'open', 'input', 'breakpoint',
        'getattr', 'setattr', 'delattr', 'vars',
        'globals', 'locals', 'dir',
    }

    # 금지된 속성 접근 (탈출 시도 패턴)
    FORBIDDEN_ATTRIBUTES = {
        '__class__', '__bases__', '__subclasses__',
        '__mro__', '__dict__', '__globals__', '__builtins__',
        '__code__', '__func__', '__self__', '__module__',
        '__import__', '__loader__', '__spec__',
    }

    def visit_Import(self, node: ast.Import):
        """import os → 차단"""
        for alias in node.names:
            module_root = alias.name.split('.')[0]
            if module_root in self.FORBIDDEN_MODULES:
                raise SecurityError(
                    f"🚫 금지된 모듈 import: '{alias.name}'\n"
                    f"   허용되지 않은 모듈에 접근하려 했습니다."
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """from os import path → 차단"""
        module = node.module or ''
        module_root = module.split('.')[0]
        if module_root in self.FORBIDDEN_MODULES:
            raise SecurityError(
                f"🚫 금지된 모듈 import: 'from {module} import ...'\n"
                f"   허용되지 않은 모듈에 접근하려 했습니다."
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """__import__('os'), eval(...) → 차단"""
        if isinstance(node.func, ast.Name):
            if node.func.id in self.FORBIDDEN_CALLS:
                raise SecurityError(
                    f"🚫 금지된 함수 호출: '{node.func.id}()'\n"
                    f"   위험한 내장 함수 사용이 차단되었습니다."
                )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        """obj.__class__.__bases__[0].__subclasses__() → 차단"""
        if node.attr in self.FORBIDDEN_ATTRIBUTES:
            raise SecurityError(
                f"🚫 클래스 계층 탐색 감지: '.{node.attr}'\n"
                f"   Python 내부 구조를 통한 탈출 시도가 차단되었습니다."
            )
        self.generic_visit(node)


def analyze_code(code: str) -> Optional[str]:
    """
    코드를 정적으로 분석합니다.

    Returns:
        None: 안전한 코드
        str: 발견된 위험 설명
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"🚫 문법 오류: {e}"

    detector = DangerousCodeDetector()
    try:
        detector.visit(tree)
        return None  # 안전
    except SecurityError as e:
        return str(e)


# ============================================================
# 섹션 2: 타임아웃 기반 실행 (무한루프 방어)
# ============================================================

class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError()


def safe_eval(code: str, timeout_sec: int = 3) -> dict:
    """
    화이트리스트 기반 안전한 코드 실행.

    1단계: AST 정적 분석
    2단계: 타임아웃 적용 후 제한된 환경에서 실행
    """
    result = {
        'blocked': False,
        'reason': None,
        'output': None,
        'error': None,
    }

    # 1단계: 정적 분석
    danger = analyze_code(code)
    if danger:
        result['blocked'] = True
        result['reason'] = danger
        return result

    # 2단계: 제한된 실행 환경 구성
    safe_builtins = {
        'print': print,
        'range': range,
        'len': len,
        'sum': sum,
        'min': min,
        'max': max,
        'abs': abs,
        'round': round,
        'int': int,
        'float': float,
        'str': str,
        'bool': bool,
        'list': list,
        'dict': dict,
        'set': set,
        'tuple': tuple,
        'enumerate': enumerate,
        'zip': zip,
        'map': map,
        'filter': filter,
        'sorted': sorted,
        'reversed': reversed,
        'isinstance': isinstance,
        'type': type,
        'repr': repr,
    }

    namespace = {'__builtins__': safe_builtins}

    # 3단계: 타임아웃 적용 실행
    import io
    from contextlib import redirect_stdout

    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_sec)

    output_buf = io.StringIO()
    try:
        with redirect_stdout(output_buf):
            exec(compile(code, '<sandbox>', 'exec'), namespace)
        result['output'] = output_buf.getvalue() or repr(
            eval(compile(code, '<sandbox>', 'eval'), namespace)
            if '\n' not in code.strip() else None
        )
    except TimeoutError:
        result['blocked'] = True
        result['reason'] = f"⏰ 타임아웃: {timeout_sec}초 실행 시간 초과"
    except Exception as e:
        result['error'] = f"런타임 오류: {type(e).__name__}: {e}"
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

    return result


# ============================================================
# 섹션 3: 탈출 시도 예제 모음
# ============================================================

ESCAPE_EXAMPLES = {
    "1": {
        "name": "🗡️  기본 OS 명령 실행 (rm -rf)",
        "code": "import os; os.system('echo rm -rf 시뮬레이션')",
        "desc": "가장 기본적인 탈출: import os를 통한 시스템 명령",
    },
    "2": {
        "name": "🗡️  __import__ 우회 시도",
        "code": "__import__('subprocess').run(['ls', '/'], capture_output=True)",
        "desc": "import 키워드 대신 __import__() 함수 사용 우회 시도",
    },
    "3": {
        "name": "🗡️  클래스 계층 탐색 (고급 탈출)",
        "code": "().__class__.__bases__[0].__subclasses__()",
        "desc": "Python 내부 클래스 계층을 탐색해 os 모듈 접근 시도",
    },
    "4": {
        "name": "🗡️  from-import 우회",
        "code": "from subprocess import run; run(['whoami'])",
        "desc": "from ... import 구문으로 금지 모듈 우회 시도",
    },
    "5": {
        "name": "🗡️  무한루프 (리소스 소모)",
        "code": "while True: pass",
        "desc": "CPU를 독점하는 무한루프로 서비스 마비 시도",
    },
    "6": {
        "name": "✅ 안전한 코드",
        "code": "result = sum(range(1, 101))\nprint(f'1~100 합계: {result}')",
        "desc": "정적 분석 통과 + 정상 실행되는 안전한 코드",
    },
    "7": {
        "name": "✅ 안전한 코드 (리스트 컴프리헨션)",
        "code": "squares = [x**2 for x in range(10)]\nprint(f'제곱수: {squares}')",
        "desc": "반복문, 리스트 생성 등 기본 연산은 허용",
    },
}


# ============================================================
# 메인: 대화형 데모 인터페이스
# ============================================================

def print_banner():
    print("\n" + "=" * 60)
    print("🔐 Sandbox Escape Demo — AI 코드 탈출 시도 & 방어")
    print("=" * 60)
    print("📌 핵심: AST 정적 분석 + 타임아웃으로 위험 코드 차단")
    print()


def run_demo(code: str, name: str = "사용자 입력"):
    """코드 분석 + 실행 결과 출력"""
    print(f"\n{'─' * 50}")
    print(f"📝 코드: {name}")
    print(f"{'─' * 50}")

    # 코드 미리보기
    for line in code.strip().split('\n'):
        print(f"   {line}")

    print("\n🔍 정적 분석 중...")

    result = safe_eval(code)

    if result['blocked']:
        print(f"\n⛔ 차단됨!")
        print(f"   {result['reason']}")
    elif result['error']:
        print(f"\n⚠️  런타임 오류 (차단 아님):")
        print(f"   {result['error']}")
    else:
        print(f"\n✅ 실행 완료!")
        if result['output']:
            print(f"   출력: {result['output'].strip()}")


def run_all_examples():
    """모든 탈출 예제 자동 실행"""
    print_banner()
    print("📋 미리 정의된 탈출 시도 예제를 순서대로 실행합니다...\n")

    for key, example in ESCAPE_EXAMPLES.items():
        print(f"\n[예제 {key}] {example['name']}")
        print(f"💡 {example['desc']}")
        run_demo(example['code'], example['name'])
        input("\n   [Enter] 다음 예제로...")


def interactive_mode():
    """사용자가 직접 코드 입력하는 대화형 모드"""
    print_banner()
    print("💻 대화형 모드: 직접 코드를 입력해 탈출을 시도해보세요!")
    print("   (종료: 'quit' 또는 Ctrl+C)")
    print("   (빈 줄 두 번 입력 시 실행)\n")

    while True:
        print()
        lines = []
        try:
            while True:
                line = input(">>> " if not lines else "... ")
                if line == 'quit':
                    print("\n👋 종료합니다.")
                    return
                if line == '' and lines and lines[-1] == '':
                    break
                lines.append(line)
        except KeyboardInterrupt:
            print("\n👋 종료합니다.")
            return
        except EOFError:
            return

        code = '\n'.join(lines).strip()
        if code:
            run_demo(code)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--all':
        run_all_examples()
    else:
        print_banner()
        print("실행 옵션을 선택하세요:")
        print("  [1] 미리 정의된 탈출 예제 모두 실행 (권장 - 발표용)")
        print("  [2] 대화형 모드 (직접 코드 입력)")
        print()

        choice = input("선택 (1/2): ").strip()
        if choice == '1':
            run_all_examples()
        else:
            interactive_mode()
