# CLAUDE.md (API)

이 문서는 FastAPI 라우트와 Claude API 호출 관련 세부 사항만 다룹니다. 전반적인 실행 방법과 상위 아키텍처는 루트의 [`../CLAUDE.md`](../CLAUDE.md)를 참고하세요.

> 참고: 현재 레포의 API 코드는 루트의 `main.py` 한 파일에 있습니다. `api/` 디렉터리는 문서 분리를 위한 공간이며, 추후 라우트가 분할될 경우 이 폴더로 옮기는 것을 가정합니다.

## 라우트

- `GET /` — `templates/index.html`로 업로드 폼을 렌더링합니다.
- `POST /analyze` — 멀티파트 폼의 `file` 필드로 CSV를 받아 분석하고, 같은 템플릿에 결과를 담아 다시 렌더링합니다. 성공/오류 모두 HTTP 200을 반환하며, 오류는 템플릿의 `error` 변수로 인라인 표시됩니다.

## CSV 입력 포맷

`parse_kakao_csv`가 기대하는 컬럼은 다음과 같습니다.

| 컬럼 | 용도 |
|------|------|
| `type` | `"message"`인 행만 사용. 그 외(시스템 이벤트 등)는 조용히 버려짐 |
| `date` | LLM 입력의 타임스탬프 앞부분 |
| `time` | LLM 입력의 타임스탬프 뒷부분 |
| `nickname` | 발화자 표시 이름 |
| `message` | 본문. 공백만 있거나 빈 값이면 해당 행 버려짐 |

- 디코딩은 `utf-8-sig`(BOM 허용), 오류는 `errors="replace"`로 흡수합니다.
- 유효한 메시지가 0개면 `error` 메시지와 함께 폼을 다시 렌더링합니다.

## 메시지 수 제한

- `MAX_MESSAGES = 500`.
- 유효 메시지가 500개를 초과하면 **마지막 500개**만 사용합니다(`all_messages[-MAX_MESSAGES:]`).
- 이 경우 템플릿에 `truncated=True`가 전달되어 UI가 알립니다.

## Claude API 호출

`client.messages.create` 호출 파라미터:

- `model = "claude-opus-5-5"` (상수 `MODEL`)
- `max_tokens = 2000`
- `thinking = {"type": "adaptive"}`
- `system = SYSTEM_PROMPT` — 아래 **시스템 프롬프트 계약** 참고
- `messages = [{"role": "user", "content": chat_text}]` — `format_for_llm`이 만든 `[date time] nickname: message` 한 줄짜리 라인들을 `\n`으로 이어 붙인 문자열

`anthropic.Anthropic()`은 모듈 import 시점에 생성되므로, 서버 기동 전에 `ANTHROPIC_API_KEY`가 환경 변수에 반드시 있어야 합니다. `.env`는 `python-dotenv`가 import 시 로드합니다.

## 시스템 프롬프트 계약

`SYSTEM_PROMPT`는 모델이 정확히 아래 두 섹션만 한국어 마크다운으로 출력하도록 제약합니다.

1. `## 대화 요약` — 3~5개의 bullet
2. `## 액션 아이템` — 1~7개의 번호 리스트, 각 항목은 `**(카테고리)** 할 일 — 이유` 형식

프롬프트를 수정하더라도 **섹션 수·순서·헤딩명을 반드시 유지하세요.** 템플릿은 반환된 마크다운을 그대로 HTML로 렌더링하기 때문에, 섹션 구조가 바뀌면 UI 스타일링(`.result h2` 등)의 전제도 함께 깨집니다.

## 오류·거부 처리

두 경우 모두 템플릿의 `error` 변수로 전달되고 HTTP 200으로 응답합니다.

- `anthropic.APIStatusError` → `"Claude API 오류 (HTTP {status_code}): {message}"`
- `response.stop_reason == "refusal"` → 거부 안내 메시지

그 외 예외는 잡지 않으므로 FastAPI 기본 500 응답으로 전파됩니다.

## 응답 렌더링과 신뢰 가정

응답 content의 `type == "text"` 블록만 뽑아 `\n`으로 이어 붙인 뒤 `markdown.markdown`으로 HTML을 만들고, 템플릿에 `result_html | safe`로 삽입합니다. 즉 **모델 출력은 신뢰된 HTML로 취급**됩니다. 모델 입력 경로를 바꾸거나(예: 외부 소스 삽입) 사용자 입력을 모델 출력에 섞게 되는 변경을 할 때는 이 가정을 깨지 않도록 주의하세요.
