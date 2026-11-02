# Architecture

단일 파일 FastAPI 앱(`main.py`)과 하나의 Jinja 템플릿(`templates/index.html`)으로 구성됩니다. 전체 파이프라인은 두 개의 라우트에 들어 있습니다.

- `GET /` — 업로드 폼을 렌더링합니다.
- `POST /analyze` — 업로드된 CSV를 파싱하고, 마지막 500개 메시지만 추려 Claude에 보낸 뒤, 반환된 마크다운을 HTML로 렌더링해 같은 템플릿을 다시 렌더링합니다.

템플릿은 모델이 돌려준 마크다운이 **정확히 두 섹션**(`## 대화 요약`, `## 액션 아이템`)으로 끝난다고 가정하고, 그 결과를 `| safe`로 삽입합니다. 따라서 모델 입력 경로나 시스템 프롬프트를 수정할 때는 이 두 가정을 깨지 않아야 합니다.

## 구성 요소

```
demo_project/
├── main.py            # FastAPI 앱 · 라우트 · Claude 호출 · CSV 파서
├── templates/
│   └── index.html     # 업로드 폼 + 결과 렌더링 (Jinja2)
├── requirements.txt
├── .env               # ANTHROPIC_API_KEY (python-dotenv로 로드)
└── api/
    └── CLAUDE.md      # 라우트/Claude 호출 세부 가이드
```

- **웹 레이어**: FastAPI + Jinja2. 라우트 핸들러가 그대로 템플릿을 렌더링하는 전통적인 서버 사이드 렌더링 구조이며, 별도의 프런트엔드 빌드가 없습니다.
- **파싱 레이어**: `parse_kakao_csv` / `format_for_llm` 두 함수가 CSV → 메시지 리스트 → LLM용 플랫 텍스트로 변환합니다. 포맷 세부는 [`api/CLAUDE.md`](api/CLAUDE.md) 참고.
- **LLM 레이어**: `anthropic.Anthropic()` 클라이언트를 모듈 로드 시점에 생성합니다. 상수 `MODEL`과 `SYSTEM_PROMPT`가 `main.py` 상단에 모여 있어, 모델/프롬프트 변경 지점이 한 곳입니다.
- **렌더링 레이어**: 모델 응답의 마크다운을 `markdown.markdown`으로 HTML로 변환하고 템플릿에 `| safe`로 주입합니다. 모델 출력을 신뢰된 HTML로 다루므로, 모델 입력 경로를 바꿀 때 이 가정을 유지해야 합니다.

## 요청 흐름

```
사용자 브라우저
   │  (CSV 업로드)
   ▼
POST /analyze  ──►  parse_kakao_csv  ──►  tail-trim (MAX_MESSAGES=500)
                                                │
                                                ▼
                                     format_for_llm (라인 평탄화)
                                                │
                                                ▼
                              client.messages.create (claude-opus-5-5)
                                                │
                                                ▼
                           text 블록 join → markdown.markdown
                                                │
                                                ▼
                                 index.html 재렌더링 (| safe)
```

오류·거부 경로는 같은 템플릿의 `error` 변수로 흡수되며 HTTP 200으로 응답합니다. 자세한 내용은 [`api/CLAUDE.md`](api/CLAUDE.md)의 "오류·거부 처리"를 참고하세요.
