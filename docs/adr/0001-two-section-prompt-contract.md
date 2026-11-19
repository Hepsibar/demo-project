# ADR 0001 — 응답을 정확히 2섹션 마크다운으로 고정

- Status: Accepted
- 관련 코드: `main.py` (`SYSTEM_PROMPT`), `templates/index.html` (`.result h2`), `scripts/smoke.py`

## Context

`SYSTEM_PROMPT`은 모델이 **정확히 두 섹션**(`## 대화 요약`, `## 액션 아이템`)만 한국어 마크다운으로
출력하도록 강하게 제약합니다. 코드만 보면 "프롬프트를 자유롭게 고쳐도 되는 것"처럼 보이지만,
이 2섹션 구조는 단순한 취향이 아니라 **렌더링·검증 양쪽이 의존하는 계약**입니다.

- `templates/index.html`은 모델이 돌려준 마크다운을 `markdown.markdown`으로 변환해 `| safe`로 주입하고,
  `.result h2` 스타일이 섹션 헤딩이 둘 있다는 전제에 맞춰져 있습니다.
- `scripts/smoke.py`는 응답 HTML에 두 헤딩 문자열이 있는지로 성공을 판정합니다.
- 출력은 신뢰된 HTML로 취급되므로(모델 출력 = trusted), 구조가 흔들리면 UI가 조용히 깨집니다.

## Decision

응답 계약을 **섹션 수·순서·헤딩명 고정**으로 둔다. 프롬프트 문구는 바꿔도 되지만,
`## 대화 요약`(3~5 bullet) → `## 액션 아이템`(1~7 번호 리스트, `**(카테고리)** 할 일 — 이유`) 구조는 유지한다.

## Consequences

- 프롬프트를 수정할 때는 이 2섹션 구조를 깨지 않아야 하며, 바꾼다면 `templates/index.html`의 스타일 전제와
  `scripts/smoke.py`의 체크를 **함께** 갱신해야 한다.
- 섹션을 늘리거나 이름을 바꾸는 변경은 새 ADR로 이 결정을 대체(supersede)하고 기록한다.
- 상세 계약은 [`../../api/CLAUDE.md`](../../api/CLAUDE.md)의 "시스템 프롬프트 계약"을 참고.
