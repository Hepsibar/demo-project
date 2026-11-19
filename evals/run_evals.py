"""대표 task의 2섹션 응답 계약 pass-rate를 측정한다.

fixtures/sample_kakao.csv를 /analyze에 N회 POST하고, 매 응답이 계약
(`## 대화 요약` · `## 액션 아이템` 두 헤딩, HTTP 200, 인라인 오류 없음)을
지키는지 집계해 pass-rate를 낸다. 결과는 evals/results/latest.json에도 남긴다.

smoke.py가 "1회 통과/실패"를 보는 반면, 이 러너는 **여러 번 돌려 안정성(pass-rate)**을
정량화한다 — 프롬프트/모델 변경이 계약 준수율에 주는 영향을 숫자로 추적하기 위함이다.

환경 변수:
  EVAL_URL   대상 URL (기본 http://127.0.0.1:8000/analyze)
  EVAL_RUNS  반복 횟수 (기본 5)
  EVAL_MIN   통과로 볼 최소 pass-rate (기본 1.0)

종료 코드: 0 = pass-rate >= EVAL_MIN, 1 = 미달, 2 = 픽스처 없음, 3 = 서버 도달 불가.

주의: 매 실행이 **실제 Claude 호출**이므로 RUNS만큼 API 비용이 발생한다.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "fixtures" / "sample_kakao.csv"
RESULTS = Path(__file__).resolve().parent / "results"
URL = os.environ.get("EVAL_URL", "http://127.0.0.1:8000/analyze")
RUNS = int(os.environ.get("EVAL_RUNS", "5"))
MIN_RATE = float(os.environ.get("EVAL_MIN", "1.0"))
BOUNDARY = "----eval-boundary-abcdef1234"


def build_multipart(path: Path) -> tuple[bytes, str]:
    parts = [
        f"--{BOUNDARY}".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"'.encode(),
        b"Content-Type: text/csv",
        b"",
        path.read_bytes(),
        f"--{BOUNDARY}--".encode(),
        b"",
    ]
    return b"\r\n".join(parts), f"multipart/form-data; boundary={BOUNDARY}"


def check_contract(status: int, html: str) -> dict[str, bool]:
    return {
        "HTTP 200": status == 200,
        "has '대화 요약' heading": "대화 요약" in html,
        "has '액션 아이템' heading": "액션 아이템" in html,
        "no inline error block": 'class="error"' not in html,
    }


def run_once(body: bytes, ctype: str) -> tuple[bool, dict[str, bool], float]:
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": ctype})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=180) as resp:
        html = resp.read().decode("utf-8", errors="replace")
        status = resp.status
    checks = check_contract(status, html)
    return all(checks.values()), checks, time.monotonic() - t0


def main() -> int:
    if not FIXTURE.exists():
        print(f"FAIL: fixture missing: {FIXTURE}")
        return 2

    body, ctype = build_multipart(FIXTURE)
    run_records = []
    passed = 0

    for i in range(1, RUNS + 1):
        try:
            ok, checks, elapsed = run_once(body, ctype)
        except urllib.error.URLError as exc:
            print(f"FAIL: cannot reach {URL}: {exc}")
            print("hint: start the server first with scripts/dev.ps1 (or dev.sh)")
            return 3
        passed += ok
        failed_checks = [name for name, v in checks.items() if not v]
        run_records.append({"run": i, "pass": ok, "elapsed_s": round(elapsed, 2),
                            "failed_checks": failed_checks})
        mark = "OK" if ok else "FAIL"
        extra = "" if ok else f" ({', '.join(failed_checks)})"
        print(f"  [{mark}] run {i}/{RUNS}  {elapsed:.1f}s{extra}")

    rate = passed / RUNS if RUNS else 0.0
    summary = {
        "measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "url": URL,
        "runs": RUNS,
        "passed": passed,
        "pass_rate": round(rate, 4),
        "min_rate": MIN_RATE,
        "runs_detail": run_records,
    }

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "latest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\npass-rate: {passed}/{RUNS} = {rate:.0%}  (min {MIN_RATE:.0%})")
    print(f"written: {RESULTS / 'latest.json'}")
    if rate < MIN_RATE:
        print("EVAL FAILED: pass-rate below threshold")
        return 1
    print("EVAL OK")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    sys.exit(main())
