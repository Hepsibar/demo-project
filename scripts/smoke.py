"""End-to-end smoke test: POST fixtures/sample_kakao.csv to /analyze and
verify the two-section response contract."""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "fixtures" / "sample_kakao.csv"
URL = os.environ.get("SMOKE_URL", "http://127.0.0.1:8000/analyze")
BOUNDARY = "----smoke-boundary-abcdef1234"


def build_multipart(path: Path) -> tuple[bytes, str]:
    parts = [
        f"--{BOUNDARY}".encode(),
        (
            f'Content-Disposition: form-data; name="file"; filename="{path.name}"'
        ).encode(),
        b"Content-Type: text/csv",
        b"",
        path.read_bytes(),
        f"--{BOUNDARY}--".encode(),
        b"",
    ]
    body = b"\r\n".join(parts)
    return body, f"multipart/form-data; boundary={BOUNDARY}"


def main() -> int:
    if not FIXTURE.exists():
        print(f"FAIL: fixture missing: {FIXTURE}")
        return 2

    body, ctype = build_multipart(FIXTURE)
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": ctype})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.URLError as exc:
        print(f"FAIL: cannot reach {URL}: {exc}")
        print("hint: start the server first with scripts/dev.ps1 (or dev.sh)")
        return 3

    checks = {
        "HTTP 200": status == 200,
        "has '대화 요약' heading": "대화 요약" in html,
        "has '액션 아이템' heading": "액션 아이템" in html,
        "no inline error block": 'class="error"' not in html,
    }

    print(f"status: {status}, body: {len(html)} bytes")
    failed = [name for name, ok in checks.items() if not ok]
    for name, ok in checks.items():
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")

    if failed:
        print(f"SMOKE FAILED: {len(failed)} check(s)")
        return 1
    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    sys.exit(main())
