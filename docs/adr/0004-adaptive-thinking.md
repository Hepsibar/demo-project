# ADR 0004 — Claude 호출에 adaptive thinking 사용

- Status: Accepted
- 관련 코드: `main.py` (`client.messages.create(..., thinking={"type": "adaptive"})`)

## Context

`/analyze`의 작업은 긴 채팅 로그에서 주제를 추려 요약하고, 방장이 할 일을 **우선순위와 이유를 붙여**
도출하는 것이다. 이는 단순 추출이 아니라 다소의 추론을 요한다. 그러나 입력 길이·난이도는 매 요청마다 크게 다르다.

- 고정 reasoning budget을 크게 잡으면 짧은 로그에도 불필요한 지연·비용이 든다.
- 아예 끄면 복잡한 로그에서 액션 아이템의 질이 떨어진다.

## Decision

`thinking={"type": "adaptive"}`를 사용해, **모델이 입력 난이도에 맞춰 reasoning 양을 스스로 조절**하게 한다.
쉬운 입력은 빠르게, 복잡한 입력은 더 숙고하도록 맡긴다.

## Consequences

- 요약/액션 아이템 품질과 지연·비용 사이를 요청 단위로 자동 균형잡는다.
- `max_tokens = 2000`은 최종 출력 토큰 한도이며 thinking과 별개다. thinking 모드를 바꿀 때 함께 재검토한다.
- 모드/파라미터를 바꾸면 비용·지연 특성이 변하므로, 변경 시 [`../../api/CLAUDE.md`](../../api/CLAUDE.md)의 "Claude API 호출"도 갱신한다.
