# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 빠른 시작 (Quick start)

클론 직후 설치·기동·검증·훅 활성화를 한 번에 — 아래 블록을 위에서 아래로 실행합니다.

```bash
# Git Bash / WSL / Linux
pip install -r requirements.txt                 # 1. 의존성
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env      # 2. API 키 (서버 기동 전 필수)
uvicorn main:app --reload                       # 3. 개발 서버 → http://127.0.0.1:8000
python scripts/smoke.py                          # 4. 스모크 (서버 기동 상태 · 실제 Claude 호출=비용)
git config core.hooksPath scripts/hooks          # 5. 문서 경로 검증 훅 (clone마다 1회)
```
```powershell
# Windows PowerShell
pip install -r requirements.txt
"ANTHROPIC_API_KEY=sk-ant-..." | Out-File -Encoding utf8 .env
uvicorn main:app --reload                        # 또는 백그라운드: scripts/dev.ps1 start
python scripts/smoke.py
git config core.hooksPath scripts/hooks
```

각 단계의 상세·옵션은 아래 절에 있습니다.

## 실행 방법

의존성을 설치하고 개발 서버를 실행합니다.

```powershell
# Windows PowerShell
pip install -r requirements.txt
uvicorn main:app --reload        # http://127.0.0.1:8000
```
```bash
# Git Bash / WSL / Linux
pip install -r requirements.txt
uvicorn main:app --reload        # http://127.0.0.1:8000
```

**Why:** `.env`의 `ANTHROPIC_API_KEY`는 서버 기동 *전에* 있어야 합니다 — `anthropic.Anthropic()` 클라이언트가 모듈 import 시점에 생성되므로, 키가 없으면 기동 자체가 실패합니다. `python-dotenv`가 import 시 `.env`를 자동 로드합니다.

**Note:** Python 3.9+ 필요(`list[dict]` 내장 제네릭 사용). 버전 핀 파일·린터·빌드 단계는 없습니다. 기동 후 http://127.0.0.1:8000 에서 카카오톡 CSV를 업로드합니다.

### 개발 서버 헬퍼 (선택)

백그라운드 기동·상태 확인·로그 조회용 스크립트가 있습니다.

```powershell
scripts/dev.ps1 start            # 백그라운드 기동 후 헬스체크 (기본 8000 포트)
scripts/dev.ps1 status           # 실행 여부 확인
scripts/dev.ps1 logs             # stdout/stderr 마지막 40줄
scripts/dev.ps1 stop             # 중지
scripts/dev.ps1 start -Port 9000 # Note: 포트 변경
```
```bash
# Git Bash / WSL / Linux (동작 동일)
scripts/dev.sh start             # start|stop|status|restart|logs
PORT=9000 scripts/dev.sh start   # Note: 포트 변경은 PORT 환경변수
```

### 스모크 테스트

서버가 떠 있는 상태에서 `fixtures/sample_kakao.csv`를 `/analyze`에 POST 하여
두 섹션(`대화 요약`·`액션 아이템`) 응답 계약을 검증합니다.

```powershell
python scripts/smoke.py          # 종료코드 0=성공 1=계약실패 2=픽스처없음 3=서버불가
$env:SMOKE_URL="http://host/analyze"; python scripts/smoke.py   # Note: 대상 URL 변경
```
```bash
python scripts/smoke.py
SMOKE_URL=http://host/analyze python scripts/smoke.py           # Note: 대상 URL 변경
```

**Note:** 서버가 떠 있어야 하며, **실제 Claude 호출이 발생**하므로 `ANTHROPIC_API_KEY`가 필요합니다(API 비용 발생). 계약 세부는 [`api/CLAUDE.md`](api/CLAUDE.md) 참고.

### 문서 경로 검증 훅 (선택)

`scripts/check_paths.py`는 추적 중인 `*.md`가 참조하는 파일 경로가 실제로 존재하는지 검사해, stale/hallucinated 참조가 머지되는 것을 막습니다. pre-push 훅으로 한 번만 활성화합니다.

```bash
git config core.hooksPath scripts/hooks   # clone마다 1회
python scripts/check_paths.py             # 수동 실행도 가능
```

**Note:** 훅을 건너뛰려면 `git push --no-verify`. gitignore된 런타임 산출물(`.env`, `scripts/.dev.*`)은 없어도 통과합니다.

## 하위 가이드

- 전체 아키텍처(구성 요소, 레이어 구분, 요청 흐름, 모듈 의존성 다이어그램)는 [`architecture.md`](architecture.md)를 참고하세요.
- API/라우트/Claude 호출 세부 사항(CSV 포맷, `MAX_MESSAGES = 500`, 시스템 프롬프트 계약, 오류·거부 처리, 응답 렌더링의 신뢰 가정)은 [`api/CLAUDE.md`](api/CLAUDE.md)에 정리되어 있습니다.
- 코드만으로는 드러나지 않는 **설계 결정의 "왜"**(2섹션 계약·`MAX_MESSAGES` 컷·`utf-8-sig` 디코딩·adaptive thinking)는 [`docs/adr/`](docs/adr/README.md)에 기록되어 있습니다. 이 결정들을 되돌리기 전에 먼저 읽으세요.
- 2섹션 계약의 **pass-rate 측정**(프롬프트/모델 변경의 회귀 추적)은 [`evals/`](evals/README.md)를 참고하세요.

## 검증 게이트

- **문서 경로 검증** — `scripts/check_paths.py`가 추적 `*.md`의 경로 참조를 검사합니다. 로컬은 pre-push 훅(위 빠른 시작 5단계), 머지 시점은 CI `docs-paths` 워크플로가 자동 실행합니다(무과금).
- **계약 스모크/eval** — `scripts/smoke.py`·`evals/run_evals.py`는 실제 Claude 호출(비용)이라 CI에서 자동 실행하지 않습니다. `smoke` 워크플로는 수동(`workflow_dispatch`)으로만 돌며 `ANTHROPIC_API_KEY` 시크릿이 필요합니다.
- **리뷰어 지정** — `.github/CODEOWNERS`가 계약 문서·`main.py` 변경에 리뷰어를 붙이고, PR 템플릿이 계약 체크리스트를 띄웁니다.
