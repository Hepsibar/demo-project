# Architecture Decision Records (ADR)

이 디렉터리는 코드만 봐서는 **"왜 이렇게 했는지"가 드러나지 않는 설계 결정**을 기록합니다.
신규 에이전트/기여자가 같은 질문을 다시 파헤치거나, 이유를 모른 채 되돌리는 것을 막기 위한 tribal-knowledge store입니다.

각 ADR은 하나의 결정을 다루며, 되돌리기 전에 먼저 읽어야 하는 맥락을 담습니다.

| ADR | 결정 | 관련 코드 |
|-----|------|-----------|
| [0001](0001-two-section-prompt-contract.md) | 응답을 정확히 2섹션(`## 대화 요약`·`## 액션 아이템`) 마크다운으로 고정 | `main.py` `SYSTEM_PROMPT`, `templates/index.html` |
| [0002](0002-max-messages-500.md) | 메시지를 마지막 500개로 tail-trim (`MAX_MESSAGES = 500`) | `main.py` |
| [0003](0003-utf-8-sig-decoding.md) | CSV를 `utf-8-sig` + `errors="replace"`로 디코딩 | `main.py` `parse_kakao_csv` |
| [0004](0004-adaptive-thinking.md) | Claude 호출에 `thinking={"type": "adaptive"}` 사용 | `main.py` |

새 결정이 "왜"를 필요로 하면 `000N-<slug>.md`로 추가하고 위 표에 한 줄을 더합니다.
형식은 기존 ADR을 따릅니다(Status · Context · Decision · Consequences).
