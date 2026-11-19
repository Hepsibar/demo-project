# ADR 0003 — CSV를 utf-8-sig + errors="replace"로 디코딩

- Status: Accepted
- 관련 코드: `main.py` (`parse_kakao_csv`: `raw.decode("utf-8-sig", errors="replace")`)

## Context

업로드되는 CSV는 사용자가 카카오톡/엑셀 등에서 내보낸 것으로, 인코딩을 통제할 수 없다.
흔한 두 가지 문제:

1. **BOM**: Windows 계열 도구가 UTF-8 파일 앞에 BOM(`﻿`)을 붙인다. 일반 `utf-8`로 읽으면
   첫 컬럼명(`type`)이 `﻿type`이 되어 `DictReader` 키 매칭이 조용히 어긋난다 — 모든 행이 버려진다.
2. **깨진 바이트**: 혼합 인코딩이나 잘린 파일이면 디코딩 자체가 `UnicodeDecodeError`로 터진다.

## Decision

- `utf-8-sig`로 디코딩해 **BOM이 있으면 자동으로 제거**한다(없으면 일반 utf-8과 동일).
- `errors="replace"`로 **깨진 바이트는 치환 문자로 흡수**해, 일부 손상 때문에 전체 분석이 실패하지 않게 한다.

## Consequences

- BOM 유무와 무관하게 컬럼 매칭이 안정적으로 동작한다.
- 손상된 입력도 "분석 불가"로 죽지 않고 best-effort로 진행된다. 대신 치환 문자가 본문에 섞일 수 있는데,
  요약 용도에서는 허용 가능한 트레이드오프로 본다.
- 디코딩을 엄격 모드로 되돌리려면 이 ADR의 두 리스크(1·2)를 먼저 고려할 것.
